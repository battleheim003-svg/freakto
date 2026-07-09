# Freakto Automatic Event Collector Runbook — v6.5.1

این ماژول قبل از Causal Intelligence اجرا می‌شود و رویدادهای رسمی/معتبر را در `data/auto_events.csv` ذخیره می‌کند.

## Research-only

این collector هیچ سفارش واقعی، هیچ Paper Trade جدید و هیچ تصمیم معاملاتی مستقل ایجاد نمی‌کند. خروجی آن فقط برای context، tagging و research است.

## منابع اصلی

- SEC Press Releases
- SEC Litigation Releases
- Federal Reserve Press Releases
- Federal Reserve Speeches/Testimony
- Ethereum Foundation Blog
- Coinbase Blog
- Binance Announcements
- CoinDesk RSS اختیاری با `--include-media`

## بهبود v6.5.1

v6.5.1 برای sourceهایی که گاهی fail می‌شوند fallback دارد:

- RSS اصلی
- RSS/Atom جایگزین
- HTML listing page رسمی
- JSON endpoint جایگزین برای Binance

اگر یک source fail شود، چرخه Forward متوقف نمی‌شود. فقط در Source Health گزارش می‌شود.

## دستورات اصلی

```cmd
python automatic_event_collector_dashboard.py --sources
python automatic_event_collector_dashboard.py --compact
python automatic_event_collector_dashboard.py --compact --include-media
python automatic_event_collector_dashboard.py --compact --no-fetch
```

## فایل خروجی

```text
data/auto_events.csv
```

این فایل توسط Causal Intelligence خوانده می‌شود.

## ترتیب در Forward Cycle

```text
automatic_event_collector
causal_intelligence_probe
monitor_once / decision_logger / evaluator / shadow gates
```

## نکته استفاده از manual_events.csv

`manual_events.csv` هنوز مفید است، ولی فقط برای این موارد:

- رویداد بسیار مهمی که collector از دست داده
- override دستی جهت تحقیق
- تست سناریوهای خاص

مسیر اصلی از v6.5 به بعد `auto_events.csv` است.


## v7.0 — Event Quality Filter

- `automatic_event_collector_dashboard.py --compact` اکنون noiseهای product/navigation را فیلتر می‌کند.
- `market_narrative_dashboard.py --compact` روایت بازار را از eventهای تمیز، causal context و driverهای اصلی می‌سازد.
- این لایه فقط Research-only است و هیچ Paper/Live ایجاد نمی‌کند.
