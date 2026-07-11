# Freakto v10.3.0

- Added explicit feature/model/calibration/execution/split version contracts.
- Added a SQLite Experiment Registry and atomic one-shot hold-out claims.
- Separated score calibration from DecisionEngine state.
- Added closed-candle filtering and next-bar-open replay execution.
- Added volatility/liquidity-aware costs and regime-adaptive outcome horizons.
- Added FDR-adjusted feature attribution and detailed segment counts.
- Reworked walk-forward validation to expanding folds with threshold refits and
  an untouched final hold-out.
- Added chronological two-stage meta-label validation.
- Added fail-closed paper-trade preflight and net-of-cost R evaluation.
- Made replay checkpoints atomic and Windows console output encoding-safe.
- Added research-safety regression tests.

Validated locally with 17 passing unit tests and a six-symbol 38,670-row replay.
The current score remains miscalibrated and has no validated edge; this finding
is intentionally preserved instead of being optimized away.
