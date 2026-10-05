from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from apps.core.responses import ok

from .models import City
from .serializers import CityDetailSerializer, CityListSerializer


class CityListView(APIView):
    def get(self, request):
        cities = City.objects.filter(is_active=True)
        return ok(CityListSerializer(cities, many=True).data, cache_seconds=60)


class CityDetailView(APIView):
    def get(self, request, slug):
        try:
            city = City.objects.prefetch_related("faqs").get(slug=slug, is_active=True)
        except City.DoesNotExist:
            raise NotFound()
        return ok(CityDetailSerializer(city).data, cache_seconds=60)
