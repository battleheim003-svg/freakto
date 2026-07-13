# Freakto Multi-Cycle Historical Archive v2.1 — Runbook

این ابزار آرشیو Development چندچرخه‌ای را جدا از Fresh OOS می‌سازد و **هیچ تغییری در Paper یا Live ایجاد نمی‌کند**.

## پنجره‌ها

- `3Y`: سه سال منتهی به Development Cutoff
- `5Y`: پنج سال منتهی به Development Cutoff
- `FULL`: از تاریخ پایه تا اولین کندل واقعی موجود هر Symbol و سپس تا Cutoff

تمام پنجره‌ها به Cutoff منجمد زیر ختم می‌شوند:

```text
2026-07-09T12:00:00Z
```

هیچ داده‌ای بعد از این زمان وارد Development Archive نمی‌شود.

## اصلاح Full-history bootstrap

نسخه 2.1 مشکل Providerهایی را برطرف می‌کند که وقتی `since` قبل از تاریخ Listing باشد، به‌جای اولین کندل موجود، Batch خالی برمی‌گردانند.

رفتار جدید:

1. فقط برای پنجره `FULL` بازه‌های خالی به‌صورت مرحله‌ای Probe می‌شوند.
2. پس از یافتن اولین Batch غیرخالی، مرز آخرین Empty و اولین Non-empty تا دقت یک Timeframe پالایش می‌شود.
3. هر Symbol تاریخ شروع مستقل دارد؛ BTC، ETH و SOL مجبور نیستند از یک تاریخ مشترک داده داشته باشند.
4. هر Provider جداگانه ارزیابی می‌شود و داده چند صرافی در یک Dataset مخلوط نمی‌شود.
5. اگر بعضی Symbolهای FULL قابل دریافت نباشند، وضعیت `PARTIAL_FULL_HISTORY` ثبت می‌شود؛ پنجره‌های سالم 3Y/5Y و Symbolهای سالم FULL همچنان قابل Replay هستند.
6. Replay هر پنجره فقط با Symbolهای دارای Archive تأییدشده اجرا می‌شود.
7. اگر یک Replay خالی یا Skip شود، فایل Replay قدیمی همان پنجره حذف می‌شود تا Validation از خروجی stale استفاده نکند.

## مسیرهای خروجی

```text
data/multi_cycle_archive_v2/3Y/
data/multi_cycle_archive_v2/5Y/
data/multi_cycle_archive_v2/FULL/
logs/multi_cycle_archive_v2/
```

این مسیرها دست‌نخورده می‌مانند:

```text
data/market_replay/
logs/fresh_oos_v2/development_freeze/
```

## تست‌ها

```bat
python -m pytest
```

پس از این اصلاح، روی نسخه‌ای که 131 تست داشت انتظار می‌رود:

```text
136 passed
```

## ساخت و Replay کامل

```bat
python -X utf8 multi_cycle_archive_analysis.py --build --run-replay --symbols BTC/USDT,ETH/USDT,SOL/USDT --timeframe 4h --windows 3Y,5Y,FULL --cutoff 2026-07-09T12:00:00Z --full-start 2017-01-01T00:00:00Z --step 1
```

FULL discovery به‌صورت پیش‌فرض فعال است. تنظیمات اختیاری:

```bat
--listing-probe-days 90
--max-listing-probes 80
```

غیرفعال‌کردن Discovery فقط برای تست یا عیب‌یابی:

```bat
--no-full-discovery
```

برای بازسازی کامل Cacheهای Staging:

```bat
--force-refresh
```

## خروجی‌ها

```text
logs/multi_cycle_archive_v2/multi_cycle_archive_report.json
logs/multi_cycle_archive_v2/multi_cycle_archive_report.md
logs/multi_cycle_archive_v2/archive_dataset_manifest.csv
logs/multi_cycle_archive_v2/archive_build_issues.csv
logs/multi_cycle_archive_v2/multi_cycle_validation_report.json
logs/multi_cycle_archive_v2/rolling_validation.csv
logs/multi_cycle_archive_v2/expanding_validation.csv
logs/multi_cycle_archive_v2/drift_diagnostics.csv
logs/multi_cycle_archive_v2/regime_stability.csv
logs/multi_cycle_archive_v2/replays/3y_replay.csv.gz
logs/multi_cycle_archive_v2/replays/5y_replay.csv.gz
logs/multi_cycle_archive_v2/replays/full_replay.csv.gz
```

هر Manifest اکنون این فیلدها را نیز دارد:

```text
listing_probe_count
listing_boundary_source
listing_boundary_detected
actual_start_utc
provider
```

## تفسیر Status

```text
READY_TO_BUILD            هنوز Archive ساخته نشده است.
PARTIAL_ARCHIVE           حداقل یک Dataset غیر-FULL موجود نیست.
PARTIAL_FULL_HISTORY      3Y/5Y یا بخشی از FULL سالم است، ولی یک یا چند Dataset FULL موجود نیست.
ARCHIVE_READY             Archiveها آماده‌اند ولی Replay اجرا نشده است.
COMPLETE_RESEARCH_ONLY    Archive و Replay کامل شده‌اند؛ هیچ Promotion انجام نشده است.
FAIL_CLOSED               Hash، Provider، Cutoff، Replay یا Leakage Audit معتبر نیست.
```

`PARTIAL_FULL_HISTORY` خطای امنیتی نیست. این Status می‌گوید تاریخ کامل یک یا چند Symbol از Providerهای مجاز قابل دریافت نبوده است؛ Datasetهای موجود همچنان بدون مخلوط‌کردن Provider استفاده می‌شوند.

## کنترل‌های ایمنی

- SHA-256 و `dataset_version_id` برای هر Dataset
- یک Provider برای هر Symbol/Timeframe/Window
- عدم ساخت داده مصنوعی قبل از Listing
- حذف تمام ردیف‌های بعد از Development Cutoff
- Fixed benchmark برابر `score >= 70`
- بدون Tune یا Promotion روی آرشیو چندچرخه‌ای
- `promotion_applied=False`
- `paper_live_enabled=False`
