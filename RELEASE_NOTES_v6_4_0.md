# Freakto v6.4.0 — Causal/Event Intelligence Core

## Added

- `engine/causal_intelligence.py`
- `causal_intelligence_dashboard.py`
- `causal_event_dashboard.py`
- `data/manual_events.example.csv`
- `CAUSAL_INTELLIGENCE_RUNBOOK.md`

## Updated

- `monitor.py`
- `decision_logger.py`
- `decision_log_repair.py`
- `decision_evaluator.py`
- `engine/forward_test.py`
- `engine/research_upgrade_suite.py`
- GitHub Actions workflows
- `README_NEXT_STEPS.md`
- `FORWARD_TEST_RUNBOOK.md`
- `RESEARCH_ROBUSTNESS_RUNBOOK.md`

## What changed

v6.4 adds a research-only causal/event context layer:

- internal cause detection from structure/volume/trend/momentum/regime/MTF
- source registry with reliability tiers
- external public-source collection from CoinGecko, DefiLlama, Binance Futures, optional FRED, and optional lower-tier sentiment
- manual high-trust event ledger
- catalyst score, event risk, technical/event conflict, causal verdict
- causal columns in decisions/evaluations

## Safety

No live orders. No new paper trades. Research-only tagging/reporting.
