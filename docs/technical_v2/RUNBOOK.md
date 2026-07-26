# Technical Engine v2 — Research Challenger Runbook

## Purpose and safety boundary

Technical Engine v2 is a sidecar research engine for causal technical analysis. It is used by
Showcase Paper to make short observation sessions more informative. It does **not** modify or
replace the Decision Engine, Market Replay, Backtest, or `decision_evaluator.py`. It cannot place
live orders, cannot use real capital, and its records are not official Go-live evidence.

The only connection is `freakto/research/adapters/technical_v2_adapter.py`. Removing that adapter
returns Showcase to a disconnected state without changing the protected core.

## Architecture

The package `freakto/technical_v2/` contains:

- continuous, bounded evidence rather than binary indicator voting;
- indicator families (`trend`, `momentum`, `mean_reversion`, `structure`, `volume`, `volatility`)
  so correlated indicators do not receive independent full votes;
- closed-candle multi-timeframe alignment;
- trend/range and volatility-regime classification;
- break-of-structure, range boundaries, and liquidity-sweep detection;
- relative volume, volume z-score, OBV direction, and rolling VWAP location;
- regime-aware weighted family aggregation;
- ATR-based stop, invalidation, target, expiry, and cost-adjusted reward/risk;
- an independent paper-risk overlay with virtual size scaling and exposure dilution;
- calibration status, Brier score, expected calibration error, outcome attribution, and
  champion/challenger comparison;
- JSON and Markdown decision explanations.

## Dashboard controls

Open the Control Center and select the validation/Paper section.

1. Choose the session style.
2. Set **Risk tolerance**. This changes paper admission and virtual exposure only.
3. Set **Technical analysis depth** independently. At full depth, live public mode requests
   5m, 15m, 1h, and 4h closed-candle frames.
4. Choose `LIVE_PUBLIC` for current public data or `ACCELERATED_REPLAY` for a fast local lab.
5. Start Showcase.

The v2 report shows the detected regime, timeframe agreement, cost-adjusted geometry,
calibration label, family scores, drivers, warnings, session win rate, expectancy, and family
attribution. Total session trades are unlimited; concurrent exposure remains bounded and one open
position per symbol prevents accidental duplicate positions.

## Causality and data rules

- Live analysis drops the potentially forming last candle. Snapshot pricing may still use the
  latest public observation.
- Replay uses only rows at or before its current cursor. Optional daily context is cut at the same
  timestamp.
- At least 40 valid OHLC candles are required.
- All OHLC values must be numeric, close must be positive, and high cannot be below low.
- Missing or insufficient data fails closed for that symbol and is reported in the scan errors.

## Calibration and promotion

Every new model begins as `UNCALIBRATED`. A minimum of 50 labelled outcomes is required before a
calibration status can become `CALIBRATED`; sufficient samples with poor reliability become
`NEEDS_REVIEW`. This label is a diagnostic, never a promise of profitability.

Promotion order is mandatory:

1. Research replay and leakage audit
2. Shadow observation
3. Forward observation across market regimes
4. Official Paper only after its independent gates pass
5. Live only after explicit owner approval and the existing Go-live policy

Showcase trades must never be copied into official evidence to bypass those gates.

## Verification

Run focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_technical_v2.py tests\test_showcase_paper.py -q
```

Run the full suite before promotion or release:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Key failure states are visible in the dashboard and `logs/showcase_paper/session.json`. Worker
process state is stored under `.freakto-runtime/showcase-paper/`.

## Rollback

Stop Showcase from the dashboard before changing versions. Because v2 is a sidecar, rollback is
the single commit that added `freakto/technical_v2/`, its adapter, and the Showcase connection.
No protected-core database or engine migration is involved.
