from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class PriceRule(models.Model):
    """Price for a range of living area.

    price(area) = base_price + additional_price_per_sqm * (area - min_area)
    Leave max_area empty for an open-ended range (e.g. 200+ m²).
    """

    min_area = models.PositiveIntegerField("Från (m²)")
    max_area = models.PositiveIntegerField("Till (m²)", null=True, blank=True, help_text="Tomt = ingen övre gräns")
    base_price = models.DecimalField("Grundpris (kr)", max_digits=10, decimal_places=2)
    additional_price_per_sqm = models.DecimalField(
        "Tillägg per m² över 'Från' (kr)", max_digits=8, decimal_places=2, default=Decimal("0"),
    )
    description = models.CharField("Beskrivning", max_length=200, blank=True)
    active = models.BooleanField("Aktiv", default=True)

    class Meta:
        ordering = ["min_area"]
        verbose_name = "Prisregel"
        verbose_name_plural = "Prisregler"

    def __str__(self) -> str:
        upper = f"{self.max_area}" if self.max_area is not None else "+"
        return f"{self.min_area}–{upper} m²" if self.max_area is not None else f"{self.min_area}+ m²"

    def clean(self):
        if self.max_area is not None and self.max_area < self.min_area:
            raise ValidationError("'Till' måste vara större än eller lika med 'Från'.")
        if self.active:
            hi = self.max_area if self.max_area is not None else 10**9
            overlapping = PriceRule.objects.filter(active=True).exclude(pk=self.pk)
            for other in overlapping:
                other_hi = other.max_area if other.max_area is not None else 10**9
                if self.min_area <= other_hi and other.min_area <= hi:
                    raise ValidationError(f"Intervallet överlappar en annan aktiv prisregel ({other}).")

    def price_for(self, area: int) -> Decimal:
        return self.base_price + self.additional_price_per_sqm * Decimal(max(area - self.min_area, 0))


class Extra(models.Model):
    slug = models.SlugField("Kod", unique=True)
    name = models.CharField("Namn", max_length=120)
    description = models.CharField("Beskrivning", max_length=250, blank=True)
    price = models.DecimalField("Pris (kr)", max_digits=10, decimal_places=2)
    rut_eligible = models.BooleanField("Ger RUT-avdrag", default=True)
    is_active = models.BooleanField("Aktiv", default=True)
    sort_order = models.PositiveIntegerField("Sortering", default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Tilläggstjänst"
        verbose_name_plural = "Tilläggstjänster"

    def __str__(self) -> str:
        return self.name
