from django.core import mail
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.contact.models import ContactMessage
from apps.core.tests_helpers import reset_throttle

VALID = {"first_name": "Lisa", "last_name": "Berg", "email": "lisa@example.com", "phone": "0701234567", "message": "Hej!"}


@override_settings(ADMIN_EMAIL="admin@example.com")
class ContactApiTests(APITestCase):
    def setUp(self):
        reset_throttle()

    def test_submit_saves_and_notifies(self):
        with self.captureOnCommitCallbacks(execute=True):
            res = self.client.post("/api/contact/", VALID, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_invalid_email(self):
        res = self.client.post("/api/contact/", {**VALID, "email": "x"}, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["error"]["fields"]["email"], ["Ange en giltig e-postadress."])

    def test_honeypot(self):
        res = self.client.post("/api/contact/", {**VALID, "website": "spam"}, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_rate_limit(self):
        codes = [self.client.post("/api/contact/", VALID, format="json").status_code for _ in range(6)]
        self.assertEqual(codes[-1], 429)
