# Freakto Event-Based Opportunity Universe & Cost-Aware Label v2

- Status: `INSUFFICIENT_EVENT_UNIVERSE`
- Mode: `EVENT_OPPORTUNITY_COST_AWARE_DEVELOPMENT_ONLY`
- Replay window: `FULL`
- Rows loaded/directional/events: `48535 / 16150 / 0`
- Cost-gated events: `0`
- Development candidate: `None`
- Promotion applied: `False`
- Paper/Live enabled: `False`

## Safety contract

Events use entry-time fields only. Outcome fields are used only after event freezing to build conservative, cost-aware labels. Threshold selection is Optimize-only; Holdout is evaluated once. No result authorizes runtime promotion.

## Key findings

## Blockers
- The sparse event universe does not yet contain enough chronological events.

## Warnings
- Event detectors use entry-time replay fields only; replay proxies are not equivalent to full order-book events.
- Triple-Barrier labels use future outcome fields only after the event universe is frozen.
