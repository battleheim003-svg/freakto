# Feature Architecture v2 — Implementation Result

## Implementation status

```text
COMPLETE
```

The package implements a score-independent Feature Architecture v2 and a chronological Baseline Benchmark Suite.

## Files implemented

- `engine/feature_architecture_v2.py`
- `engine/baseline_benchmarks.py`
- `feature_architecture_v2_analysis.py`
- `tests/test_feature_architecture_v2.py`
- `tests/test_baseline_benchmarks.py`

## Safety assertions verified

- Aggregate `score` is excluded from model features.
- Outcome/leakage feature names are rejected.
- LONG and SHORT models are separate.
- Structure is a gate rather than an additive component.
- Momentum is capped and can be removed in a declared variant.
- Chronological splits use unique timestamps and purge gaps.
- Thresholds are selected on Optimize, not Holdout.
- Frozen Fresh OOS evaluation performs no refitting and no threshold reselection.
- Promotion, Paper, and Live remain disabled.

## Test result

```text
22 passed
compileall passed
```

Tests cover:

- leakage rejection;
- Development/Fresh cutoff separation;
- duplicate removal;
- feature engineering;
- cost/volatility geometry;
- structure and risk gates;
- side-specific fitting;
- no-momentum variant;
- chronological purge splits;
- Optimize-only threshold selection;
- coefficient export;
- deterministic bootstrap intervals;
- simple baseline availability;
- common-Holdout comparison;
- Walk-forward no-overlap;
- frozen candidate evaluation without refitting;
- output writing and safety metadata.

## Synthetic integration smoke test

A 5,000-row synthetic multi-cycle replay was used only to validate the full execution path.

```text
Selected replay window : FULL
Available windows      : 3Y,5Y,FULL
Rows loaded/usable     : 5000 / 5000
Variants evaluated     : 4
Baselines evaluated    : 8
Status                 : COMPLETE_NO_DEVELOPMENT_CANDIDATE
Promotion applied      : False
Paper/Live enabled     : False
```

The synthetic result is not evidence about the real trading strategy. The authoritative result must be generated locally from the user's real `full_replay.csv.gz`.

## Real-data command

```bat
python -X utf8 feature_architecture_v2_analysis.py --replay-root logs/multi_cycle_archive_v2 --output-dir logs/feature_architecture_v2 --cutoff 2026-07-09T12:00:00Z
```

Given the already observed negative historical expectancy and weak score monotonicity, `COMPLETE_NO_DEVELOPMENT_CANDIDATE` is a plausible real-data outcome. The analyzer must be allowed to report that honestly; constraints should not be lowered to force a candidate.
