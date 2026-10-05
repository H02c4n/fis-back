from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class SiteSettings(models.Model):
    """Singleton with business configuration editable in Django Admin."""

    company_name = models.CharField("Företagsnamn", max_length=120, default="COMPANY_NAME")
    key_office_enabled = models.BooleanField(
        "Erbjud nyckelavlämning på kontor",
        default=False,
        help_text="Aktivera endast om företaget faktiskt har ett kontor där kunder kan lämna nycklar.",
    )
    min_booking_lead_days = models.PositiveSmallIntegerField(
        "Minsta framförhållning (dagar)", default=2,
        help_text="Tider närmare än så här i tid kan inte bokas online.",
    )
    self_cleaning_oven_surcharge = models.DecimalField(
        "Tillägg självrengörande ugn (kr)", max_digits=10, decimal_places=2, default=Decimal("0"),
    )

    # RUT – deliberately configurable; rules change over time. Verify with Skatteverket.
    rut_enabled = models.BooleanField(
        "Visa och räkna med RUT-avdrag", default=False,
        help_text="Aktivera först när företaget är godkänt för RUT och procent/tak nedan är kontrollerade.",
    )
    rut_percent = models.DecimalField(
        "RUT-avdrag (% av arbetskostnad)", max_digits=5, decimal_places=2, default=Decimal("50"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Kontrollera gällande procentsats hos Skatteverket.",
    )
    rut_labor_share_percent = models.DecimalField(
        "Andel av priset som är arbetskostnad (%)", max_digits=5, decimal_places=2, default=Decimal("100"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Endast arbetskostnaden ger RUT-avdrag (t.ex. inte material/resor om de faktureras separat).",
    )
    rut_max_deduction = models.DecimalField(
        "Tak för RUT-avdrag per bokning (kr)", max_digits=10, decimal_places=2, default=Decimal("75000"),
        help_text="Taket gäller per person och år. Systemet känner inte till kundens tidigare utnyttjande.",
    )

    class Meta:
        verbose_name = "Webbplatsinställningar"
        verbose_name_plural = "Webbplatsinställningar"

    def __str__(self) -> str:
        return "Webbplatsinställningar"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # singleton – never delete
        pass

    @classmethod
    def load(cls) -> "SiteSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
