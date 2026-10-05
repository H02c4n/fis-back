from django.conf import settings
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Flyttstädning – administration"
admin.site.site_title = "Flyttstädning admin"
admin.site.index_title = "Hantera bokningar, priser och städer"

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/", include("apps.core.urls")),
    path("api/", include("apps.cities.urls")),
    path("api/", include("apps.pricing.urls")),
    path("api/", include("apps.bookings.urls")),
    path("api/", include("apps.contact.urls")),
]
