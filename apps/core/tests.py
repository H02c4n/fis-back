from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core.tests_helpers import reset_throttle


class PermissionAndConfigTests(TestCase):
    def setUp(self):
        reset_throttle()

    def test_admin_requires_login(self):
        res = self.client.get("/admin/", follow=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn("/admin/login/", res["Location"])

    def test_admin_index_for_superuser(self):
        u = get_user_model().objects.create_superuser("boss", "b@example.com", "a-very-long-password-1")
        self.client.force_login(u)
        self.assertEqual(self.client.get("/admin/").status_code, 200)
        for path in ("bookings/booking", "cities/city", "pricing/pricerule", "contact/contactmessage", "core/sitesettings"):
            self.assertEqual(self.client.get(f"/admin/{path}/").status_code, 200, path)

    def test_config_hides_office_option_by_default(self):
        d = self.client.get("/api/config/").json()["data"]
        self.assertEqual([o["value"] for o in d["key_handling_options"]], ["HOME", "ALREADY_LEFT"])
        self.assertFalse(d["rut_enabled"])

    def test_health(self):
        self.assertEqual(self.client.get("/api/health/").json(), {"success": True, "data": {"status": "ok"}})

    def test_no_secrets_in_config(self):
        body = self.client.get("/api/config/").content.decode().lower()
        for word in ("password", "secret", "smtp"):
            self.assertNotIn(word, body)
