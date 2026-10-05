import re

from rest_framework import serializers

from .models import Booking, KeyHandling

PHONE_RE = re.compile(r"^\+?[0-9][0-9 \-()]{5,19}$")
POSTAL_RE = re.compile(r"^\d{3}\s?\d{2}$")


class BookingCreateSerializer(serializers.Serializer):
    # Home / service
    area = serializers.IntegerField(min_value=1, max_value=1000)
    self_cleaning_oven = serializers.BooleanField(required=False, default=False)
    extras = serializers.ListField(child=serializers.SlugField(), required=False, default=list, max_length=20)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=2000, default="")
    key_handling = serializers.ChoiceField(choices=KeyHandling.choices)
    use_rut = serializers.BooleanField(required=False, default=True)
    slot_id = serializers.IntegerField(min_value=1)
    # Customer & address
    first_name = serializers.CharField(max_length=80, trim_whitespace=True)
    last_name = serializers.CharField(max_length=80, trim_whitespace=True)
    phone = serializers.CharField(max_length=30)
    email = serializers.EmailField(max_length=254, error_messages={"invalid": "Ange en giltig e-postadress."})
    address = serializers.CharField(max_length=200)
    postal_code = serializers.CharField(max_length=10)
    city = serializers.CharField(max_length=100)
    accepted_terms = serializers.BooleanField()
    # Honeypot – real users never fill this in (hidden field).
    website = serializers.CharField(required=False, allow_blank=True, default="", max_length=200)

    def validate_phone(self, value):
        value = value.strip()
        if not PHONE_RE.match(value):
            raise serializers.ValidationError("Ange ett giltigt telefonnummer.")
        return value

    def validate_postal_code(self, value):
        value = value.strip()
        if not POSTAL_RE.match(value):
            raise serializers.ValidationError("Ange ett giltigt postnummer (5 siffror).")
        digits = value.replace(" ", "")
        return f"{digits[:3]} {digits[3:]}"

    def validate_email(self, value):
        return value.strip().lower()

    def validate_accepted_terms(self, value):
        if not value:
            raise serializers.ValidationError("Du behöver godkänna villkoren för att boka.")
        return value


class BookingSummarySerializer(serializers.ModelSerializer):
    """Public booking summary – deliberately excludes personal data (name, email, phone, address)."""

    extras = serializers.SerializerMethodField()
    time = serializers.TimeField(format="%H:%M")
    date = serializers.DateField(format="%Y-%m-%d")

    class Meta:
        model = Booking
        fields = (
            "reference", "status", "date", "time", "area", "city", "extras",
            "price_before_rut", "rut_discount", "total_price",
        )

    def get_extras(self, obj):
        return [{"name": e.name, "price": int(e.price)} for e in obj.extras.all()]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for k in ("price_before_rut", "rut_discount", "total_price"):
            data[k] = int(float(data[k]))
        return data
