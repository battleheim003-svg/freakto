# Freakto v9.0.0 - Evidence Graph Engine

## Added

- `engine/evidence_graph.py`
- `evidence_graph_dashboard.py`
- `EVIDENCE_GRAPH_RUNBOOK.md`

## What it does

Builds a research-only evidence graph:

```text
Evidence Source -> Narrative -> Root Cause -> Decision Context -> Outcome
```

The graph tracks:

- nodes
- edges
- evidence paths
- hit-rate after 24h
- average signed return after 24h
- low-sample maturity
- provisional evidence-weight learning signals

## Safety

No Paper trades, Live trades, exchange orders, or autonomous entries are created.
This is only a research/audit layer.
