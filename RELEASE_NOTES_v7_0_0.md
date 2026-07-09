# Freakto v7.0.0 — Market Narrative Engine + Event Noise Filter

## Added

- `engine/market_narrative.py`
- `market_narrative_dashboard.py`
- `MARKET_NARRATIVE_RUNBOOK.md`

## Improved

- Automatic Event Collector now has an Event Quality Filter.
- Coinbase product/static pages and SEC navigation fallback noise are filtered out.
- Existing `data/auto_events.csv` is purged from obvious legacy product/navigation noise during the next collector write.
- Causal Intelligence can promote cleaned automatic multi-source context to `MULTI_SOURCE_EVENT_CONSENSUS`.
- Forward Test plan includes `market_narrative_probe`.
- Research Suite includes Market Narrative status.
- Decision logs can carry compact narrative fields.

## Safety

Research-only. No live orders. No new Paper trades.
