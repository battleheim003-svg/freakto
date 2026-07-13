# Freakto Multi-Cycle Feature Decay & Regime Drift — Runbook

## Purpose

This research-only analyzer explains how Freakto's decision-time components,
score behavior, side performance, and market-regime behavior changed across
multiple market cycles.

It consumes the replay files already produced by:

```text
logs/multi_cycle_archive_v2/replays/3y_replay.csv.gz
logs/multi_cycle_archive_v2/replays/5y_replay.csv.gz
logs/multi_cycle_archive_v2/replays/full_replay.csv.gz
```

It does **not** rebuild historical data and does **not** alter the frozen Fresh
OOS dataset.

## Scientific design

The `3Y`, `5Y`, and `FULL` datasets overlap. They must not be counted as three
independent experiments. The analyzer therefore:

1. Selects `FULL` as the primary replay when available.
2. Enforces the frozen Development cutoff.
3. Divides FULL into non-overlapping eras:
   - `LEGACY`: before cutoff minus five years
   - `TRANSITION`: five to three years before cutoff
   - `RECENT`: last three years before cutoff
4. Uses `3Y` and `5Y` only as descriptive nested-window cross-checks.

For the current frozen cutoff:

```text
Development cutoff : 2026-07-09T12:00:00Z
Transition start   : 2021-07-09T12:00:00Z
Recent start       : 2023-07-09T12:00:00Z
```

## Analysis produced

- Component association with future net return by era
- Expected-direction alignment, including inverse alignment for `risk_penalty`
- Top-versus-bottom quantile expectancy spread
- Component distribution drift using PSI
- Recent component redundancy and correlation changes
- LONG/SHORT and per-symbol component decay
- Regime × Side × Symbol drift
- Regime sample-share drift
- Frozen `score >= 70` benchmark decay
- Score-band behavior by era
- Nested `3Y/5Y/FULL` cross-check table

## Safety contract

The analyzer:

- rejects outcome/leakage columns as explanatory features;
- removes rows after the Development cutoff;
- deduplicates replay decisions;
- never tunes weights or thresholds;
- never writes runtime policy files;
- never promotes a model;
- never enables Paper or Live trading.

A status such as `STABLE_EDGE_DIAGNOSTIC` remains descriptive only. It is not a
Live or Paper authorization.

## Installation

Extract the delivered ZIP directly over the Freakto project root, preserving
`engine/` and `tests/` directories.

## Tests

```bat
python -m pytest
```

The package adds 16 tests. Starting from the current 136-test project, the
expected total is:

```text
152 passed
```

## Run the real analysis

```bat
python -X utf8 multi_cycle_feature_decay_analysis.py --replay-root logs/multi_cycle_archive_v2 --output-dir logs/multi_cycle_feature_decay --cutoff 2026-07-09T12:00:00Z
```

Optional stricter sample constraints:

```bat
python -X utf8 multi_cycle_feature_decay_analysis.py --replay-root logs/multi_cycle_archive_v2 --output-dir logs/multi_cycle_feature_decay --cutoff 2026-07-09T12:00:00Z --min-era-samples 300 --min-scope-samples 100 --regime-min-samples 60
```

## Outputs

```text
logs/multi_cycle_feature_decay/component_by_era.csv
logs/multi_cycle_feature_decay/component_decay_summary.csv
logs/multi_cycle_feature_decay/component_distribution_drift.csv
logs/multi_cycle_feature_decay/component_redundancy_drift.csv
logs/multi_cycle_feature_decay/regime_side_matrix.csv
logs/multi_cycle_feature_decay/regime_drift_summary.csv
logs/multi_cycle_feature_decay/score_decay.csv
logs/multi_cycle_feature_decay/nested_window_crosscheck.csv
logs/multi_cycle_feature_decay/multi_cycle_feature_decay_report.json
logs/multi_cycle_feature_decay/multi_cycle_feature_decay_report.md
```

## Component statuses

- `RECENT_HARMFUL`: recent association and quantile spread are adverse.
- `DECAYED`: supportive legacy behavior materially weakened recently.
- `UNSTABLE_SIGN_FLIP`: association direction changed across eras.
- `WEAK_OR_MIXED`: small or contradictory effects.
- `NO_STANDALONE_SIGNAL`: no meaningful standalone relationship.
- `STABLE_OR_RECENT_SUPPORTIVE`: supportive diagnostic, not promotion evidence.
- `INSUFFICIENT_*`: sample coverage is not adequate.

`risk_penalty` is direction-aligned inversely: a higher penalty is considered
supportive when it is associated with lower future return, because that is the
intended meaning of a risk penalty.

## Regime statuses

- `STABLE_EDGE_DIAGNOSTIC`
- `DECAYED_EDGE`
- `CHRONICALLY_NEGATIVE`
- `RECENT_IMPROVEMENT_UNCONFIRMED`
- `UNSTABLE`
- `INSUFFICIENT_*`
- `INELIGIBLE_UNKNOWN`

## Interpretation rule

Do not change a component merely because one diagnostic is negative. A redesign
candidate should satisfy all of the following before runtime consideration:

1. Multi-era diagnostic evidence is coherent.
2. The causal change is specified before new data is observed.
3. The modified model is replayed with a new frozen Development protocol.
4. It succeeds on untouched Fresh OOS.
5. It succeeds in Forward/Paper with realistic costs and fills.

## Recommended commit

```bat
git add engine/multi_cycle_feature_decay.py engine/regime_drift.py multi_cycle_feature_decay_analysis.py tests/test_multi_cycle_feature_decay.py tests/test_regime_drift.py MULTI_CYCLE_FEATURE_DECAY_RUNBOOK.md MULTI_CYCLE_FEATURE_DECAY_IMPLEMENTATION_RESULT.md CHANGED_FILES.txt

git commit -m "feat: add multi-cycle feature decay and regime drift analysis"

git push origin main
```
