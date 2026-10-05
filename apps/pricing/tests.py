from decimal import Decimal

from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase

from apps.core.tests_helpers import enable_rut, reset_throttle, seed_pricing
from apps.pricing.models import PriceRule
from apps.pricing.services import calculate_price
from apps.core.exceptions import ApiError


class PricingServiceTests(APITestCase):
    def setUp(self):
        reset_throttle()
        seed_pricing()

    def test_tier_price_and_extras(self):
        r = calculate_price(area=83, extra_slugs=["balkong-oppen"])
        self.assertEqual((r.base_price, r.extras_total, r.gross_total, r.rut_discount, r.total),
                         (4075, 200, 4275, 0, 4275))

    def test_per_sqm_addition_and_open_ended_rule(self):
        self.assertEqual(calculate_price(area=120).base_price, Decimal(4900 + 20 * 40))
        self.assertEqual(calculate_price(area=250).base_price, Decimal(8900 + 50 * 35))

    def test_boundaries(self):
        self.assertEqual(calculate_price(area=49).base_price, 2500)
        self.assertEqual(calculate_price(area=50).base_price, 3500)
        self.assertEqual(calculate_price(area=99).base_price, 4075)
        self.assertEqual(calculate_price(area=100).base_price, 4900)

    def test_rut_disabled_by_default(self):
        r = calculate_price(area=83)
        self.assertFalse(r.rut_enabled)
        self.assertEqual(r.rut_discount, 0)

    def test_rut_percent_and_only_eligible_extras(self):
        enable_rut(percent=50)
        r = calculate_price(area=83, extra_slugs=["altan"])  # altan is not RUT-eligible
        self.assertEqual(r.gross_total, 4375)
        self.assertEqual(r.rut_discount, Decimal("2038"))  # 50% of 4075 = 2037.5 -> 2038
        self.assertEqual(r.total, 4375 - 2038)

    def test_rut_cap_and_opt_out(self):
        enable_rut(percent=50, cap=1000)
        self.assertEqual(calculate_price(area=83).rut_discount, 1000)
        self.assertEqual(calculate_price(area=83, use_rut=False).rut_discount, 0)

    def test_unknown_extra_rejected(self):
        with self.assertRaises(ApiError) as ctx:
            calculate_price(area=83, extra_slugs=["nope"])
        self.assertEqual(ctx.exception.code, "INVALID_EXTRA")

    def test_no_rule_for_area(self):
        PriceRule.objects.all().delete()
        with self.assertRaises(ApiError):
            calculate_price(area=83)

    def test_overlapping_rules_rejected(self):
        with self.assertRaises(ValidationError):
            PriceRule(min_area=60, max_area=80, base_price=1, active=True).full_clean()


class PricingApiTests(APITestCase):
    def setUp(self):
        reset_throttle()
        seed_pricing()

    def test_calculate_endpoint(self):
        res = self.client.post("/api/pricing/calculate/", {"area": 83, "extras": ["balkong-oppen"]}, format="json")
        self.assertEqual(res.status_code, 200)
        d = res.json()["data"]
        self.assertTrue(res.json()["success"])
        self.assertEqual((d["base_price"], d["extras_total"], d["rut_discount"], d["total"]), (4075, 200, 0, 4275))

    def test_validation_error_envelope(self):
        res = self.client.post("/api/pricing/calculate/", {"area": -5}, format="json")
        self.assertEqual(res.status_code, 400)
        body = res.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("area", body["error"]["fields"])

    def test_prices_list(self):
        res = self.client.get("/api/prices/")
        self.assertEqual(len(res.json()["data"]["rules"]), 5)
        self.assertIsNone(res.json()["data"]["rules"][0]["from_price_after_rut"])
        enable_rut()
        res = self.client.get("/api/prices/")
        self.assertEqual(res.json()["data"]["rules"][0]["from_price_after_rut"], 1250)

    def test_extras_list(self):
        self.assertEqual(len(self.client.get("/api/extras/").json()["data"]), 2)
