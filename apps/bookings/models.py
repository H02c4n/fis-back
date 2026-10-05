import secrets

from django.db import models

REFERENCE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no look-alike characters


def generate_reference() -> str:
    return "FS-" + "".join(secrets.choice(REFERENCE_ALPHABET) for _ in range(8))


class BookingStatus(models.TextChoices):
    NEW = "NEW", "Ny"
    CONFIRMED = "CONFIRMED", "Bekräftad"
    IN_PROGRESS = "IN_PROGRESS", "Pågående"
    COMPLETED = "COMPLETED", "Utförd"
    CANCELLED = "CANCELLED", "Avbokad"


class KeyHandling(models.TextChoices):
    HOME = "HOME", "Kunden är hemma och öppnar"
    OFFICE = "OFFICE", "Nyckel lämnas på kontor"
    ALREADY_LEFT = "ALREADY_LEFT", "Nycklar redan lämnade"


class OvenType(models.TextChoices):
    STANDARD = "STANDARD", "Vanlig ugn"
    SELF_CLEANING = "SELF_CLEANING", "Självrengörande ugn"


class Customer(models.Model):
    first_name = models.CharField("Förnamn", max_length=80)
    last_name = models.CharField("Efternamn", max_length=80)
    email = models.EmailField("E-post", db_index=True)
    phone = models.CharField("Telefon", max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kund"
        verbose_name_plural = "Kunder"

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self) -> str:
        return str(self)


class AvailabilitySlot(models.Model):
    """A bookable time window. One slot = one booking (no double booking)."""

    date = models.DateField("Datum", db_index=True)
    start_time = models.TimeField("Starttid")
    end_time = models.TimeField("Sluttid", null=True, blank=True)
    is_active = models.BooleanField("Bokningsbar", default=True)

    class Meta:
        ordering = ["date", "start_time"]
        verbose_name = "Bokningsbar tid"
        verbose_name_plural = "Bokningsbara tider"
        constraints = [models.UniqueConstraint(fields=["date", "start_time"], name="uniq_slot_date_time")]

    def __str__(self) -> str:
        end = f"–{self.end_time:%H:%M}" if self.end_time else ""
        return f"{self.date} {self.start_time:%H:%M}{end}"


class BlockedDate(models.Model):
    date = models.DateField("Datum", unique=True)
    reason = models.CharField("Anledning", max_length=200, blank=True)

    class Meta:
        ordering = ["date"]
        verbose_name = "Blockerat datum"
        verbose_name_plural = "Blockerade datum"

    def __str__(self) -> str:
        return f"{self.date}"


class Booking(models.Model):
    reference = models.CharField("Bokningsnummer", max_length=20, unique=True, editable=False, default=generate_reference)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="bookings")
    slot = models.ForeignKey(AvailabilitySlot, on_delete=models.PROTECT, related_name="bookings")
    # Snapshots of date/time so history survives if slots are edited or removed later.
    date = models.DateField("Datum", db_index=True)
    time = models.TimeField("Tid")
    area = models.PositiveIntegerField("Bostadsyta (m²)")
    address = models.CharField("Adress", max_length=200)
    postal_code = models.CharField("Postnummer", max_length=10)
    city = models.CharField("Ort", max_length=100, db_index=True)
    key_handling = models.CharField("Nyckelhantering", max_length=20, choices=KeyHandling.choices)
    oven_type = models.CharField("Ugn", max_length=20, choices=OvenType.choices, default=OvenType.STANDARD)
    notes = models.TextField("Övrig information", blank=True)
    use_rut = models.BooleanField("Kunden vill använda RUT", default=True)

    # Price snapshot – never recalculated after creation.
    price_before_rut = models.DecimalField("Pris före RUT (kr)", max_digits=10, decimal_places=2)
    rut_discount = models.DecimalField("RUT-avdrag (kr)", max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField("Att betala (kr)", max_digits=10, decimal_places=2)
    price_snapshot = models.JSONField("Prisunderlag", default=dict, editable=False)

    status = models.CharField("Status", max_length=20, choices=BookingStatus.choices, default=BookingStatus.NEW, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-time"]
        verbose_name = "Bokning"
        verbose_name_plural = "Bokningar"
        constraints = [
            # Hard database guarantee: a slot can have at most one non-cancelled booking.
            models.UniqueConstraint(
                fields=["slot"],
                condition=~models.Q(status="CANCELLED"),
                name="uniq_active_booking_per_slot",
            )
        ]

    def __str__(self) -> str:
        return f"{self.reference} – {self.customer}"


class BookingExtra(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="extras")
    extra = models.ForeignKey("pricing.Extra", on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    rut_eligible = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Bokat tillägg"
        verbose_name_plural = "Bokade tillägg"

    def __str__(self) -> str:
        return self.name
