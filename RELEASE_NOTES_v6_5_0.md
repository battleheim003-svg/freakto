
# Freakto v6.5.0 — Automatic Event Collector

## Added

- `engine/auto_event_collector.py`
- `automatic_event_collector_dashboard.py`
- `data/auto_event_sources.example.json`
- `AUTO_EVENT_COLLECTOR_RUNBOOK.md`
- `RELEASE_NOTES_v6_5_0.md`

## Updated

- `engine/causal_intelligence.py` now loads `data/auto_events.csv` alongside `data/manual_events.csv`.
- `causal_event_dashboard.py` now displays both manual and automatic event ledgers.
- `decision_logger.py`, `decision_log_repair.py`, and `decision_evaluator.py` now preserve `causal_auto_event_count`.
- `engine/forward_test.py` now runs `automatic_event_collector` before `causal_intelligence_probe`.
- GitHub Actions now runs the automatic event collector in the Forward Test workflow.
- Research Suite includes an `automatic_event_collector` section.

## Safety

Research-only. No Paper/Live activation.
