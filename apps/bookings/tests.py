from datetime import timedelta
from unittest import mock

from django.core import mail
from django.db import IntegrityError, transaction
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.bookings.models import BlockedDate, Booking, BookingStatus
from apps.core.models import SiteSettings
from apps.core.tests_helpers import enable_rut, make_slot, reset_throttle, seed_pricing
from apps.pricing.models import PriceRule


def payload(slot, **overrides):
    data = {
        "area": 83, "self_cleaning_oven": False, "extras": ["balkong-oppen"], "notes": "Portkod 1234",
        "key_handling": "HOME", "slot_id": slot.pk, "first_name": "Anna", "last_name": "Andersson",
        "phone": "070-123 45 67", "email": "Anna@Example.com", "address": "Storgatan 1",
        "postal_code": "21122", "city": "Malmö", "accepted_terms": True,
    }
    data.update(overrides)
    return data


@override_settings(ADMIN_EMAIL="admin@example.com")
class BookingApiTests(APITestCase):
    def setUp(self):
        reset_throttle()
        seed_pricing()
        self.slot = make_slot()

    def post(self, data):
        return self.client.post("/api/bookings/", data, format="json")

    def test_create_booking_recalculates_price_server_side(self):
        # A client cannot influence price: unknown fields like "total" are ignored.
        res = self.post(payload(self.slot, total=1))
        self.assertEqual(res.status_code, 201, res.content)
        d = res.json()["data"]
        self.assertEqual(d["total_price"], 4275)
        self.assertTrue(d["reference"].startswith("FS-"))
        b = Booking.objects.get()
        self.assertEqual(b.customer.email, "anna@example.com")
        self.assertEqual(b.postal_code, "211 22")
        self.assertEqual(b.status, BookingStatus.NEW)
        self.assertEqual(b.extras.count(), 1)
        self.assertEqual(b.date, self.slot.date)

    def test_emails_sent_to_admin_and_customer(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.post(payload(self.slot))
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].subject, "Ny flyttstädningsbokning")
        self.assertEqual(mail.outbox[1].to, ["anna@example.com"])

    def test_email_failure_does_not_break_booking(self):
        with mock.patch("apps.bookings.emails.send_mail", side_effect=OSError("smtp down")):
            with self.captureOnCommitCallbacks(execute=True):
                res = self.post(payload(self.slot))
        self.assertEqual(res.status_code, 201)

    def test_price_snapshot_survives_price_change(self):
        self.post(payload(self.slot))
        PriceRule.objects.filter(min_area=75).update(base_price=9999)
        b = Booking.objects.get()
        self.assertEqual(b.price_before_rut, 4275)
        self.assertEqual(b.price_snapshot["base_price"], 4075)

    def test_rut_snapshot(self):
        enable_rut(50)
        self.post(payload(self.slot))
        b = Booking.objects.get()
        self.assertEqual((b.price_before_rut, b.rut_discount, b.total_price), (4275, 2138, 2137))

    def test_duplicate_booking_prevented(self):
        self.assertEqual(self.post(payload(self.slot)).status_code, 201)
        res = self.post(payload(self.slot, email="other@example.com"))
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.json()["error"]["code"], "SLOT_UNAVAILABLE")
        self.assertEqual(res.json()["error"]["message"], "Tiden är inte längre tillgänglig. Välj en annan tid.")
        self.assertEqual(Booking.objects.count(), 1)

    def test_db_constraint_blocks_second_active_booking(self):
        self.post(payload(self.slot))
        first = Booking.objects.get()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Booking.objects.create(
                customer=first.customer, slot=self.slot, date=first.date, time=first.time, area=50, address="x",
                postal_code="1", city="x", key_handling="HOME", price_before_rut=1, total_price=1,
            )

    def test_cancelled_booking_frees_slot(self):
        self.post(payload(self.slot))
        Booking.objects.update(status=BookingStatus.CANCELLED)
        self.assertEqual(self.post(payload(self.slot, email="b@example.com")).status_code, 201)

    def test_blocked_date_inactive_and_too_soon_slots_rejected(self):
        BlockedDate.objects.create(date=self.slot.date)
        self.assertEqual(self.post(payload(self.slot)).status_code, 409)
        soon = make_slot(days_ahead=0)
        self.assertEqual(self.post(payload(soon)).status_code, 409)
        inactive = make_slot(days_ahead=10)
        inactive.is_active = False
        inactive.save()
        self.assertEqual(self.post(payload(inactive)).status_code, 409)
        self.assertEqual(self.post(payload(self.slot, slot_id=99999)).status_code, 409)

    def test_validation(self):
        res = self.post(payload(self.slot, email="not-an-email", postal_code="12", phone="abc", accepted_terms=False, area=0))
        self.assertEqual(res.status_code, 400)
        fields = res.json()["error"]["fields"]
        for f in ("email", "postal_code", "phone", "accepted_terms", "area"):
            self.assertIn(f, fields)
        self.assertEqual(fields["email"], ["Ange en giltig e-postadress."])
        self.assertEqual(Booking.objects.count(), 0)

    def test_office_key_handling_requires_setting(self):
        self.assertEqual(self.post(payload(self.slot, key_handling="OFFICE")).status_code, 400)
        s = SiteSettings.load()
        s.key_office_enabled = True
        s.save()
        self.assertEqual(self.post(payload(self.slot, key_handling="OFFICE")).status_code, 201)

    def test_invalid_extra(self):
        res = self.post(payload(self.slot, extras=["bogus"]))
        self.assertEqual(res.json()["error"]["code"], "INVALID_EXTRA")

    def test_honeypot_discards_silently(self):
        res = self.post(payload(self.slot, website="http://spam"))
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Booking.objects.count(), 0)

    def test_rate_limit(self):
        codes = [self.post({}).status_code for _ in range(11)]
        self.assertEqual(codes[-1], 429)

    def test_public_summary_has_no_personal_data(self):
        ref = self.post(payload(self.slot)).json()["data"]["reference"]
        res = self.client.get(f"/api/bookings/{ref}/")
        self.assertEqual(res.status_code, 200)
        text = res.content.decode()
        for secret in ("Anna", "Andersson", "example.com", "070", "Storgatan"):
            self.assertNotIn(secret, text)
        self.assertEqual(self.client.get("/api/bookings/FS-NOPE1234/").status_code, 404)

    def test_bookings_cannot_be_listed(self):
        self.assertEqual(self.client.get("/api/bookings/").status_code, 405)


class AvailabilityApiTests(APITestCase):
    def setUp(self):
        reset_throttle()
        seed_pricing()

    def test_only_free_active_unblocked_slots_listed(self):
        from datetime import time
        free = make_slot(5)
        booked = make_slot(5, start=time(13, 0))
        blocked = make_slot(6)
        inactive = make_slot(7)
        inactive.is_active = False
        inactive.save()
        too_soon = make_slot(0)
        BlockedDate.objects.create(date=blocked.date)
        self.client.post("/api/bookings/", payload(booked), format="json")

        res = self.client.get("/api/availability/")
        self.assertEqual(res.status_code, 200)
        dates = res.json()["data"]["dates"]
        ids = [s["id"] for d in dates for s in d["slots"]]
        self.assertEqual(ids, [free.pk])
        self.assertEqual(res["Cache-Control"], "no-store")

    def test_bad_date_param(self):
        self.assertEqual(self.client.get("/api/availability/?from=hello").status_code, 400)
