from django.contrib import admin

from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Företag", {"fields": ("company_name", "key_office_enabled", "min_booking_lead_days")}),
        ("Tillägg", {"fields": ("self_cleaning_oven_surcharge",)}),
        ("RUT-avdrag", {"fields": ("rut_enabled", "rut_percent", "rut_labor_share_percent", "rut_max_deduction")}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
