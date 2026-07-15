# Freakto Scheduled Paper Cycle & Performance Dashboard

## Cloud schedule

The GitHub workflow runs automatically at 00:09, 04:09, 08:09, 12:09, 16:09 and 20:09 UTC. These times are nine minutes after each 4-hour candle boundary. Manual `workflow_dispatch` remains available.

GitHub Actions must remain enabled and the workflow file must be on the repository default branch. The existing `paper-state` branch stores persistent state between ephemeral runners.

## Dashboard lifecycle

Every cycle runs the market monitor, decision evaluation, paper scan, paper evaluation, performance dashboard generation and readiness status. Dashboard files are written to `logs/paper_performance/`, uploaded as a run Artifact and packed into persistent cloud state.

## Outputs

- `paper_performance_summary.json`
- `paper_performance_dashboard.md`
- `paper_performance_ledger.csv`
- `paper_performance_by_regime.csv`
- `paper_equity_curve.csv`
- `paper_equity_curve.png`

## Metrics

Metrics use the latest evaluation per `paper_trade_id`. Only CLOSED trades contribute to Win Rate, Profit Factor, Expectancy, Cumulative R and Max Drawdown. Open trades remain visible in signal/open counts. Net R is preferred over gross R.

Regime grouping uses the first available entry-time label in this order: `regime_label`, `market_mode`, `primary_event`, `regime`, `risk_tone`, then `UNKNOWN`.

## Local command

```bat
python -X utf8 paper_performance_dashboard.py
```

Telegram summary:

```bat
python -X utf8 paper_performance_dashboard.py --send
```

## Safety

This suite is research-paper only. It never enables live orders, real capital or non-zero allocation.
