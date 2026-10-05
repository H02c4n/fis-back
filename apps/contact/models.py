from django.db import models


class ContactMessage(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", "Ny"
        HANDLED = "HANDLED", "Hanterad"

    first_name = models.CharField("Förnamn", max_length=80)
    last_name = models.CharField("Efternamn", max_length=80)
    email = models.EmailField("E-post")
    phone = models.CharField("Telefon", max_length=30, blank=True)
    message = models.TextField("Meddelande")
    status = models.CharField("Status", max_length=20, choices=Status.choices, default=Status.NEW, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Meddelande"
        verbose_name_plural = "Meddelanden"

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.created_at:%Y-%m-%d})"
