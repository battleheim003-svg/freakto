# Freakto v5.3.0 — Historical Backfill & Backtest Engine

## هدف

استفاده از دیتای گذشته برای سنجش اولیه Edge، بدون اینکه خروجی Backtest با Forward Test قاطی شود.

## فایل‌های جدید

```text
engine/historical_backtest.py
historical_backtest_dashboard.py
HISTORICAL_BACKTEST_RUNBOOK.md
RELEASE_NOTES_v5_3_0.md
```

## فایل‌های اصلاح‌شده

```text
validation_suite_dashboard.py
README_NEXT_STEPS.md
```

## خروجی‌های جدید

```text
logs/backtests/historical_backtest_<run_id>.csv
logs/backtests/historical_backtest_<run_id>.json
logs/backtests/historical_backtest_report_<run_id>.md
logs/historical_backtest_evaluations.csv
logs/historical_backtest_runs.csv
```

## دستورها

```cmd
python historical_backtest_dashboard.py --status
python historical_backtest_dashboard.py --symbols BTC/USDT --limit 300 --step 12 --max-rows-per-symbol 20
python historical_backtest_dashboard.py --symbols BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT,XRP/USDT,DOGE/USDT --limit 800 --step 6
python historical_backtest_dashboard.py --symbols BTC/USDT,ETH/USDT,SOL/USDT --limit 800 --step 6 --send
python validation_suite_dashboard.py
```

## نکته ایمنی

این نسخه هیچ سفارش واقعی ارسال نمی‌کند، Paper Trade ثبت نمی‌کند و Live Trading را فعال نمی‌کند. Backtest فقط یک لایه Research است.
