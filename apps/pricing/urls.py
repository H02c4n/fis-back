from django.urls import path

from .views import CalculatePriceView, ExtraListView, PriceListView

urlpatterns = [
    path("prices/", PriceListView.as_view()),
    path("extras/", ExtraListView.as_view()),
    path("pricing/calculate/", CalculatePriceView.as_view()),
]
