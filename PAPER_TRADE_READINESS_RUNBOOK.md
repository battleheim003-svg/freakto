# Paper-trade readiness protocol (v10.3)

> Canonical command surface: `freakto paper ...`. See
> [`docs/OPERATIONS.md`](docs/OPERATIONS.md). This runbook defines the deeper
> readiness protocol and does not replace the fail-closed CLI contract.

This release makes the paper-trade path fail closed. "Ready" means the system
is safe to collect forward observations; it does not mean that the strategy has
a positive edge or is approved for live trading.

## Architecture contract

Every decision and replay row persists `feature_set_version`, `model_version`,
`calibration_version`, `execution_model_version`, and
`split_protocol_version`. Runs are stored in
`logs/experiments/experiment_registry.sqlite3` with the data range, dataset
fingerprint, hyperparameters and terminal result. Calibration is separate from
DecisionEngine and cannot mutate score weights.

## Required workflow

1. Build or refresh closed-candle historical data.
2. Run strict replay:
   `python market_replay_dashboard.py --replay --symbols BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT,XRP/USDT,DOGE/USDT --compact`
3. Run score calibration once on the untouched TEST hold-out:
   `python replay_score_calibration_dashboard.py --compact`
4. Verify the gate: `python paper_trading_dashboard.py --preflight`
5. Start observation only when ready: `python paper_trading_dashboard.py --scan`
6. Evaluate observations: `python paper_trading_dashboard.py --evaluate`

A second calibration against the same dataset is blocked. Extend the data range
to create a genuinely new hold-out instead of reusing TEST.

## Safety guarantees

- The evolving current candle is removed before live feature computation.
- Replay features are audited by recomputing historical prefixes.
- Persisted learning and historical-edge inputs are disabled in replay.
- Decisions occur after bar close and fills use the next available bar open.
- Slippage increases with causal volatility and low liquidity, with a cap.
- An additional evaluation horizon adapts to regime.
- Same-candle stop/target ambiguity is accounted as stop-first.
- Paper evaluation reports net R after fee and estimated slippage.
- Meta-label threshold selection uses Validation; TEST is not used for tuning.
- Feature tests report Benjamini-Hochberg FDR-adjusted significance.

## Current validated run

- Replay run: `market_replay_20260711_192507`
- Complete rows: 38,670
- Directional rows: 14,174
- TEST directional rows: 3,074
- Leakage audit: passed on all six symbols
- TEST average net return: -0.660934%
- Calibration: `SCORE_INVERTED_OR_MISCALIBRATED`
- Robust shadow candidates: 0

The current hypothesis is not promoted. Paper mode is suitable only for
collecting honest forward evidence and validating operations.

## Formal go-live review gate

Phase 10 adds `freakto paper go-live-check`. Its frozen contract, numerical
thresholds, evidence format, kill-switch drills, and rollback rules are defined
in [`docs/refactor/PHASE_10_GO_LIVE.md`](docs/refactor/PHASE_10_GO_LIVE.md).
Passing that check does not authorize orders: live orders, real capital, and
allocation remain disabled and require a separate independently approved
implementation phase.
