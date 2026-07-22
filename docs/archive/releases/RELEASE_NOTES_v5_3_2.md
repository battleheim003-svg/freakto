# Freakto v5.3.2 — Backtest Gate Simulator

## هدف

بعد از v5.3.1 مشخص شد Backtest کلی Edge مثبت ندارد، اما چند subset مثل Symbol+Side یا Score Bucket نشانه‌های مثبت کم‌نمونه دارند. v5.3.2 برای تست دقیق این subsetها ساخته شد.

## فایل‌های جدید

```text
engine/backtest_gate_simulator.py
backtest_gate_simulator_dashboard.py
BACKTEST_GATE_SIMULATOR_RUNBOOK.md
RELEASE_NOTES_v5_3_2.md
```

## فایل‌های اصلاح‌شده

```text
validation_suite_dashboard.py
README_NEXT_STEPS.md
```

## قابلیت‌ها

- تست ده‌ها gate تحقیقاتی روی `logs/historical_backtest_evaluations.csv`
- تفکیک بر اساس:
  - ACTIONABLE / WATCHLIST
  - LONG / SHORT
  - Symbol
  - Symbol + Side
  - Score thresholds
  - Score buckets
  - Confidence / Risk / Regime
  - Trend / Momentum / Volume / Structure / Historical Edge
- محاسبه برای هر gate:
  - Samples
  - Avg Return
  - Win Rate
  - Target 1 Hit Rate
  - Stop Hit Rate
  - MFE/MAE
  - Research Score
  - Verdict
- ذخیره JSON/Markdown/CSV

## Lookahead Safety

Gate filters فقط از فیلدهای live-known استفاده می‌کنند. فیلدهای آینده مثل return، target، stop، MFE و MAE فقط برای ارزیابی به کار می‌روند.

## دستورات

```cmd
python backtest_gate_simulator_dashboard.py --compact
python backtest_gate_simulator_dashboard.py --compact --min-samples 30 --horizon 24h
python backtest_gate_simulator_dashboard.py --compact --horizon 4h
python backtest_gate_simulator_dashboard.py --send
```

## خروجی‌ها

```text
logs/backtests/gate_simulator/gate_simulation_<run_id>.json
logs/backtests/gate_simulator/gate_simulation_report_<run_id>.md
logs/backtests/gate_simulator/gate_simulation_results_<run_id>.csv
```

## نکته ایمنی

این نسخه هیچ gateای را وارد Paper/Live نمی‌کند. همه خروجی‌ها فقط برای Research هستند.
