# Freakto Feature Architecture v2 & Baseline Benchmark Suite

## Purpose

This research stage tests whether a score-independent, interpretable architecture can outperform simple baselines on the frozen Development Archive.

It does **not** replace `DecisionEngine`, change runtime weights, enable Paper, or enable Live trading.

## Design

Feature Architecture v2 follows these contracts:

- LONG and SHORT are fitted independently.
- Aggregate `score` is metadata only and is never a model input.
- Structure is an entry gate, not an additive score.
- Momentum is capped; a declared no-momentum variant is tested separately.
- Trend and Momentum are normalized by volatility when ATR is available.
- Execution cost and planned reward/risk are explicit features when available.
- Outcome, future, MFE/MAE, target-hit, stop-hit, and return fields are rejected as features.
- Chronological Train / Optimize / Holdout use unique timestamps and purge gaps.
- Thresholds are selected only on Optimize and audited once on untouched Development Holdout.
- Final authorization still requires untouched Fresh OOS and Forward/Paper evidence.

## Variants

- `ARCH_V2_BASE`
- `ARCH_V2_NO_MOMENTUM`
- `ARCH_V2_LEAN`
- `ARCH_V2_LONG_ONLY`

## Simple baselines

- `ALL_DIRECTIONAL`
- `CHAMPION_SCORE_GE_70`
- `LONG_ONLY`
- `SHORT_ONLY`
- `TREND_ONLY`
- `MEAN_REVERSION_RSI` when RSI is available
- `BUY_AND_HOLD` observation baseline when market return is available
- `RANDOM_DIRECTIONAL` deterministic observation baseline when market return is available

Buy-and-hold and random-direction results are per replay observation. They are research comparators, not a capital-allocation backtest.

## Installation

No new dependency is required. `scikit-learn` and `joblib` already exist in `requirements.txt`.

## Tests

```bat
python -m pytest
```

This package adds 22 tests. If the project currently has 152 tests, the expected count is:

```text
174 passed
```

## Run the Development benchmark

```bat
python -X utf8 feature_architecture_v2_analysis.py --replay-root logs/multi_cycle_archive_v2 --output-dir logs/feature_architecture_v2 --cutoff 2026-07-09T12:00:00Z
```

The analyzer automatically prefers `FULL`, while `5Y` and `3Y` remain available as archive context. It does not concatenate nested windows.

## Outputs

```text
logs/feature_architecture_v2/holdout_benchmarks.csv
logs/feature_architecture_v2/threshold_candidates.csv
logs/feature_architecture_v2/side_diagnostics.csv
logs/feature_architecture_v2/feature_coefficients.csv
logs/feature_architecture_v2/walk_forward.csv
logs/feature_architecture_v2/prediction_sample.csv
logs/feature_architecture_v2/frozen_candidate_manifest.json
logs/feature_architecture_v2/feature_architecture_v2_report.json
logs/feature_architecture_v2/feature_architecture_v2_report.md
```

If and only if a Development candidate passes all strict constraints, this additional file is created:

```text
logs/feature_architecture_v2/frozen_architecture_candidate.joblib
```

Creation of that file is **not** promotion. It only freezes the exact Development model, gates, and thresholds for future untouched evaluation.

## Candidate constraints

A Development candidate must simultaneously satisfy:

- positive Holdout net expectancy;
- Holdout profit factor at least `1.05`;
- at least 200 selected Holdout observations;
- block-bootstrap lower confidence bound above zero;
- positive Walk-forward fraction at least `2/3`;
- expectancy at least `0.05%` above the best simple baseline;
- Optimize-selected thresholds only.

If any condition fails, status remains:

```text
COMPLETE_NO_DEVELOPMENT_CANDIDATE
```

## Fixed Fresh OOS evaluation

Only use this after:

1. a frozen model file exists;
2. Fresh OOS outcomes are complete;
3. the Fresh file contains both entry-time fields and the canonical net outcome.

```bat
python -X utf8 feature_architecture_v2_analysis.py ^
  --replay-root logs/multi_cycle_archive_v2 ^
  --output-dir logs/feature_architecture_v2 ^
  --cutoff 2026-07-09T12:00:00Z ^
  --frozen-model logs/feature_architecture_v2/frozen_architecture_candidate.joblib ^
  --fresh-oos-file logs/fresh_oos_v2/fresh_oos_evaluated_rows.csv
```

The Fresh evaluator:

- keeps only timestamps strictly after the Development cutoff;
- loads the frozen model as-is;
- does not refit;
- does not reselect thresholds;
- does not promote or enable Paper/Live.

If the joined evaluated Fresh file does not yet exist, continue collecting Fresh OOS data. Do not join future outcomes into the entry-time Feature Store used for model fitting.

## Status interpretation

### `COMPLETE_NO_DEVELOPMENT_CANDIDATE`

No architecture variant passed all Development requirements. Do not create a runtime integration.

### `COMPLETE_DEVELOPMENT_CANDIDATE_FROZEN`

One exact candidate was frozen for untouched Fresh OOS evaluation. This is still **NO-GO** for Paper/Live promotion.

### `READY_AWAITING_MULTI_CYCLE_REPLAY`

The required replay files were not found under `logs/multi_cycle_archive_v2/replays`.

## Safety

- Development archive only for model fitting and threshold selection.
- Fresh OOS is never used for fitting or threshold tuning.
- No automatic runtime integration.
- No Paper/Live activation.
- Positive results remain diagnostic until Forward/Paper confirmation.
