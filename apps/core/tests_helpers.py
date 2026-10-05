from datetime import time, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.utils import timezone

from apps.bookings.models import AvailabilitySlot
from apps.core.models import SiteSettings
from apps.pricing.models import Extra, PriceRule


def seed_pricing():
    for lo, hi, base, per in [(0, 49, 2500, 0), (50, 74, 3500, 0), (75, 99, 4075, 0), (100, 199, 4900, 40), (200, None, 8900, 35)]:
        PriceRule.objects.create(min_area=lo, max_area=hi, base_price=Decimal(base), additional_price_per_sqm=Decimal(per))
    Extra.objects.create(slug="balkong-oppen", name="Balkong (öppen)", price=Decimal(200))
    Extra.objects.create(slug="altan", name="Altan", price=Decimal(300), rut_eligible=False)


def make_slot(days_ahead=7, start=time(8, 0)):
    return AvailabilitySlot.objects.create(
        date=timezone.localdate() + timedelta(days=days_ahead), start_time=start, end_time=time(12, 0)
    )


def enable_rut(percent=50, cap=75000):
    s = SiteSettings.load()
    s.rut_enabled, s.rut_percent, s.rut_max_deduction = True, Decimal(percent), Decimal(cap)
    s.save()
    return s


def reset_throttle():
    cache.clear()
