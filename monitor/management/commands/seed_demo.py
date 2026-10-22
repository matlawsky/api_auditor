from django.core.management.base import BaseCommand
from monitor.models import Monitor


class Command(BaseCommand):
    help = "Create demo monitors without overwriting existing settings."

    def handle(self, *args, **options):
        for mode, label in Monitor.Mode.choices:
            Monitor.objects.get_or_create(
                name=label, defaults={"mode": mode}
            )
        self.stdout.write(self.style.SUCCESS("Monitory demonstracyjne gotowe."))