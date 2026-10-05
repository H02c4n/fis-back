from django.db import models
from django.utils.text import slugify


class City(models.Model):
    name = models.CharField("Ort", max_length=100)
    slug = models.SlugField("URL-slug", max_length=100, unique=True, help_text="t.ex. malmo, angelholm")
    short_description = models.CharField("Kort beskrivning (kort/länk)", max_length=200, blank=True)
    hero_title = models.CharField("Hero-rubrik", max_length=200, blank=True)
    hero_description = models.TextField("Hero-text", blank=True)
    seo_title = models.CharField("SEO-titel", max_length=70, blank=True)
    meta_description = models.CharField("Meta-beskrivning", max_length=170, blank=True)
    introduction = models.TextField("Introduktion", blank=True)
    local_content = models.TextField(
        "Lokalt innehåll", blank=True,
        help_text="Unik text om flyttstädning i just denna ort. Nämn bara områden och förhållanden som stämmer.",
    )
    cta_text = models.CharField("CTA-text", max_length=100, blank=True)
    is_active = models.BooleanField("Aktiv (visas på sajten)", default=True)
    is_indexed = models.BooleanField(
        "Indexeras av Google", default=False,
        help_text="Aktivera först när sidan har tillräckligt med unikt innehåll. Annars sätts noindex och sidan utesluts ur sitemap.",
    )
    sort_order = models.PositiveIntegerField("Sortering", default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Stad"
        verbose_name_plural = "Städer"
        indexes = [models.Index(fields=["is_active", "sort_order"])]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name.replace("å", "a").replace("ä", "a").replace("ö", "o"))
        super().save(*args, **kwargs)


class CityFAQ(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="faqs")
    question = models.CharField("Fråga", max_length=250)
    answer = models.TextField("Svar")
    sort_order = models.PositiveIntegerField("Sortering", default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "Vanlig fråga"
        verbose_name_plural = "Vanliga frågor"

    def __str__(self) -> str:
        return self.question
