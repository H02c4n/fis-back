import re

from rest_framework import serializers

PHONE_RE = re.compile(r"^\+?[0-9][0-9 \-()]{5,19}$")


class ContactSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=80)
    last_name = serializers.CharField(max_length=80)
    email = serializers.EmailField(error_messages={"invalid": "Ange en giltig e-postadress."})
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")
    message = serializers.CharField(max_length=5000)
    website = serializers.CharField(required=False, allow_blank=True, default="", max_length=200)  # honeypot

    def validate_phone(self, value):
        value = value.strip()
        if value and not PHONE_RE.match(value):
            raise serializers.ValidationError("Ange ett giltigt telefonnummer.")
        return value
