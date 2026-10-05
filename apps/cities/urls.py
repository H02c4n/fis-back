from django.urls import path

from .views import CityDetailView, CityListView

urlpatterns = [
    path("cities/", CityListView.as_view()),
    path("cities/<slug:slug>/", CityDetailView.as_view()),
]
