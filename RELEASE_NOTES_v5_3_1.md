# Freakto v5.3.1 - Backtest Diagnostics & Edge Breakdown

## Added

- `engine/backtest_diagnostics.py`
- `backtest_diagnostics_dashboard.py`
- `BACKTEST_DIAGNOSTICS_RUNBOOK.md`

## Updated

- `validation_suite_dashboard.py`
- `README_NEXT_STEPS.md`

## Purpose

v5.3.0 showed that the current historical backtest has negative average 24h return. v5.3.1 diagnoses why by breaking down performance across:

- holding period
- side
- symbol
- symbol + side
- actionability
- score bucket
- confidence/risk label
- target/stop path
- component buckets
- MFE/MAE

## Commands

```cmd
python backtest_diagnostics_dashboard.py
python backtest_diagnostics_dashboard.py --compact
python backtest_diagnostics_dashboard.py --send
python validation_suite_dashboard.py
```

## Safety

This is research only. It never sends orders and never creates paper trades.
