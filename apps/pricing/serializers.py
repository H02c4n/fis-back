from rest_framework import serializers

from .models import Extra, PriceRule
from .services import rut_for, sek
from apps.core.models import SiteSettings


class PriceRuleSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="__str__", read_only=True)
    from_price = serializers.SerializerMethodField()
    from_price_after_rut = serializers.SerializerMethodField()

    class Meta:
        model = PriceRule
        fields = ("id", "label", "min_area", "max_area", "description", "from_price", "from_price_after_rut")

    def get_from_price(self, obj):
        return int(sek(obj.price_for(obj.min_area)))

    def get_from_price_after_rut(self, obj):
        gross = sek(obj.price_for(obj.min_area))
        settings = self.context["site_settings"]
        return int(gross - rut_for(gross, settings)) if settings.rut_enabled else None


class ExtraSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()

    class Meta:
        model = Extra
        fields = ("slug", "name", "description", "price", "rut_eligible")

    def get_price(self, obj):
        return int(sek(obj.price))


class CalculateInputSerializer(serializers.Serializer):
    area = serializers.IntegerField(min_value=1, max_value=1000)
    extras = serializers.ListField(child=serializers.SlugField(), required=False, default=list, max_length=20)
    self_cleaning_oven = serializers.BooleanField(required=False, default=False)
    use_rut = serializers.BooleanField(required=False, default=True)
