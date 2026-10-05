from django.contrib import admin

from .models import City, CityFAQ


class CityFAQInline(admin.TabularInline):
    model = CityFAQ
    extra = 1


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "is_indexed", "content_length", "faq_count", "sort_order", "updated_at")
    list_editable = ("is_active", "is_indexed", "sort_order")
    search_fields = ("name", "slug")
    list_filter = ("is_active", "is_indexed")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [CityFAQInline]
    fieldsets = (
        (None, {"fields": ("name", "slug", "short_description", "is_active", "is_indexed", "sort_order")}),
        ("SEO", {"fields": ("seo_title", "meta_description")}),
        ("Sidinnehåll", {"fields": ("hero_title", "hero_description", "introduction", "local_content", "cta_text")}),
    )

    @admin.display(description="Tecken lokal text")
    def content_length(self, obj):
        return len(obj.local_content or "")

    @admin.display(description="FAQ")
    def faq_count(self, obj):
        return obj.faqs.count()
