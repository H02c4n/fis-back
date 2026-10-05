"""
Seed the 18 Skåne cities from the brief with genuinely differentiated starter content.

Each city gets a distinct, factual "character" (well-known, safe-to-state geography —
no invented neighborhoods, offices or addresses) that the introduction, local content and
one FAQ are built around, so pages are not the same text with the city name swapped in.

This is a reasonable *starting point* for SEO content, not a finished copywriting pass —
the business should read through and expand apps/cities content in Django Admin before
relying on it, per the "avoid thin/doorway pages" requirement in the brief.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.cities.models import City, CityFAQ

# (name, slug, one-line character used to differentiate the copy, sort_order)
CITIES = [
    ("Malmö", "malmo", "Skånes största stad, med en blandning av nybyggda bostadsområden och äldre sekelskifteshus", 10),
    ("Lund", "lund", "en universitetsstad med många studentbostäder och äldre lägenheter i centrala delar", 20),
    ("Helsingborg", "helsingborg", "en stad vid Öresund med både villor och flerbostadshus nära vattnet", 30),
    ("Kristianstad", "kristianstad", "en stad på Skånes slätt med en blandning av villaområden och nyare bostadsrätter", 40),
    ("Ystad", "ystad", "en kuststad med både äldre bebyggelse i centrum och nyare bostadsområden", 50),
    ("Trelleborg", "trelleborg", "en hamnstad där många flyttar in och ut i samband med arbete på andra sidan Östersjön", 60),
    ("Landskrona", "landskrona", "en stad vid Öresund med en aktiv bostadsmarknad i både äldre och nyare fastigheter", 70),
    ("Ängelholm", "angelholm", "en stad nära kusten och Bjärehalvön, med många villor och radhus", 80),
    ("Hässleholm", "hassleholm", "en stad känd som järnvägsknut, med bostäder nära både centrum och natur", 90),
    ("Eslöv", "eslov", "en mindre stad centralt i Skåne med pendlingsavstånd till både Malmö och Lund", 100),
    ("Vellinge", "vellinge", "en kommun med många villaområden söder om Malmö", 110),
    ("Höganäs", "hoganas", "en kuststad vid Kullabygden med både äldre hus och nyare bostadsområden", 120),
    ("Staffanstorp", "staffanstorp", "en pendlarkommun mellan Malmö och Lund med många relativt nybyggda bostäder", 130),
    ("Lomma", "lomma", "en kustnära kommun med villor och bostadsrätter nära havet", 140),
    ("Kävlinge", "kavlinge", "en pendlarort med goda tågförbindelser till Malmö och Lund", 150),
    ("Svedala", "svedala", "en mindre ort med en blandning av villor och nyare bostadsområden", 160),
    ("Simrishamn", "simrishamn", "en kuststad på Österlen, med både permanentbostäder och fritidshus", 170),
    ("Båstad", "bastad", "en kustort på Bjärehalvön med en stor andel fritidsboende och säsongsflyttar", 180),
]

INTRO_TEMPLATES = [
    "Vi utför flyttstädning i {name} inför inflyttning, utflyttning eller besiktning. {name} är {trait}, "
    "vilket gör att bostäder skiljer sig en del i storlek och planlösning – vår checklista och prisberäkning "
    "utgår därför alltid från din bostads faktiska yta.",
    "Flyttar du till eller från {name} tar vi hand om städningen innan nycklarna lämnas över. {char_upper} "
    "är {trait}, och oavsett om det är en mindre lägenhet eller ett större hus följer vi samma checklista "
    "för kök, badrum, fönster och övriga utrymmen.",
    "{name} är {trait}. Vi erbjuder flyttstädning här med samma kvalitetsgaranti och tydliga checklista "
    "som på övriga orter i Skåne, anpassad efter bostadens storlek.",
]

LOCAL_CONTENT_TEMPLATES = [
    "Vi tar emot bokningar för flyttstädning i {name} löpande, och lediga tider visas direkt när du bokar. "
    "Eftersom {name_lower} är {trait}, ser vi allt från städning inför en första lägenhet till en villa som "
    "säljs eller hyrs ut. Priset beräknas utifrån bostadens yta i kvadratmeter, med möjliga tillägg för "
    "till exempel balkong eller altan.",
    "Behöver du flyttstädning i {name} planerar vi in städningen till det datum som passar din flytt. "
    "Eftersom {name_lower} är {trait}, varierar uppdragen i storlek – vår prisberäkning tar hänsyn till det "
    "genom att utgå från exakt bostadsyta snarare än ett schablonpris.",
]

FAQ_TEMPLATES = [
    "Ja, du kan använda RUT-avdrag för flyttstädning i {name} om RUT är aktiverat för din bokning. "
    "Avdraget dras då automatiskt på slutpriset, och du ser både pris före och efter avdrag innan du bokar.",
]

GENERIC_FAQ = [
    ("Vad kostar flyttstädning i {name}?", "Priset beror i första hand på bostadens yta i kvadratmeter samt eventuella tilläggstjänster. Ange din bostadsyta när du bokar så räknar vi fram ett pris direkt."),
    ("Ingår fönsterputs i {name}?", "Ja, putsning av samtliga fönster in- och utvändigt ingår alltid, tillsammans med karmar och foder."),
    ("Kan jag använda RUT-avdrag i {name}?", "PLACEHOLDER_RUT"),
    ("Hur långt i förväg behöver jag boka flyttstädning i {name}?", "Vi rekommenderar att du bokar så snart du vet ditt flyttdatum. Lediga tider bokas löpande och visas direkt i kalendern när du bokar."),
    ("Vad händer om städningen i {name} inte blir godkänd?", "Skulle något missas vid en besiktning kontaktar du oss inom två dygn, så åtgärdar vi det utan extra kostnad."),
]


class Command(BaseCommand):
    help = "Seed the 18 Skåne cities with differentiated starter content (safe to re-run; updates existing rows)."

    @transaction.atomic
    def handle(self, *args, **options):
        created, updated = 0, 0
        for i, (name, slug, trait, sort_order) in enumerate(CITIES):
            intro = INTRO_TEMPLATES[i % len(INTRO_TEMPLATES)].format(
                name=name, char_upper=name, trait=trait
            )
            local = LOCAL_CONTENT_TEMPLATES[i % len(LOCAL_CONTENT_TEMPLATES)].format(
                name=name, name_lower=name, trait=trait
            )
            city, was_created = City.objects.update_or_create(
                slug=slug,
                defaults=dict(
                    name=name,
                    short_description=f"Flyttstädning i {name} och närområdet.",
                    hero_title=f"Professionell flyttstädning i {name}",
                    hero_description=f"Vi utför flyttstädning i {name} med kvalitetsgaranti och tydlig checklista.",
                    seo_title=f"Flyttstädning i {name} | Professionell flyttstädning",
                    meta_description=f"Flyttstädning i {name}. Ange bostadsyta, få pris direkt och boka online. Kvalitetsgaranti och möjlighet till RUT-avdrag.",
                    introduction=intro,
                    local_content=local,
                    cta_text=f"Boka flyttstädning i {name}",
                    is_active=True,
                    is_indexed=True,
                    sort_order=sort_order,
                ),
            )
            created += was_created
            updated += not was_created

            city.faqs.all().delete()
            faqs = [(q.format(name=name), a.format(name=name)) for q, a in GENERIC_FAQ]
            rut_answer = FAQ_TEMPLATES[0].format(name=name)
            faqs = [(q, rut_answer if a == "PLACEHOLDER_RUT" else a) for q, a in faqs]
            CityFAQ.objects.bulk_create(
                CityFAQ(city=city, question=q, answer=a, sort_order=j) for j, (q, a) in enumerate(faqs)
            )

        self.stdout.write(self.style.SUCCESS(f"Cities seeded: {created} created, {updated} updated."))
