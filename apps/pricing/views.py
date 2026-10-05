from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.core.models import SiteSettings
from apps.core.responses import ok

from .models import Extra, PriceRule
from .serializers import CalculateInputSerializer, ExtraSerializer, PriceRuleSerializer
from .services import calculate_price


class PriceListView(APIView):
    def get(self, request):
        s = SiteSettings.load()
        rules = PriceRule.objects.filter(active=True)
        return ok(
            {
                "rules": PriceRuleSerializer(rules, many=True, context={"site_settings": s}).data,
                "rut_enabled": s.rut_enabled,
            },
            cache_seconds=60,
        )


class ExtraListView(APIView):
    def get(self, request):
        return ok(ExtraSerializer(Extra.objects.filter(is_active=True), many=True).data, cache_seconds=60)


class CalculatePriceView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "pricing"

    def post(self, request):
        s = CalculateInputSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        result = calculate_price(
            area=d["area"], extra_slugs=d["extras"], self_cleaning_oven=d["self_cleaning_oven"], use_rut=d["use_rut"]
        )
        return ok(result.as_dict())
