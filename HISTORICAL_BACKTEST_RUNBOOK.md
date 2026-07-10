# v10 Migration Note — Market Replay جایگزین مسیر اصلی Historical Research

فایل `historical_backtest_dashboard.py` برای سازگاری با خروجی‌های قدیمی باقی مانده است، اما برای داده‌ی ۲ تا ۳ ساله و Replay دقیق باید از دستور زیر استفاده شود:

```cmd
python -X utf8 market_replay_dashboard.py --full --symbols BTC/USDT,ETH/USDT,SOL/USDT --timeframe 4h --years 3 --step 1
```

تفاوت‌های v10:

- Pagination چندساله به‌جای limit تک‌درخواست؛
- Cache محلی فشرده؛
- Gap/Coverage validation؛
- Checkpoint/Resume؛
- Learning Override و Historical Edge خاموش در گذشته؛
- No-lookahead audit؛
- Train/Validation/Test زمانی؛
- Fee و Slippage؛
- برخورد محافظه‌کارانه با Stop/Target همزمان.

راهنمای اصلی: `MARKET_REPLAY_RUNBOOK.md`

---

# Freakto v5.3 Historical Backfill & Backtest Runbook

این بخش برای استفاده از دیتای گذشته ساخته شده است، اما خروجی آن عمداً از Forward Test جدا ذخیره می‌شود.

## هدف

- Replay تصمیم‌های Decision Engine روی کندل‌های گذشته
- جلوگیری از Lookahead در لحظه تصمیم‌گیری
- ارزیابی آینده فقط بعد از ساخت تصمیم
- ساخت دیتای آماری جدا با برچسب `BACKTEST`

## دستورهای اصلی

وضعیت تجمعی Backtest:

```cmd
python historical_backtest_dashboard.py --status
```

اجرای سریع روی چند نماد:

```cmd
python historical_backtest_dashboard.py --symbols BTC/USDT,ETH/USDT,SOL/USDT --limit 800 --step 6
```

اجرای سبک‌تر برای تست GitHub/لوکال:

```cmd
python historical_backtest_dashboard.py --symbols BTC/USDT --limit 300 --step 12 --max-rows-per-symbol 20
```

ارسال خلاصه به تلگرام:

```cmd
python historical_backtest_dashboard.py --symbols BTC/USDT,ETH/USDT,SOL/USDT --limit 800 --step 6 --send
```

## خروجی‌ها

```text
logs/backtests/historical_backtest_<run_id>.csv
logs/backtests/historical_backtest_<run_id>.json
logs/backtests/historical_backtest_report_<run_id>.md
logs/historical_backtest_evaluations.csv
logs/historical_backtest_runs.csv
```

## نکته ایمنی

Backtest جای Forward Test را نمی‌گیرد. اگر Backtest خوب شد ولی Forward بد بود، نتیجه معتبر نیست. اگر هر دو خوب شدند، فقط آن‌وقت می‌شود به Paper جدی یا Micro Live Review فکر کرد.

## معنی چند عدد مهم

- `Directional Win Rate`: درصد نمونه‌های LONG/SHORT که بازده 24h سمت‌دارشان مثبت بوده.
- `Target 1 Hit Rate`: درصد برخورد به تارگت اول در مسیر آینده.
- `Stop Hit Rate`: درصد برخورد به Stop.
- `Avg 24h Return`: میانگین بازده سمت‌دار 24h.

## تنظیم پیشنهادی فعلی

برای شروع:

```cmd
python historical_backtest_dashboard.py --symbols BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT,XRP/USDT,DOGE/USDT --limit 800 --step 6
```

این برای تایم‌فریم 4h تقریباً روزی یک تصمیم replay می‌کند و جلوی حجم بیش‌ازحد لاگ را می‌گیرد.
