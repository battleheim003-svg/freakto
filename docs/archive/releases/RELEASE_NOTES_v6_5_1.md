# Freakto v6.5.1 — Automatic Event Collector Source Resilience Patch

این نسخه یک Patch تکمیلی برای v6.5.0 است و روی کیفیت جمع‌آوری خبر/رویداد تمرکز دارد.

## هدف

در تست واقعی v6.5.0، collector توانست از SEC و Federal Reserve دیتا جمع کند، اما چند منبع رسمی/معتبر مثل Binance، Coinbase و SEC Litigation ممکن بود به خاطر تغییر RSS/API، محدودیت صفحه یا HTML/JS fail شوند. v6.5.1 برای همین ساخته شد.

## تغییرات اصلی

- اضافه شدن fallback URL برای sourceهای رسمی/معتبر.
- تلاش چندمرحله‌ای برای RSS، Atom، HTML listing page و JSON endpoint.
- HTML fallback parser برای صفحات رسمی که RSS آن‌ها جابه‌جا یا غیرفعال شده باشد.
- fallback بهتر برای Binance Announcements: JSON endpoint جایگزین + صفحه رسمی announcement.
- fallback بهتر برای Coinbase Blog: چند آدرس RSS/page رسمی.
- fallback بهتر برای SEC Litigation Releases: RSS جایگزین + صفحه رسمی litigation releases.
- User-Agent محافظه‌کارتر برای کاهش خطاهای ساده‌ی fetch.
- همچنان Research-only؛ هیچ Paper/Live/Order ایجاد نمی‌کند.

## فایل‌های تغییرکرده

```text
engine/auto_event_collector.py
data/auto_event_sources.example.json
AUTO_EVENT_COLLECTOR_RUNBOOK.md
CAUSAL_INTELLIGENCE_RUNBOOK.md
FORWARD_TEST_RUNBOOK.md
README_NEXT_STEPS.md
RELEASE_NOTES_v6_5_1.md
RESEARCH_ROBUSTNESS_RUNBOOK.md
SHADOW_GATE_RUNBOOK.md
```

## تست پیشنهادی

```cmd
python automatic_event_collector_dashboard.py --sources
python automatic_event_collector_dashboard.py --compact
python causal_intelligence_dashboard.py --compact
python causal_event_dashboard.py --show
python forward_test_dashboard.py --plan
```

## نکته مهم

اگر sourceای باز هم fail شود، الزاماً مشکل پروژه نیست. بعضی سایت‌ها anti-bot، تغییر endpoint یا محدودیت منطقه‌ای دارند. v6.5.1 تلاش می‌کند fallback بزند، اما شکست یک source نباید کل Forward cycle را متوقف کند.
