from rest_framework.views import APIView

from .models import SiteSettings
from .responses import ok

KEY_HANDLING_LABELS = {
    "HOME": "Jag är hemma och öppnar",
    "OFFICE": "Jag lämnar nyckeln på vårt kontor",
    "ALREADY_LEFT": "Jag har redan lämnat mina nycklar",
}


class HealthView(APIView):
    throttle_classes: list = []

    def get(self, request):
        return ok({"status": "ok"})


class ConfigView(APIView):
    """Public, non-sensitive configuration the booking UI needs."""

    def get(self, request):
        s = SiteSettings.load()
        options = [
            {"value": k, "label": v}
            for k, v in KEY_HANDLING_LABELS.items()
            if k != "OFFICE" or s.key_office_enabled
        ]
        return ok(
            {
                "company_name": s.company_name,
                "rut_enabled": s.rut_enabled,
                "min_booking_lead_days": s.min_booking_lead_days,
                "key_handling_options": options,
            },
            cache_seconds=60,
        )
