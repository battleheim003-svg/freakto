# Freakto v5.3.1 - Backtest Diagnostics Runbook

این ابزار برای فهمیدن علت Edge منفی در Backtest ساخته شده است.

## اجرای سریع

```cmd
python backtest_diagnostics_dashboard.py
```

نسخه خلاصه‌تر:

```cmd
python backtest_diagnostics_dashboard.py --compact
```

ارسال به تلگرام:

```cmd
python backtest_diagnostics_dashboard.py --send
```

## قبل از اجرا

باید اول Backtest تاریخی داشته باشی:

```cmd
python historical_backtest_dashboard.py --symbols BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT,XRP/USDT,DOGE/USDT --limit 800 --step 6
```

Diagnostics از این فایل می‌خواند:

```text
logs/historical_backtest_evaluations.csv
```

## چیزهایی که گزارش می‌دهد

- عملکرد 4h / 12h / 24h
- عملکرد LONG و SHORT جدا
- عملکرد هر نماد
- عملکرد Symbol + Side
- عملکرد Actionability
- Score buckets
- Target/Stop path
- MFE/MAE
- Trend/Momentum/Volume/Structure buckets
- پیشنهادهای اصلاحی برای گیت‌های بعدی

## نکته ایمنی

این گزارش فقط برای تحقیق است. حتی اگر یک bucket مثبت باشد، بدون Forward/Paper کافی نباید وارد Live شد.
