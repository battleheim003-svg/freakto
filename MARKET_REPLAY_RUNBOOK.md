# Freakto v10.0 — Historical Data & Market Replay Runbook

## هدف

Market Replay نسخه‌ی v10 برای حل ضعف داده‌ی تاریخی ساخته شده است. این بخش دو کار جدا انجام می‌دهد:

1. دریافت چندساله‌ی OHLCV با pagination و ذخیره‌ی محلی؛
2. اجرای Decision Engine به‌صورت کندل‌به‌کندل، بدون دیدن کندل‌های آینده.

خروجی Market Replay فقط برای Research و Backtest است و هیچ Paper/Live order ایجاد نمی‌کند.

## اجرای پیشنهادی مرحله‌به‌مرحله

### 1. تست وضعیت فعلی

```cmd
python -X utf8 market_replay_dashboard.py --status --compact
```

### 2. دریافت سه سال داده برای BTC

```cmd
python -X utf8 market_replay_dashboard.py --build-data --symbols BTC/USDT --timeframe 4h --years 3 --compact
```

### 3. Replay سریع اولیه، تقریباً روزی یک تصمیم

در تایم‌فریم 4h، مقدار `--step 6` یعنی هر 6 کندل یک تصمیم:

```cmd
python -X utf8 market_replay_dashboard.py --replay --symbols BTC/USDT --timeframe 4h --years 3 --step 6 --compact
```

### 4. اجرای کامل روی پورتفو

```cmd
python -X utf8 market_replay_dashboard.py --full --symbols BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT,XRP/USDT,DOGE/USDT --timeframe 4h --years 3 --step 1
```

برای شروع سبک‌تر، `--step 6` استفاده شود و بعد از تأیید سلامت داده، Replay دقیق با `--step 1` اجرا شود.

## بازه‌ی تاریخی دقیق

```cmd
python -X utf8 market_replay_dashboard.py --full --symbols BTC/USDT,ETH/USDT --timeframe 4h --start 2023-01-01 --end 2026-01-01 --step 1
```

تمام تاریخ‌ها UTC هستند.

## انتخاب صرافی

حالت پیش‌فرض:

```text
exchange=auto
order=kucoin,okx,bybit,kraken
```

سیستم providerها را امتحان می‌کند و dataset با پوشش بهتر را نگه می‌دارد. برای جلوگیری از مخلوط شدن microstructure صرافی‌ها، یک dataset نهایی از یک provider ساخته می‌شود.

انتخاب دستی:

```cmd
python -X utf8 market_replay_dashboard.py --build-data --symbols BTC/USDT --years 3 --exchange okx
```

## Cache و به‌روزرسانی

اگر dataset موجود پوشش کافی داشته باشد، دوباره دانلود نمی‌شود. برای دریافت مجدد کامل:

```cmd
python -X utf8 market_replay_dashboard.py --build-data --symbols BTC/USDT --years 3 --force-refresh
```

## ادامه‌ی اجرای قطع‌شده

Market Replay به‌طور دوره‌ای checkpoint می‌سازد. Run ID اجرای قطع‌شده را بردار و اجرا کن:

```cmd
python -X utf8 market_replay_dashboard.py --resume market_replay_YYYYMMDD_HHMMSS --symbols BTC/USDT,ETH/USDT --timeframe 4h
```

پارامترهای symbols/timeframe باید با اجرای اصلی یکسان باشند.

## جلوگیری از Lookahead

در Replay، این دو بخش به‌صورت اجباری خاموش‌اند:

```text
Learning Overrides
Historical Edge
```

چون فایل‌های آن‌ها ممکن است با داده‌ای ساخته شده باشند که در زمان کندل تاریخی هنوز وجود نداشته است.

همچنین موتور چند نقطه‌ی تاریخی را دوباره محاسبه می‌کند و نتیجه‌ی اندیکاتورها را با Featureهای از قبل محاسبه‌شده مقایسه می‌کند. خروجی سالم باید باشد:

```text
Leakage Audit: PASSED_NO_LOOKAHEAD
```

اگر Audit شکست بخورد و حالت strict فعال باشد، Replay متوقف می‌شود.

## داده‌ی تاریخی اخبار و Context

OHLCV به‌تنهایی نمی‌تواند خبرها، ETF flow، Funding، On-chain و Narrative تاریخی را بازسازی کند. نسخه v10 یک ورودی اختیاری زمان‌دار دارد:

```cmd
python -X utf8 market_replay_dashboard.py --replay --symbols BTC/USDT --context-file data/market_replay_context.csv
```

حداقل ستون‌ها:

```text
timestamp_utc,symbol
```

ستون‌های اختیاری قابل استفاده:

```text
news_sentiment_score
news_sentiment_summary
onchain_signal_score
onchain_status
cross_exchange_volume_ratio
cross_exchange_provider_count
```

فقط Contextهایی استفاده می‌شوند که timestamp آن‌ها مساوی یا قبل از کندل Replay باشد. merge آینده ممنوع است.

## هزینه و Slippage

پیش‌فرض برای هر سمت ورود/خروج:

```text
Fee: 10 bps
Slippage: 5 bps
```

مثال تغییر:

```cmd
python -X utf8 market_replay_dashboard.py --replay --symbols BTC/USDT --fee-bps 8 --slippage-bps 4
```

Net Return هزینه‌ی رفت و برگشت را کم می‌کند.

## نحوه‌ی برخورد با Stop و Target همزمان

OHLC ترتیب حرکت داخل کندل را نشان نمی‌دهد. اگر Stop و Target 1 در یک کندل لمس شوند:

```text
intrabar_ambiguity = True
first_exit_reason = STOP_FIRST_CONSERVATIVE_AMBIGUOUS
```

این روش عمداً محافظه‌کارانه است.

## شناسه‌ی Experiment و جلوگیری از مخلوط شدن Runها

هر ترکیب تنظیمات Replay و نسخه‌ی dataset یک `replay_experiment_id` جدا می‌سازد. بنابراین تغییر Fee، Slippage، Step، Min Score، Context یا داده‌ی تاریخی باعث نمی‌شود نتیجه‌ی آزمایش جدید روی آزمایش قدیمی overwrite شود.

```text
replay_experiment_id
replay_data_fingerprint
```

برای مقایسه‌ی Strategyها باید ابتدا بر اساس `replay_experiment_id` گروه‌بندی شود.

## تقسیم زمانی

Replay به شکل زمانی، نه تصادفی، تقسیم می‌شود:

```text
TRAIN_60
VALIDATION_20
TEST_20
```

Test split باید برای تصمیم نهایی دست‌نخورده بماند. تنظیم Strategy/Gate بر اساس Test split باعث Overfitting می‌شود.

## خروجی داده‌های تاریخی

```text
data/market_replay/<timeframe>/<SYMBOL>.csv.gz
data/market_replay/<timeframe>/<SYMBOL>.manifest.json
logs/market_replay/data_quality/*.json
```

## خروجی Replay

```text
logs/market_replay/<run_id>.csv
logs/market_replay/<run_id>.json
logs/market_replay/<run_id>_report.md
logs/market_replay/market_replay_evaluations.csv
logs/market_replay/market_replay_runs.csv
logs/market_replay/checkpoints/
```

## معیار حداقل پیشنهادی

قبل از اینکه نتیجه Replay جدی تلقی شود:

```text
Leakage Audit = PASSED_NO_LOOKAHEAD
Complete Rows >= 500
Test Directional Rows >= 50
Test Avg Net Return > 0
Forward Test مستقل نیز نتیجه را تأیید کند
```

عبور از این موارد اجازه‌ی Live نمی‌دهد؛ فقط یک Strategy/Gate را به Research Candidate تبدیل می‌کند.

## v10.1.5 Canonical Evaluation Metrics

برای Replayهای قدیمی ابتدا Dry Run بگیر:

```cmd
python -X utf8 replay_evaluation_recorder_dashboard.py
```

سپس Backfill امن را اعمال کن:

```cmd
python -X utf8 replay_evaluation_recorder_dashboard.py --apply
```

بعد Thresholdها را با Split زمانی واقعی ارزیابی کن:

```cmd
python -X utf8 replay_real_metrics_dashboard.py --compact
```

Backfill قبل از بازنویسی CSV، Backup زمان‌دار می‌سازد.


## v10.2 Score Calibration

پس از Replay و v10.1.5:

```cmd
python -X utf8 replay_score_calibration_dashboard.py --compact
```

این مرحله monotonicity Score، Feature attribution، Feature interactions و عملکرد Symbol/Regime/Side را روی Splitهای زمانی بررسی می‌کند.
