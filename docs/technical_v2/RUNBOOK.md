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

Version 2.1 additionally provides a professional audit chain:

1. `data_quality.py` checks candle cadence, duplicates, missing candles, robust outliers,
   freshness, OHLC geometry, and optional cross-source divergence.
2. `setup_engine.py` selects one regime-compatible setup: Trend Pullback, Breakout + Volume,
   Liquidity Sweep Reversal, Range Mean Reversion, Momentum Continuation, or Volatility Expansion.
3. `execution_simulator.py` estimates spread, volatility/liquidity slippage, latency, market impact,
   and partial fill.
4. `economics.py` calculates net expected value after fees, execution, funding, and rollover.
5. `triple_barrier.py` labels Target, Stop, or Time exits and treats ambiguous same-candle hits as
   Stop-first by default.
6. `segmented_calibration.py` calibrates by symbol, setup, regime, side, and entry timeframe, with
   a transparent global fallback.
7. `futures_microstructure.py` accepts Open Interest, Funding, taker imbalance, order-book
   imbalance, and liquidation imbalance only when a provider actually supplies them.
8. `portfolio_risk.py` reduces virtual size for same-side, correlated, concentrated, or excessive
   gross exposure.
9. `validation.py` creates purged/embargoed walk-forward splits and sequential OOS stability
   reports.
10. `promotion.py` can recommend Research → Shadow only. It never authorizes Live.

## Dashboard controls

Open the Control Center and select the validation/Paper section.

1. Choose the session style.
2. Set **Risk tolerance**. This changes paper admission and virtual exposure only.
3. Set **Technical analysis depth** independently. At full depth, live public mode requests
   1m for entry timing, 5m/15m for setup, and 1h/4h for regime context.
4. Choose `LIVE_PUBLIC` for current public data or `ACCELERATED_REPLAY` for a fast local lab.
5. Start Showcase.

The v2 report shows data quality, selected setup, detected regime, timeframe agreement,
cost-adjusted geometry, net EV, execution cost, portfolio status, calibration label, family scores,
drivers, warnings, session win rate, expectancy, attribution, walk-forward stability, and automatic
challenger blockers. Total session trades are unlimited; concurrent exposure remains bounded and
one open position per symbol prevents accidental duplicate positions.

## Session profit guard

Each Showcase worker run starts with a fresh virtual-equity baseline. The guard calculates:

```text
session return = (new realised PnL + current unrealised PnL) / virtual session equity
```

Default profit targets are risk-tier aware:

- Precision: 1.0%
- Cautious: 1.5%
- Active test: 2.0%
- Exploratory: 3.0%

The profit target becomes eligible after at least three trades close, preventing one lucky trade
from ending the observation session. The loss limit is immediate. When either boundary is touched,
the worker closes remaining Showcase positions using their last recorded marks, records
`PROFIT_TARGET_REACHED` or `LOSS_LIMIT_REACHED`, and stops without any live order or remote-price
wait. Targets, loss limits, and virtual equity can be adjusted in Advanced settings; zero disables
the corresponding boundary.

## Causality and data rules

- Live analysis drops the potentially forming last candle. Snapshot pricing may still use the
  latest public observation.
- Replay uses only rows at or before its current cursor. Optional daily context is cut at the same
  timestamp.
- At least 40 valid OHLC candles are required.
- All OHLC values must be numeric, close must be positive, and high cannot be below low.
- Missing or insufficient data fails closed for that symbol and is reported in the scan errors.
- A failed quality gate, rejected setup, non-positive net EV, or blocked portfolio exposure cannot
  open a Showcase trade.

## Optional enriched Futures contract

An enriched provider can attach a `microstructure` mapping to `DataFrame.attrs` or provide these
columns directly:

- `open_interest_change_pct`
- `price_change_pct`
- `funding_rate_pct`
- `taker_buy_ratio` (0 to 1)
- `order_book_imbalance` (-1 to 1)
- `liquidation_imbalance` (-1 to 1)

If none are present, the family is marked `UNAVAILABLE` and stays neutral. Values are never
invented from OHLCV.

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
.\.venv\Scripts\python.exe -m pytest tests\test_technical_v2.py tests\test_technical_v2_professional.py tests\test_showcase_paper.py -q
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
