# Freakto Execution Cost & Trade Geometry Optimizer Runbook

## Purpose

This research-only stage tests whether net edge can be recovered by combining:

- entry-time cost-to-target and cost-to-risk filters;
- minimum net reward/risk gates;
- side and score filtering;
- alternative stop widths and 1R/1.5R/2R/3R targets;
- 6-candle and 12-candle horizons;
- conservative break-even and trailing diagnostics;
- chronological Train/Optimize/Holdout selection with purge gaps;
- walk-forward stability checks;
- execution-cost sensitivity from 50% to 150% of recorded cost.

It does **not** modify Decision Engine weights, runtime stops/targets, canonical labels, Paper, or Live.

## Files

- `engine/trade_geometry.py`: pre-trade geometry features and MFE/MAE simulations.
- `engine/execution_cost_optimizer.py`: leakage-safe staged search, walk-forward, Holdout, reports.
- `execution_cost_geometry_analysis.py`: command-line entry point.
- `tests/test_trade_geometry.py`: geometry, cost, path and management tests.
- `tests/test_execution_cost_optimizer.py`: split, leakage, fail-closed, Holdout and artifact tests.

## Run

```bat
python -m pytest
python -X utf8 execution_cost_geometry_analysis.py
```

Optional:

```bat
python -X utf8 execution_cost_geometry_analysis.py ^
  --dataset logs\market_replay\market_replay_evaluations.csv ^
  --output-dir logs\execution_geometry
```

## Output files

```text
logs/execution_geometry/execution_geometry_report.json
logs/execution_geometry/execution_geometry_report.md
logs/execution_geometry/execution_geometry_candidates.csv
logs/execution_geometry/execution_geometry_walk_forward.csv
logs/execution_geometry/execution_geometry_holdout.csv
logs/execution_geometry/execution_cost_sensitivity.csv
logs/execution_geometry/execution_geometry_shadow_predictions.csv
```

## Safety and leakage controls

1. The latest replay run is selected to avoid repeated market-history counting.
2. Splits are based on unique timestamps, not row order alone.
3. Twelve candles are purged between Train, Optimize and Holdout.
4. Candidate entry gates use only score, side, planned geometry and recorded execution cost.
5. MFE, MAE and future returns are used only to build research outcomes.
6. Candidate selection occurs on Train/Optimize; Holdout is audited once.
7. Only one selected candidate reaches Holdout.
8. Aggregate MFE/MAE does not preserve complete price-path ordering. Break-even and trailing candidates are therefore diagnostic-only unless full paths are recorded.
9. `promotion_applied` and `paper_live_enabled` always remain `False` in this tool.

## ATR behavior

The optimizer supports native percentage ATR fields when one of these columns exists:

```text
atr_pct
atr_14_pct
atr_percent
atr14_pct
normalized_atr_pct
```

The current replay dataset does not contain one of those fields. The recorded planned-stop distance is therefore used as an explicit `PLANNED_STOP_PROXY` risk unit. The report discloses this fallback.

## Promotion requirements

A policy can only be recommended when it has:

- positive Train expectancy;
- positive Optimize expectancy;
- Optimize profit factor of at least 1.05;
- sufficient samples;
- required walk-forward pass rate;
- positive untouched Holdout expectancy;
- Holdout profit factor of at least 1.05;
- acceptable drawdown relative to canonical Holdout;
- promotion-eligible path information.

A `FAIL` status is a valid research result and must not be bypassed by manually lowering thresholds.
