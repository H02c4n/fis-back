from rest_framework.test import APITestCase

from apps.cities.models import City, CityFAQ
from apps.core.tests_helpers import reset_throttle


class CityApiTests(APITestCase):
    def setUp(self):
        reset_throttle()
        self.malmo = City.objects.create(name="Malmö", slug="malmo", seo_title="Flyttstädning i Malmö", is_active=True)
        CityFAQ.objects.create(city=self.malmo, question="Vad kostar det?", answer="Det beror på ytan.", sort_order=1)
        City.objects.create(name="Dolt", slug="dolt", is_active=False)

    def test_list_only_active(self):
        res = self.client.get("/api/cities/")
        self.assertEqual([c["slug"] for c in res.json()["data"]], ["malmo"])

    def test_detail_includes_faqs_and_index_flag(self):
        d = self.client.get("/api/cities/malmo/").json()["data"]
        self.assertEqual(d["faqs"][0]["question"], "Vad kostar det?")
        self.assertFalse(d["is_indexed"])  # noindex until the owner opts in

    def test_inactive_and_unknown_are_404(self):
        self.assertEqual(self.client.get("/api/cities/dolt/").status_code, 404)
        res = self.client.get("/api/cities/finns-inte/")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["error"]["code"], "NOT_FOUND")

    def test_slug_generated_without_swedish_letters(self):
        c = City(name="Ängelholm")
        c.save()
        self.assertEqual(c.slug, "angelholm")


class SeedCitiesCommandTests(APITestCase):
    def test_seeds_18_distinct_active_indexed_cities(self):
        from io import StringIO

        from django.core.management import call_command

        call_command("seed_cities", stdout=StringIO())
        self.assertEqual(City.objects.count(), 18)
        self.assertTrue(City.objects.filter(is_active=True, is_indexed=True).count() == 18)

        malmo = City.objects.get(slug="malmo")
        lund = City.objects.get(slug="lund")
        self.assertNotEqual(malmo.introduction, lund.introduction)
        self.assertIn("Malmö", malmo.introduction)
        self.assertEqual(malmo.faqs.count(), 5)

    def test_rerunning_is_idempotent(self):
        from io import StringIO

        from django.core.management import call_command

        call_command("seed_cities", stdout=StringIO())
        call_command("seed_cities", stdout=StringIO())
        self.assertEqual(City.objects.count(), 18)
        self.assertEqual(City.objects.get(slug="malmo").faqs.count(), 5)
