# Freakto Event-Based Opportunity Universe & Cost-Aware Label v2

## Purpose

This research stage stops treating every directional candle as an equal trading opportunity. It creates a sparse, pre-declared event universe and evaluates conservative cost-aware labels and a meta-label model.

The stage is development-only. It does not modify the runtime Decision Engine, score weights, Paper settings, or Live settings.

## Event families

The event universe supports:

- `BREAKOUT_CONFIRMATION`
- `EXTREME_MEAN_REVERSION`
- `VOLATILITY_EXPANSION`
- `REGIME_TRANSITION`
- `LIQUIDITY_SWEEP`

Explicit replay flags are used when available. Otherwise, causal entry-time proxies are used. Outcome fields, future returns, MFE, MAE, exit reasons, and hit flags are prohibited from event detection.

If several events occur on one decision, all event names are retained in `event_types`, but a fixed priority chooses one `primary_event`. This prevents portfolio double counting.

## Cost gate

Before any outcome label is inspected, each event is checked using only planned entry geometry and entry-time cost estimates:

- maximum execution cost
- minimum target-to-cost ratio
- minimum net reward/risk
- maximum risk penalty
- valid entry, target, and stop geometry

A cost gate is not a profitability claim. It only rejects opportunities whose planned geometry cannot plausibly overcome execution costs.

## Cost-aware Triple-Barrier label

After the event universe is frozen, labels are created using:

- Target-1 barrier
- Stop barrier
- fixed event horizon, default 6 candles
- fixed-close time exit
- recorded round-trip costs

When Target and Stop are both touched ambiguously, the label uses conservative `STOP_FIRST` ordering.

`meta_label = 1` means the realized event return after recorded costs was positive relative to the `NO_TRADE = 0` baseline.

## Chronological research protocol

The analyzer uses:

```text
Train -> Purge -> Optimize -> Purge -> Holdout
```

- Meta-model fitting: Train only
- Probability-threshold selection: Optimize only
- Final audit: untouched Holdout once
- Walk-forward: expanding causal folds
- Fresh OOS: fixed frozen model and fixed threshold only

No threshold is selected on Holdout or Fresh OOS.

## Baselines

The common Holdout includes:

- `NO_TRADE`
- `ALL_DIRECTIONAL`
- `CHAMPION_SCORE_GE_70`
- `EVENT_ANY`
- `EVENT_COST_GATED`
- each event family, with and without the pre-trade cost gate
- `EVENT_META_LABEL_V2`

A development candidate must be positive after costs, confidence-supported, walk-forward-stable, sufficiently sampled, and better than the best adequately sampled non-meta baseline by the configured margin.

## Install and test

From the project root:

```bat
.venv\Scripts\activate
python -m pytest
```

After adding this stage to the current 174-test project, the expected total is:

```text
198 passed
```

## Run the real analysis

```bat
python -X utf8 event_opportunity_v2_analysis.py --replay-root logs/multi_cycle_archive_v2 --output-dir logs/event_opportunity_v2 --cutoff 2026-07-09T12:00:00Z --horizon 6
```

## Outputs

```text
logs/event_opportunity_v2/event_universe.csv
logs/event_opportunity_v2/event_overlap.csv
logs/event_opportunity_v2/cost_aware_label_summary.csv
logs/event_opportunity_v2/event_family_benchmarks.csv
logs/event_opportunity_v2/holdout_benchmarks.csv
logs/event_opportunity_v2/meta_threshold_candidates.csv
logs/event_opportunity_v2/meta_model_coefficients.csv
logs/event_opportunity_v2/walk_forward.csv
logs/event_opportunity_v2/prediction_sample.csv
logs/event_opportunity_v2/frozen_event_candidate_manifest.json
logs/event_opportunity_v2/event_opportunity_v2_report.json
logs/event_opportunity_v2/event_opportunity_v2_report.md
```

A frozen model file is written only when all development constraints pass:

```text
logs/event_opportunity_v2/frozen_event_meta_candidate.joblib
```

## Optional fixed Fresh OOS evaluation

Only after a frozen candidate exists and Fresh OOS outcomes are complete:

```bat
python -X utf8 event_opportunity_v2_analysis.py --replay-root logs/multi_cycle_archive_v2 --output-dir logs/event_opportunity_v2 --frozen-model logs/event_opportunity_v2/frozen_event_meta_candidate.joblib --fresh-oos-file PATH_TO_COMPLETE_FRESH_OOS.csv
```

The Fresh OOS path never refits the model and never reselects thresholds.

## Safety

- Development archive and Fresh OOS remain separate.
- No runtime score or event policy is promoted.
- No Paper trade is opened.
- No Live trade is enabled.
- Positive development findings remain diagnostic until untouched Fresh OOS and Forward/Paper confirmation.
