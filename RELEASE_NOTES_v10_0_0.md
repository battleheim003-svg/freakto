# Freakto v10.0.0 — Historical Data Store & Market Replay

## Added

- Paginated multi-year OHLCV downloader with CCXT provider fallback.
- Local compressed historical dataset cache and per-dataset manifest.
- Coverage, gap, duplicate, invalid OHLC and continuity validation.
- Candle-by-candle replay using the current Decision Engine.
- Replay-safe mode that disables persisted Learning Overrides and Historical Edge.
- Automated no-lookahead feature audit.
- Chronological Train/Validation/Test splits.
- Fee/slippage-adjusted returns, MFE/MAE, target/stop and conservative intrabar ambiguity handling.
- Checkpoint/resume support.
- Experiment and dataset fingerprints so different replay configurations are not mixed.
- Optional timestamped historical context file with backward-only merge.
- Cumulative replay ledger and status integration into the Research/Validation suites.
- Manual GitHub Actions workflow for historical data and replay artifacts.

## New files

```text
engine/historical_data_store.py
engine/market_replay.py
market_replay_dashboard.py
MARKET_REPLAY_RUNBOOK.md
RELEASE_NOTES_v10_0_0.md
run_market_replay.bat
data/market_replay_context_template.csv
tests/test_market_replay.py
.github/workflows/freakto-market-replay.yml
```

## Modified files

```text
engine/decision.py
engine/historical_backtest.py
engine/research_upgrade_suite.py
engine/live_readiness_score.py
validation_suite_dashboard.py
README.md
README_NEXT_STEPS.md
HISTORICAL_BACKTEST_RUNBOOK.md
GITHUB_ACTIONS_SETUP_FA.md
.gitignore
```

## Safety

- No Live order is sent.
- No Paper trade is opened.
- Replay output remains separate from Forward Test.
- Historical news/event intelligence is not invented; it requires an explicitly timestamped historical context dataset.
