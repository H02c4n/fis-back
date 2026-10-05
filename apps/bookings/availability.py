from datetime import date, timedelta

from django.db.models import Exists, OuterRef, QuerySet
from django.utils import timezone

from apps.core.models import SiteSettings

from .models import AvailabilitySlot, BlockedDate, Booking, BookingStatus


def earliest_bookable_date() -> date:
    return timezone.localdate() + timedelta(days=SiteSettings.load().min_booking_lead_days)


def available_slots(start: date, end: date) -> QuerySet[AvailabilitySlot]:
    """Active, unblocked, unbooked slots in [start, end], respecting the minimum lead time."""
    start = max(start, earliest_bookable_date())
    taken = Booking.objects.filter(slot=OuterRef("pk")).exclude(status=BookingStatus.CANCELLED)
    return (
        AvailabilitySlot.objects.filter(is_active=True, date__gte=start, date__lte=end)
        .exclude(date__in=BlockedDate.objects.values("date"))
        .annotate(taken=Exists(taken))
        .filter(taken=False)
        .order_by("date", "start_time")
    )
