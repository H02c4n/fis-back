"""Email notifications. Failures are logged and never break the booking request."""
import logging

from django.conf import settings
from django.core.mail import send_mail

from apps.core.models import SiteSettings

from .models import Booking

logger = logging.getLogger(__name__)


def _kr(value) -> str:
    return f"{int(value):,}".replace(",", " ") + " kr"


def booking_summary(booking: Booking) -> str:
    extras = ", ".join(f"{e.name} ({_kr(e.price)})" for e in booking.extras.all()) or "Inga"
    return "\n".join(
        [
            f"Bokningsnummer: {booking.reference}",
            "Tjänst: Flyttstädning",
            f"Datum: {booking.date:%Y-%m-%d}",
            f"Tid: {booking.time:%H:%M}",
            f"Bostadsyta: {booking.area} m²",
            f"Tillägg: {extras}",
            f"Adress: {booking.address}, {booking.postal_code} {booking.city}",
            f"Nyckelhantering: {booking.get_key_handling_display()}",
            f"Pris före RUT: {_kr(booking.price_before_rut)}",
            f"RUT-avdrag: {_kr(booking.rut_discount)}",
            f"Att betala: {_kr(booking.total_price)}",
            f"Övrig information: {booking.notes or '–'}",
        ]
    )


def send_booking_emails(booking_id: int) -> None:
    try:
        booking = Booking.objects.select_related("customer").prefetch_related("extras").get(pk=booking_id)
    except Booking.DoesNotExist:
        return
    company = SiteSettings.load().company_name
    summary = booking_summary(booking)
    c = booking.customer

    if settings.ADMIN_EMAIL:
        try:
            send_mail(
                "Ny flyttstädningsbokning",
                f"Kund: {c.full_name}\nE-post: {c.email}\nTelefon: {c.phone}\n\n{summary}",
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
            )
        except Exception:
            logger.exception("Failed to send booking notification to admin (booking %s)", booking.reference)
    else:
        logger.warning("ADMIN_EMAIL is not set; no admin notification sent for %s", booking.reference)

    try:
        send_mail(
            f"Bekräftelse på din flyttstädning – {booking.reference}",
            f"Hej {c.first_name}!\n\nTack för din bokning hos {company}. Här är en sammanfattning:\n\n{summary}\n\n"
            "Har du frågor är du välkommen att svara på det här mejlet.\n\nVänliga hälsningar,\n" + company,
            settings.DEFAULT_FROM_EMAIL,
            [c.email],
        )
    except Exception:
        logger.exception("Failed to send booking confirmation to customer (booking %s)", booking.reference)
