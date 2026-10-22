import logging

from django.core.cache import cache
from redis.exceptions import RedisError
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Check, Incident, Monitor

logger = logging.getLogger(__name__)


class MonitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Monitor
        fields = ["id", "name", "mode", "enabled"]
        read_only_fields = ["id"]


class CheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Check
        fields = [
            "id", "monitor", "slot", "checked_at",
            "ok", "status_code", "latency_ms", "error",
        ]


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = ["id", "monitor", "opened_at", "closed_at"]


class MonitorViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Monitor.objects.order_by("id")
    serializer_class = MonitorSerializer


class CheckViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Check.objects.all()
    serializer_class = CheckSerializer


class IncidentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer


@api_view(["GET"])
def summary(request):
    key = "summary:v1"
    try:
        data = cache.get(key)
    except RedisError:
        logger.warning("Summary cache unavailable")
        data = None

    if data is None:
        data = {
            "enabled_monitors": Monitor.objects.filter(enabled=True).count(),
            "checks": Check.objects.count(),
            "open_incidents": Incident.objects.filter(closed_at__isnull=True).count(),
        }
        try:
            cache.set(key, data, timeout=20)
        except RedisError:
            logger.warning("Summary cache write failed")
    return Response(data)