from datetime import date, timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import NotFound
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.core.exceptions import ApiError
from apps.core.responses import ok

from .availability import available_slots
from .models import Booking
from .serializers import BookingCreateSerializer, BookingSummarySerializer
from .services import create_booking


def _parse_date(value: str | None, default: date, field: str) -> date:
    if not value:
        return default
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ApiError("VALIDATION_ERROR", "Ogiltigt datum.", 400, {field: ["Använd formatet ÅÅÅÅ-MM-DD."]})


class AvailabilityView(APIView):
    """GET /api/availability/?from=YYYY-MM-DD&to=YYYY-MM-DD"""

    def get(self, request):
        today = timezone.localdate()
        start = _parse_date(request.query_params.get("from"), today, "from")
        end = _parse_date(request.query_params.get("to"), start + timedelta(days=60), "to")
        if end < start:
            raise ApiError("VALIDATION_ERROR", "Slutdatum måste vara efter startdatum.", 400, {"to": ["Ogiltigt intervall."]})
        if (end - start).days > settings.BOOKING_MAX_AVAILABILITY_RANGE_DAYS:
            end = start + timedelta(days=settings.BOOKING_MAX_AVAILABILITY_RANGE_DAYS)

        days: dict[str, list] = {}
        for slot in available_slots(start, end):
            days.setdefault(slot.date.isoformat(), []).append(
                {
                    "id": slot.pk,
                    "start_time": slot.start_time.strftime("%H:%M"),
                    "end_time": slot.end_time.strftime("%H:%M") if slot.end_time else None,
                }
            )
        data = {"dates": [{"date": d, "slots": s} for d, s in days.items()]}
        response = ok(data)
        response["Cache-Control"] = "no-store"  # availability must always be fresh
        return response


class BookingCreateView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "booking"

    def post(self, request):
        s = BookingCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        if data["website"]:  # honeypot filled in: pretend success, store nothing
            return ok({"reference": "FS-00000000"}, status=201)
        booking = create_booking(data)
        booking = Booking.objects.prefetch_related("extras").get(pk=booking.pk)
        return ok(BookingSummarySerializer(booking).data, status=201)


class BookingDetailView(APIView):
    """Public summary for the /tack page. Contains no personal data."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "booking_lookup"

    def get(self, request, reference):
        try:
            booking = Booking.objects.prefetch_related("extras").get(reference=reference.upper())
        except Booking.DoesNotExist:
            raise NotFound()
        response = ok(BookingSummarySerializer(booking).data)
        response["Cache-Control"] = "no-store"
        return response
