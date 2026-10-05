"""Single source of truth for price calculation. Used by the pricing API and by booking creation."""
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from django.db import models

from apps.core.exceptions import ApiError
from apps.core.models import SiteSettings

from .models import Extra, PriceRule

OVEN_SLUG = "self-cleaning-oven"
OVEN_NAME = "Självrengörande ugn"


def sek(value: Decimal) -> Decimal:
    """Round to whole kronor."""
    return Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


@dataclass
class PriceLine:
    slug: str
    name: str
    price: Decimal
    rut_eligible: bool
    extra_id: int | None = None


@dataclass
class PriceBreakdown:
    area: int
    base_price: Decimal
    lines: list[PriceLine] = field(default_factory=list)
    extras_total: Decimal = Decimal("0")
    gross_total: Decimal = Decimal("0")  # price before RUT
    rut_discount: Decimal = Decimal("0")
    total: Decimal = Decimal("0")  # what the customer pays
    rut_enabled: bool = False
    price_rule_id: int | None = None

    def as_dict(self) -> dict:
        return {
            "area": self.area,
            "base_price": int(self.base_price),
            "extras": [
                {"slug": l.slug, "name": l.name, "price": int(l.price), "rut_eligible": l.rut_eligible}
                for l in self.lines
            ],
            "extras_total": int(self.extras_total),
            "gross_total": int(self.gross_total),
            "rut_discount": int(self.rut_discount),
            "total": int(self.total),
            "rut_enabled": self.rut_enabled,
        }


def rut_for(eligible_amount: Decimal, settings: SiteSettings) -> Decimal:
    if not settings.rut_enabled or eligible_amount <= 0:
        return Decimal("0")
    labor = eligible_amount * settings.rut_labor_share_percent / Decimal(100)
    deduction = labor * settings.rut_percent / Decimal(100)
    return sek(min(deduction, settings.rut_max_deduction))


def find_rule(area: int) -> PriceRule:
    rule = (
        PriceRule.objects.filter(active=True, min_area__lte=area)
        .filter(models.Q(max_area__isnull=True) | models.Q(max_area__gte=area))
        .order_by("-min_area")
        .first()
    )
    if rule is None:
        raise ApiError(
            "AREA_NOT_SUPPORTED",
            "Vi kan inte räkna ut ett pris automatiskt för den bostadsytan. Kontakta oss så hjälper vi dig.",
            400,
            {"area": ["Bostadsytan stöds inte för automatisk prisberäkning."]},
        )
    return rule


def calculate_price(*, area: int, extra_slugs=(), self_cleaning_oven: bool = False, use_rut: bool = True) -> PriceBreakdown:
    settings = SiteSettings.load()
    rule = find_rule(area)
    base = sek(rule.price_for(area))

    slugs = list(dict.fromkeys(extra_slugs))  # de-duplicate, keep order
    extras = list(Extra.objects.filter(slug__in=slugs, is_active=True))
    found = {e.slug for e in extras}
    missing = [s for s in slugs if s not in found]
    if missing:
        raise ApiError(
            "INVALID_EXTRA", "En vald tilläggstjänst finns inte längre.", 400,
            {"extras": [f"Okänd tilläggstjänst: {s}" for s in missing]},
        )
    by_slug = {e.slug: e for e in extras}
    lines = [
        PriceLine(e.slug, e.name, sek(e.price), e.rut_eligible, e.pk) for e in (by_slug[s] for s in slugs)
    ]
    if self_cleaning_oven and settings.self_cleaning_oven_surcharge > 0:
        lines.append(PriceLine(OVEN_SLUG, OVEN_NAME, sek(settings.self_cleaning_oven_surcharge), True))

    extras_total = sum((l.price for l in lines), Decimal("0"))
    gross = base + extras_total
    eligible = base + sum((l.price for l in lines if l.rut_eligible), Decimal("0"))
    rut = rut_for(eligible, settings) if use_rut else Decimal("0")

    return PriceBreakdown(
        area=area, base_price=base, lines=lines, extras_total=extras_total, gross_total=gross,
        rut_discount=rut, total=gross - rut, rut_enabled=settings.rut_enabled, price_rule_id=rule.pk,
    )

