from django.urls import path

from .views import ConfigView, HealthView

urlpatterns = [
    path("health/", HealthView.as_view()),
    path("config/", ConfigView.as_view()),
]
