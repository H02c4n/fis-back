from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.core.models import SiteSettings
from apps.pricing.models import Extra, PriceRule

PLACEHOLDER = "PLATSHÅLLARE – ersätt med företagets riktiga pris i admin"


class Command(BaseCommand):
    help = "Seed PLACEHOLDER prices/extras (only if none exist). Replace the values in Django Admin before launch."

    def add_arguments(self, parser):
        parser.add_argument("--with-slots", action="store_true", help="Also generate slots for the next 60 days (dev)")

    def handle(self, *args, **opts):
        SiteSettings.load()
        if not PriceRule.objects.exists():
            for lo, hi, base, per in [
                (0, 49, 2500, 0), (50, 74, 3500, 0), (75, 99, 4075, 0),
                (100, 199, 4900, 40), (200, None, 8900, 35),
            ]:
                PriceRule.objects.create(
                    min_area=lo, max_area=hi, base_price=Decimal(base), additional_price_per_sqm=Decimal(per),
                    description=PLACEHOLDER,
                )
        if not Extra.objects.exists():
            for i, (slug, name, price) in enumerate(
                [("altan-uterum", "Altan / uterum", 300), ("balkong-oppen", "Balkong (öppen)", 200),
                 ("balkong-inglasad", "Balkong (inglasad)", 400)]
            ):
                Extra.objects.create(slug=slug, name=name, price=Decimal(price), sort_order=i, description=PLACEHOLDER)
        if opts["with_slots"]:
            call_command("generate_slots")
        self.stdout.write(self.style.SUCCESS("Seed complete. Review prices in Django Admin."))
