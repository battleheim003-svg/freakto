
# Freakto v6.5.0 — Automatic Event Collector Runbook

هدف این ماژول این است که `data/manual_events.csv` فقط نقش پشتیبان/curated داشته باشد و رویدادهای روزانه از منابع رسمی یا معتبر به‌صورت خودکار جمع شوند.

## اجرای سریع

```cmd
python automatic_event_collector_dashboard.py --sources
python automatic_event_collector_dashboard.py --compact
python causal_intelligence_dashboard.py --compact
python causal_event_dashboard.py --show
```

## خروجی اصلی

```text
data/auto_events.csv
logs/events/auto_event_collector_*.json
logs/events/auto_event_collector_report_*.md
logs/events/auto_event_source_health_*.csv
```

## منطق اعتماد منبع

- Tier 1: منبع رسمی regulator/macro/exchange/protocol مثل SEC، Federal Reserve، Binance Announcements، Ethereum Foundation.
- Tier 2: وبلاگ رسمی شرکت یا رسانه معتبر؛ فقط context، نه سیگنال مستقل.
- Tier 3: aggregator/sentiment؛ برای نسخه‌های بعدی و فقط با وزن پایین.

## نکته مهم

این ماژول هیچ Paper Trade و هیچ سفارش واقعی ایجاد نمی‌کند. فقط event ledger می‌سازد تا Causal Intelligence بتواند catalyst/conflict را کنار تصمیم‌های تکنیکال بررسی کند.
