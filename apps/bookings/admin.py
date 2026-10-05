from django.contrib import admin, messages
from django.db.models import Exists, OuterRef

from .models import AvailabilitySlot, BlockedDate, Booking, BookingExtra, BookingStatus, Customer


class BookingExtraInline(admin.TabularInline):
    model = BookingExtra
    extra = 0
    can_delete = False
    readonly_fields = ("extra", "name", "price", "rut_eligible")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("reference", "customer", "city", "area", "date", "time", "total_price", "status")
    list_filter = ("status", "date", "city")
    search_fields = ("reference", "id", "customer__first_name", "customer__last_name", "customer__email", "customer__phone")
    date_hierarchy = "date"
    list_select_related = ("customer",)
    inlines = [BookingExtraInline]
    actions = ["mark_confirmed", "mark_completed", "mark_cancelled"]
    readonly_fields = (
        "reference", "customer", "slot", "date", "time", "area", "price_before_rut", "rut_discount",
        "total_price", "price_snapshot", "created_at", "updated_at",
    )

    def has_add_permission(self, request):
        return False  # bookings are created through the website

    def _set_status(self, request, queryset, status):
        n = queryset.update(status=status)
        self.message_user(request, f"{n} bokning(ar) uppdaterade.", messages.SUCCESS)

    @admin.action(description="Markera som bekräftad")
    def mark_confirmed(self, request, queryset):
        self._set_status(request, queryset, BookingStatus.CONFIRMED)

    @admin.action(description="Markera som utförd")
    def mark_completed(self, request, queryset):
        self._set_status(request, queryset, BookingStatus.COMPLETED)

    @admin.action(description="Avboka (frigör tiden)")
    def mark_cancelled(self, request, queryset):
        self._set_status(request, queryset, BookingStatus.CANCELLED)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "phone", "created_at")
    search_fields = ("first_name", "last_name", "email", "phone")


@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ("date", "start_time", "end_time", "is_active", "is_booked")
    list_filter = ("is_active", "date")
    list_editable = ("is_active",)
    date_hierarchy = "date"
    actions = ["deactivate", "activate"]

    def get_queryset(self, request):
        taken = Booking.objects.filter(slot=OuterRef("pk")).exclude(status=BookingStatus.CANCELLED)
        return super().get_queryset(request).annotate(_booked=Exists(taken))

    @admin.display(boolean=True, description="Bokad", ordering="_booked")
    def is_booked(self, obj):
        return obj._booked

    @admin.action(description="Inaktivera valda tider")
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description="Aktivera valda tider")
    def activate(self, request, queryset):
        queryset.update(is_active=True)


@admin.register(BlockedDate)
class BlockedDateAdmin(admin.ModelAdmin):
    list_display = ("date", "reason")
