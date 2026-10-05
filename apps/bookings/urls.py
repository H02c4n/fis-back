from django.urls import path

from .views import AvailabilityView, BookingCreateView, BookingDetailView

urlpatterns = [
    path("availability/", AvailabilityView.as_view()),
    path("bookings/", BookingCreateView.as_view()),
    path("bookings/<str:reference>/", BookingDetailView.as_view()),
]
