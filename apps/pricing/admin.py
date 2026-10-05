from django.contrib import admin

from .models import Extra, PriceRule


@admin.register(PriceRule)
class PriceRuleAdmin(admin.ModelAdmin):
    list_display = ("__str__", "base_price", "additional_price_per_sqm", "active", "description")
    list_editable = ("active",)
    ordering = ("min_area",)


@admin.register(Extra)
class ExtraAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "price", "rut_eligible", "is_active", "sort_order")
    list_editable = ("price", "rut_eligible", "is_active", "sort_order")
    prepopulated_fields = {"slug": ("name",)}
