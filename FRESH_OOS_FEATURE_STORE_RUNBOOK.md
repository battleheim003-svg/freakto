# Freakto Fresh Out-of-Sample Replay & Feature Store v2

## Purpose

This stage freezes the old replay as Development data and evaluates the existing model on strictly later observations without selecting new thresholds or weights.

## Safety contract

- The latest run in `logs/market_replay/market_replay_evaluations.csv` is copied into a compressed immutable snapshot.
- SHA-256 hashes are stored for both the original source and frozen snapshot.
- Fresh rows must have a decision timestamp strictly later than the frozen cutoff.
- The benchmark remains pre-registered at `score >= 70`; the fresh sample is never searched for a better threshold.
- Entry-time features and future outcome paths are stored in separate files.
- No Paper or Live setting is modified.
- A positive report is still research-only and does not automatically promote a model.

## First execution

```bat
python -m pytest
python -X utf8 fresh_oos_replay_analysis.py
```

The first execution normally returns `READY_AWAITING_FRESH_DATA`, because the current replay file becomes the frozen Development dataset and contains no timestamp after its own cutoff.

## Collect and evaluate genuinely new history

After historical OHLCV files contain candles after the cutoff:

```bat
python -X utf8 fresh_oos_replay_analysis.py --run-replay --symbols BTC/USDT,ETH/USDT,SOL/USDT --timeframes 4h --data-dir data/market_replay
```

The command calls the existing Market Replay engine with `save=False`, so fresh evaluation rows are written only to `logs/fresh_oos_v2` and do not contaminate the frozen Development CSV.

## Outputs

```text
logs/fresh_oos_v2/development_freeze/development_freeze_manifest.json
logs/fresh_oos_v2/development_freeze/development_<dataset_id>.csv.gz
logs/fresh_oos_v2/feature_store_v2/fresh_oos_features_v2.csv.gz
logs/fresh_oos_v2/feature_store_v2/fresh_oos_outcome_paths_v2.csv.gz
logs/fresh_oos_v2/feature_store_v2/feature_store_v2_manifest.json
logs/fresh_oos_v2/fresh_oos_report.json
logs/fresh_oos_v2/fresh_oos_report.md
logs/fresh_oos_v2/fresh_oos_coverage.csv
```

## Feature Store v2 design

`fresh_oos_features_v2.csv.gz` contains only information available at decision time, including indicator values, component scores, regime, planned trade geometry and recorded execution-cost assumptions.

`fresh_oos_outcome_paths_v2.csv.gz` contains one row per future candle and decision, including full OHLCV, signed gross/net return and stop/target touch flags. OHLC data cannot reveal the order of two touches within the same candle, so those cases are explicitly marked and conservatively recorded as stop-first.

## Cost profiles

Recorded Replay fee and slippage fields have priority. When they are absent, the registry reads an optional JSON profile and finally uses a conservative built-in fallback. Copy `data_fresh_oos_cost_profiles.example.json` and replace values only with fees and slippage verified for the exact exchange/account/symbol.

## Interpreting statuses

- `READY_AWAITING_FRESH_DATA`: system is installed correctly, but not enough post-cutoff decisions exist.
- `COMPLETE_NO_PROMOTION`: enough fresh data exists, but the fixed benchmark failed.
- `PASS_FIXED_BENCHMARK_RESEARCH_ONLY`: untouched OOS passed the fixed benchmark; still no automatic Paper/Live activation.
- `FAILED_DATA_INTEGRITY`: overlap, duplicate IDs, path-order violation or feature/outcome leakage was detected.
