from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("created_at", "first_name", "last_name", "email", "phone", "status")
    list_filter = ("status", "created_at")
    list_editable = ("status",)
    search_fields = ("first_name", "last_name", "email", "phone", "message")
    readonly_fields = ("first_name", "last_name", "email", "phone", "message", "created_at")

    def has_add_permission(self, request):
        return False
