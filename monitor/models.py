from django.db import models
from django.db.models import Q


class Monitor(models.Model):
    class Mode(models.TextChoices):
        OK = "ok", "Poprawna odpowiedź"
        ERROR = "error", "HTTP 500"
        SLOW = "slow", "Przekroczony czas"
        INVALID = "invalid", "Niepoprawny kontrakt JSON"

    name = models.CharField(max_length=100, unique=True)
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.OK)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Check(models.Model):
    monitor = models.ForeignKey(Monitor, on_delete=models.CASCADE)
    slot = models.BigIntegerField()
    checked_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ok = models.BooleanField()
    status_code = models.PositiveSmallIntegerField(null=True)
    latency_ms = models.PositiveIntegerField()
    error = models.CharField(max_length=100, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["monitor", "slot"], name="unique_monitor_slot"
            ),
        ]
        ordering = ["-checked_at", "-id"]


class Incident(models.Model):
    monitor = models.ForeignKey(Monitor, on_delete=models.CASCADE)
    opened_at = models.DateTimeField()
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["monitor"],
                condition=Q(closed_at__isnull=True),
                name="one_open_incident_per_monitor",
            ),
        ]
        ordering = ["-opened_at", "-id"]