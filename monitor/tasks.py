import logging
import time
import httpx
from celery import shared_task
from django.db import OperationalError, connection, transaction
from django.utils import timezone

from .models import Check, Incident, Monitor
from .probe import inspect_target

logger = logging.getLogger(__name__)


@shared_task
def dispatch():
    slot = int(time.time() // 60)
    for monitor_id in Monitor.objects.filter(enabled=True).values_list("id", flat=True):
        run_check.apply_async(args=[monitor_id, slot], expires=55)


def save_result(monitor, slot, result):
    with transaction.atomic():
        check, created = Check.objects.get_or_create(
            monitor=monitor, slot=slot, defaults=result
        )
        if not created:
            return check

        now = timezone.now()
        if result["ok"]:
            Incident.objects.filter(
                monitor=monitor, closed_at__isnull=True
            ).update(closed_at=now)
        else:
            Incident.objects.get_or_create(
                monitor=monitor,
                closed_at__isnull=True,
                defaults={"opened_at": now},
            )
        return check


@shared_task(
    autoretry_for=(OperationalError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def run_check(monitor_id, slot):
    if int(time.time() // 60) - slot > 1:
        return

    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [monitor_id])
        acquired = cursor.fetchone()[0]
    if not acquired:
        return

    try:
        monitor = Monitor.objects.filter(pk=monitor_id, enabled=True).first()
        if monitor is None or Check.objects.filter(monitor=monitor, slot=slot).exists():
            return

        with httpx.Client(
            timeout=httpx.Timeout(3.0, connect=1.0),
            follow_redirects=False,
            trust_env=False,
        ) as client:
            result = inspect_target(monitor.mode, client)

        save_result(monitor, slot, result)
        logger.info(
            "check monitor=%s slot=%s ok=%s error=%s",
            monitor_id, slot, result["ok"], result["error"],
        )
    finally:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_unlock(%s)", [monitor_id])