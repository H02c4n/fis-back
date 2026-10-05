# Flyttstädning – Backend (Django + DRF)

Phase 1–2 of the project: models, admin, pricing, availability, booking and contact APIs.

## Quick start
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DEBUG=True                 # or copy .env.example values into your environment
# PostgreSQL: export DATABASE_URL=postgres://user:pass@localhost:5432/flyttstad  (SQLite is used if unset – dev/tests only)
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_initial_data --with-slots   # PLACEHOLDER prices + 60 days of slots
python manage.py seed_cities                      # all 18 Skåne cities with starter SEO content
python manage.py runserver
python manage.py test             # 46 tests
```
Or with Docker: `docker compose up --build` (Postgres + backend on :8000).

Admin: `/admin/` (configurable via `ADMIN_URL`).

## Business configuration (all in Admin)
| What | Where |
|---|---|
| Prices per m² tier | Prisregler. `price = base_price + additional_price_per_sqm × (area − min_area)`. Leave "Till" empty for open-ended (200+). Overlapping active ranges are rejected. |
| Extras | Tilläggstjänster (price, RUT-eligible, active) |
| RUT | Webbplatsinställningar. **Off by default.** Set percent, labour share and cap after checking Skatteverket's current rules. |
| Office key drop-off | Webbplatsinställningar → only enable if an office really exists |
| Availability | Bokningsbara tider (add/disable), Blockerade datum. Bulk: `python manage.py generate_slots --days 60 --weekdays 0,1,2,3,4 --windows 08:00-12:00,13:00-17:00` |
| Cities & FAQ | Städer. New `City` rows appear in the API immediately. `is_indexed` is false by default (noindex) until content is reviewed. Run `python manage.py seed_cities` to populate the 18 Skåne cities from the brief with differentiated starter content (safe to re-run — it updates existing rows and replaces their FAQs). **Read it before launch**: it's real, unique text per city, not lorem ipsum, but it's a starting point built from a few well-known facts per city, not a full copywriting pass — expand it in Admin. |
| Bookings | Bokningar (bulk actions: bekräfta / utförd / avboka – cancelling frees the slot) |

## API
All responses: `{"success": true, "data": …}` or `{"success": false, "error": {"code", "message", "fields?"}}`.

| Method | Path | Notes |
|---|---|---|
| GET | `/api/config/` | company name, RUT on/off, key-handling options |
| GET | `/api/cities/`, `/api/cities/{slug}/` | active cities; detail includes FAQs + `is_indexed` |
| GET | `/api/prices/` | tiers with `from_price` / `from_price_after_rut` (null when RUT is off) |
| GET | `/api/extras/` | active extras |
| POST | `/api/pricing/calculate/` | `{area, extras[], self_cleaning_oven?, use_rut?}` → `base_price, extras, extras_total, gross_total, rut_discount, total` |
| GET | `/api/availability/?from=&to=` | free slots grouped by date (never cached) |
| POST | `/api/bookings/` | creates a booking; price is always recalculated server-side |
| GET | `/api/bookings/{reference}/` | public summary for `/tack` – **no personal data** |
| POST | `/api/contact/` | contact form |

Booking body: `area, self_cleaning_oven, extras[], notes, key_handling (HOME|OFFICE|ALREADY_LEFT), use_rut, slot_id, first_name, last_name, phone, email, address, postal_code, city, accepted_terms` plus hidden honeypot field `website` (must stay empty).

Error codes: `VALIDATION_ERROR` (400), `INVALID_EXTRA` (400), `AREA_NOT_SUPPORTED` (400), `SLOT_UNAVAILABLE` (409), `NOT_FOUND` (404), `RATE_LIMITED` (429).

## Double-booking protection
1. `select_for_update()` row lock on the slot inside `transaction.atomic()`.
2. Availability re-checked inside the lock (active, not blocked, lead time, no non-cancelled booking).
3. Partial unique constraint `uniq_active_booking_per_slot` in the database as the final guarantee.

## Security notes
Stateless API (no cookies → CSRF not applicable; admin keeps CSRF/session), CORS limited to `CORS_ALLOWED_ORIGINS`, throttling per endpoint (booking 10/h, contact 5/h), honeypot, server-side validation, HTTPS/HSTS/secure cookies when `DEBUG=False`. The default throttle cache is per-process; use Redis (`CACHES`) if you run several workers/instances.
