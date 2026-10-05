from datetime import date, datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.bookings.models import AvailabilitySlot


class Command(BaseCommand):
    help = "Create bookable time slots for the coming days (existing slots are left untouched)."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=60)
        parser.add_argument("--weekdays", default="0,1,2,3,4", help="Comma-separated, Monday=0 … Sunday=6")
        parser.add_argument("--windows", default="08:00-12:00,13:00-17:00", help="Comma-separated HH:MM-HH:MM")

    def handle(self, *args, **opts):
        weekdays = {int(x) for x in opts["weekdays"].split(",") if x.strip()}
        windows = []
        for w in opts["windows"].split(","):
            start, end = w.strip().split("-")
            windows.append((datetime.strptime(start, "%H:%M").time(), datetime.strptime(end, "%H:%M").time()))
        today: date = timezone.localdate()
        created = 0
        for offset in range(1, opts["days"] + 1):
            day = today + timedelta(days=offset)
            if day.weekday() not in weekdays:
                continue
            for start, end in windows:
                _, was_created = AvailabilitySlot.objects.get_or_create(
                    date=day, start_time=start, defaults={"end_time": end}
                )
                created += was_created
        self.stdout.write(self.style.SUCCESS(f"Created {created} slots."))
