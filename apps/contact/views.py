import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.core.responses import ok

from .models import ContactMessage
from .serializers import ContactSerializer

logger = logging.getLogger(__name__)


def _notify(message_id: int) -> None:
    msg = ContactMessage.objects.get(pk=message_id)
    if not settings.ADMIN_EMAIL:
        logger.warning("ADMIN_EMAIL is not set; contact message %s not emailed", msg.pk)
        return
    try:
        send_mail(
            "Nytt meddelande via webbplatsen",
            f"Från: {msg.first_name} {msg.last_name}\nE-post: {msg.email}\nTelefon: {msg.phone or '–'}\n\n{msg.message}",
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
        )
    except Exception:
        logger.exception("Failed to send contact notification (message %s)", msg.pk)


class ContactView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "contact"

    def post(self, request):
        s = ContactSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        if data["website"]:  # honeypot: pretend success
            return ok({"received": True}, status=201)
        data.pop("website")
        with transaction.atomic():
            msg = ContactMessage.objects.create(**data)
            transaction.on_commit(lambda: _notify(msg.pk))
        return ok({"received": True}, status=201)
