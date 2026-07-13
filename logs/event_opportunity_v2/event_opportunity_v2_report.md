# Freakto Event-Based Opportunity Universe & Cost-Aware Label v2

- Status: `COMPLETE_NO_DEVELOPMENT_CANDIDATE`
- Mode: `EVENT_OPPORTUNITY_COST_AWARE_DEVELOPMENT_ONLY`
- Replay window: `FULL`
- Rows loaded/directional/events: `48535 / 16150 / 3589`
- Cost-gated events: `0`
- Development candidate: `None`
- Promotion applied: `False`
- Paper/Live enabled: `False`

## Safety contract

Events use entry-time fields only. Outcome fields are used only after event freezing to build conservative, cost-aware labels. Threshold selection is Optimize-only; Holdout is evaluated once. No result authorizes runtime promotion.

## Key findings
- Event detector schema mode: REPLAY_COMPONENT_SCHEMA.
- Raw family matches before priority: breakout=2449, mean_reversion=4, volatility_expansion=1420, regime_transition=823, liquidity_sweep=0.
- Unavailable without explicit entry-time data: LIQUIDITY_SWEEP.
- Sparse event detection retained 3589 of 16150 directional rows (22.22%).
- The most common primary event was BREAKOUT_CONFIRMATION with 2449 rows.
- The pre-trade cost gate retained 0 event rows (0.00%).
- The fixed no-trade baseline has zero expectancy and zero drawdown; every tradable candidate must beat it after costs.
- Meta-label Holdout selected n=0, expectancy=0.000000% and PF=0.0.
- Walk-forward positive-fold fraction was 0.00%.
- Best adequately sampled non-meta Holdout baseline expectancy was -0.285950%.
- 1025 decisions triggered multiple events; pre-declared priority prevented double counting.
- No event/meta-label candidate is eligible for Fresh OOS freezing.

## Blockers
- Meta model was not fitted
- Meta-label model was not fitted: insufficient cost-gated train events
- Meta-label Holdout sample count is below the promotion minimum.
- Meta-label Holdout expectancy is not positive.
- Meta-label Holdout profit factor is below the promotion minimum.
- Meta-label Holdout confidence interval does not stay above zero.
- Meta-label walk-forward positive-fold fraction is insufficient.

## Warnings
- Event detectors use entry-time replay fields only; replay proxies are not equivalent to full order-book events.
- Triple-Barrier labels use future outcome fields only after the event universe is frozen.
