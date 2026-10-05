from rest_framework import serializers

from .models import City, CityFAQ


class CityFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = CityFAQ
        fields = ("question", "answer")


class CityListSerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("name", "slug", "short_description", "is_indexed", "updated_at")


class CityDetailSerializer(serializers.ModelSerializer):
    faqs = CityFAQSerializer(many=True, read_only=True)

    class Meta:
        model = City
        fields = (
            "name", "slug", "short_description", "hero_title", "hero_description", "seo_title",
            "meta_description", "introduction", "local_content", "cta_text", "is_indexed",
            "updated_at", "faqs",
        )
