from django.db import IntegrityError, transaction

from apps.core.exceptions import ApiError
from apps.pricing.services import calculate_price

from .availability import earliest_bookable_date
from .emails import send_booking_emails
from .models import (
    AvailabilitySlot, BlockedDate, Booking, BookingExtra, BookingStatus, Customer, KeyHandling, OvenType,
)

def _slot_unavailable() -> ApiError:
    return ApiError("SLOT_UNAVAILABLE", "Tiden är inte längre tillgänglig. Välj en annan tid.", 409)


def create_booking(data: dict) -> Booking:
    """Create a booking atomically. Price is always recalculated server-side."""
    from apps.core.models import SiteSettings

    site = SiteSettings.load()
    if data["key_handling"] == KeyHandling.OFFICE and not site.key_office_enabled:
        raise ApiError(
            "VALIDATION_ERROR", "Det valda alternativet för nyckelhantering är inte tillgängligt.", 400,
            {"key_handling": ["Alternativet är inte tillgängligt."]},
        )

    price = calculate_price(
        area=data["area"], extra_slugs=data["extras"],
        self_cleaning_oven=data["self_cleaning_oven"], use_rut=data["use_rut"],
    )

    with transaction.atomic():
        # Row lock: concurrent requests for the same slot are serialised here (PostgreSQL).
        try:
            slot = AvailabilitySlot.objects.select_for_update().get(pk=data["slot_id"], is_active=True)
        except AvailabilitySlot.DoesNotExist:
            raise _slot_unavailable()

        if (
            slot.date < earliest_bookable_date()
            or BlockedDate.objects.filter(date=slot.date).exists()
            or Booking.objects.filter(slot=slot).exclude(status=BookingStatus.CANCELLED).exists()
        ):
            raise _slot_unavailable()

        customer = Customer.objects.filter(email=data["email"]).order_by("-id").first()
        if customer is None:
            customer = Customer(email=data["email"])
        customer.first_name, customer.last_name, customer.phone = data["first_name"], data["last_name"], data["phone"]
        customer.save()

        try:
            with transaction.atomic():  # savepoint: the unique constraint is the final safety net
                booking = Booking.objects.create(
                    customer=customer, slot=slot, date=slot.date, time=slot.start_time, area=data["area"],
                    address=data["address"], postal_code=data["postal_code"], city=data["city"],
                    key_handling=data["key_handling"],
                    oven_type=OvenType.SELF_CLEANING if data["self_cleaning_oven"] else OvenType.STANDARD,
                    notes=data["notes"], use_rut=data["use_rut"],
                    price_before_rut=price.gross_total, rut_discount=price.rut_discount, total_price=price.total,
                    price_snapshot=price.as_dict(),
                )
        except IntegrityError:
            raise _slot_unavailable()

        BookingExtra.objects.bulk_create(
            BookingExtra(booking=booking, extra_id=l.extra_id, name=l.name, price=l.price, rut_eligible=l.rut_eligible)
            for l in price.lines
        )
        transaction.on_commit(lambda: send_booking_emails(booking.pk))
    return booking
