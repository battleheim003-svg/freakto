# Technical Engine v2.1 Validation Protocol

## Objective

Determine whether the v2.1 challenger has positive cost-adjusted expectancy that is stable across
time, symbols, directions, setups, and regimes. Fast Showcase results are diagnostic only.

## Dataset contract

- Signals use closed candles only.
- The 1m frame times entry; 5m/15m define setup; 1h/4h define context.
- All higher-timeframe rows must be available at or before the decision timestamp.
- Outcomes use Target, Stop, or Time barriers. When both price barriers appear inside one OHLC
  candle, the default label is Stop.
- Fees, spread, slippage, latency, partial fill, funding, and rollover must be recorded separately.

## Required validation

1. Build chronological walk-forward folds.
2. Purge observations between training and test windows.
3. Apply an embargo after each test window.
4. Freeze thresholds before reading each OOS result.
5. Report results per setup, regime, symbol, side, and timeframe.
6. Compare against the current champion, Buy-and-Hold where meaningful, and a frequency-matched
   random-entry baseline.
7. Retain negative and ambiguous results; never delete unfavourable folds.

## Research-to-Shadow minimums

The automated recommendation requires at least 200 closed challenger samples, passed walk-forward
stability, improved expectancy, and no drawdown regression. These are minimum software gates, not
proof of profitability. Statistical power and regime coverage can require substantially more data.

The only automated positive outcome is `PROMOTE_TO_SHADOW`. Paper and Live remain governed by the
existing independent gates and explicit owner approval.

## Failure interpretation

- `DATA_QUALITY_REJECTED`: repair data before inspecting strategy performance.
- `NO_VALID_SETUP`: the market does not match a supported setup.
- `NON_POSITIVE_EXPECTED_VALUE`: costs consume the forecast edge.
- `PORTFOLIO_RISK_BLOCK`: the individual trade may be valid but aggregate exposure is not.
- `UNCALIBRATED`: the applicable segment and global fallback have insufficient outcomes.
- `WALK_FORWARD_NOT_PASSED`: performance is not sufficiently stable out of sample.
