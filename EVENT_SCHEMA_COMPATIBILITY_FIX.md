# Event Opportunity v2 — Production Replay Schema Compatibility Fix

## Root cause
The production replay stores component scores (`trend_score`, `momentum_score`, `volume_score`, `structure_score`), regime/side scores and `execution_volatility_multiplier`, but does not persist raw OHLC, ATR, RSI or explicit breakout/sweep flags. The original detector therefore produced zero events.

## Fix
- Adds `execution_volatility_multiplier` as the volatility proxy.
- Uses causal rolling quantiles per symbol/timeframe for breakout, volatility expansion, mean-reversion and regime-transition proxies.
- Supports direction alignment through both regime labels and long/short score dominance.
- Keeps liquidity sweep unavailable unless an explicit entry-time sweep flag exists; it is never inferred from component scores.
- Adds raw pre-priority family counts and schema mode diagnostics to reports.
- Adds regression tests matching the real Market Replay schema.

## Safety
No future return, target/stop outcome, MFE, MAE or aggregate outcome label is used to create events. No runtime, Paper or Live policy is changed.
