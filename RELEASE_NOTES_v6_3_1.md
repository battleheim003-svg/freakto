# Freakto v6.3.1 — Bull Probe Evaluation Sync Patch

## Purpose

Fixes the v6.3 reporting mismatch where `STRUCTURE_SCORE_GE_10` could have evaluated Shadow samples in `shadow_gate_signals.csv`, while Bull Regime Probes still showed `NO_FORWARD_SAMPLE`.

## What changed

- `engine/forward_shadow_coverage.py` now uses `shadow_gate_signals.csv` as a fallback evaluation source for Bull probes.
- Bull probes now expose `forward_data_source`, usually either `decision_evaluations` or `shadow_ledger_sync`.
- `Complete Evaluations` in the coverage dashboard is synchronized with evaluated Shadow rows when the decision/evaluation join has no complete rows.
- Status can now report `NO_BEAR_COVERAGE_WITH_BULL_PROBE_CONFLICTS` when Bear coverage is absent but Bull forward evidence conflicts with Backtest.

## Safety

No orders are sent. No Paper Trades are created. Bull probes remain research-only and must not be promoted to Paper/Live without sufficient Forward samples and Backtest agreement.

## Commands

```cmd
python forward_shadow_coverage_dashboard.py --compact
python freakto_research_suite_dashboard.py
python validation_suite_dashboard.py --iterations 20 --trades 10
```
