# Freakto Multi-Cycle Historical Archive v2 — Runbook

این ابزار یک آرشیو Development چندچرخه‌ای می‌سازد و **هیچ تغییری در Fresh OOS Freeze، Paper یا Live ایجاد نمی‌کند**.

## هدف

سه پنجره جدا ساخته می‌شود:

- `3Y`: سه سال منتهی به Development Cutoff
- `5Y`: پنج سال منتهی به Development Cutoff
- `FULL`: از تاریخ پایه مشخص‌شده تا Development Cutoff

تمام پنجره‌ها به یک Cutoff منجمد ختم می‌شوند. هیچ داده‌ای بعد از Cutoff وارد Training/Development Archive نمی‌شود.

## مسیرهای خروجی

```text
data/multi_cycle_archive_v2/3Y/
data/multi_cycle_archive_v2/5Y/
data/multi_cycle_archive_v2/FULL/
logs/multi_cycle_archive_v2/
```

آرشیو اصلی `data/market_replay` و پوشه زیر دست‌نخورده باقی می‌مانند:

```text
logs/fresh_oos_v2/development_freeze/
```

## اجرای تست‌ها

```bat
python -m pytest
```

## ساخت آرشیوها

بهتر است Cutoff را صریح وارد کنی. Cutoff فعلی پروژه:

```text
2026-07-09T12:00:00Z
```

ساخت آرشیو سه‌ساله، پنج‌ساله و Full-history:

```bat
python -X utf8 multi_cycle_archive_analysis.py --build --symbols BTC/USDT,ETH/USDT,SOL/USDT --timeframe 4h --windows 3Y,5Y,FULL --cutoff 2026-07-09T12:00:00Z --full-start 2017-01-01T00:00:00Z --step 1
```

دریافت Full-history ممکن است زمان‌بر باشد. ابزار برای هر Symbol/Timeframe فقط یک Provider را نگه می‌دارد و Providerها را در یک Dataset مخلوط نمی‌کند.

## اجرای Replay چندچرخه‌ای

پس از کامل‌شدن آرشیوها:

```bat
python -X utf8 multi_cycle_archive_analysis.py --run-replay --symbols BTC/USDT,ETH/USDT,SOL/USDT --timeframe 4h --windows 3Y,5Y,FULL --cutoff 2026-07-09T12:00:00Z --step 1
```

ساخت و Replay در یک مرحله:

```bat
python -X utf8 multi_cycle_archive_analysis.py --build --run-replay --symbols BTC/USDT,ETH/USDT,SOL/USDT --timeframe 4h --windows 3Y,5Y,FULL --cutoff 2026-07-09T12:00:00Z --full-start 2017-01-01T00:00:00Z --step 1
```

## خروجی‌ها

```text
logs/multi_cycle_archive_v2/multi_cycle_archive_report.json
logs/multi_cycle_archive_v2/multi_cycle_archive_report.md
logs/multi_cycle_archive_v2/archive_dataset_manifest.csv
logs/multi_cycle_archive_v2/multi_cycle_validation_report.json
logs/multi_cycle_archive_v2/rolling_validation.csv
logs/multi_cycle_archive_v2/expanding_validation.csv
logs/multi_cycle_archive_v2/drift_diagnostics.csv
logs/multi_cycle_archive_v2/regime_stability.csv
logs/multi_cycle_archive_v2/replays/3y_replay.csv.gz
logs/multi_cycle_archive_v2/replays/5y_replay.csv.gz
logs/multi_cycle_archive_v2/replays/full_replay.csv.gz
```

## کنترل‌های ایمنی

- هر Dataset دارای SHA-256 و `dataset_version_id` است.
- هر Dataset فقط یک Provider دارد.
- Listing/Provider boundary به‌صورت Warning ثبت می‌شود؛ داده مصنوعی برای قبل از Listing ساخته نمی‌شود.
- هر ردیف بعد از Development Cutoff حذف و Block می‌شود.
- Rolling و Expanding Windowها فقط برای ارزیابی هستند.
- Threshold ثابت `score >= 70` تغییر نمی‌کند.
- هیچ Weight یا Gate روی داده چندچرخه‌ای Tune یا Promote نمی‌شود.
- `promotion_applied=False` و `paper_live_enabled=False` همیشه حفظ می‌شوند.

## تفسیر Status

```text
READY_TO_BUILD           آرشیوی هنوز ساخته نشده است.
PARTIAL_ARCHIVE          حداقل یک Symbol/Window موجود نیست.
ARCHIVE_READY            آرشیوها آماده‌اند ولی Replay اجرا نشده است.
COMPLETE_RESEARCH_ONLY   آرشیو و Replay کامل شده‌اند؛ هیچ Promotion انجام نشده است.
FAIL_CLOSED              Hash، Provider، Cutoff یا Leakage Audit معتبر نیست.
```

## نکته درباره FULL History

برای نمادهایی مثل SOL، تاریخ واقعی ممکن است دیرتر از `--full-start` آغاز شود. ابزار این وضعیت را به‌عنوان `listing_boundary_detected=true` ثبت می‌کند و Coverage را جعل نمی‌کند.
