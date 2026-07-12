# Historical Data Cache Freshness Fix

## Problem

The historical builder previously reused a cached multi-year dataset whenever its overall coverage percentage was above the configured threshold. A dataset could therefore remain several recent candles stale while still reporting about 99.8% coverage.

This prevented `market_replay_dashboard.py --full` from fetching new candles, so Fresh OOS replay received no post-cutoff outcomes.

## Fix

- Cache reuse now requires both acceptable coverage and a recent tail.
- At most one timeframe candle of lag is tolerated for the currently forming exchange candle.
- Stale caches are refreshed incrementally from one candle before the cached tail.
- The cached provider is tried first to avoid silently mixing exchange microstructure.
- Existing data is de-duplicated after the overlapping incremental fetch.

## Verification

```bat
python -m pytest
python -X utf8 market_replay_dashboard.py --full --symbols BTC/USDT,ETH/USDT,SOL/USDT --timeframe 4h --years 3 --step 1
python -X utf8 fresh_oos_replay_analysis.py --run-replay --symbols BTC/USDT,ETH/USDT,SOL/USDT --timeframes 4h --data-dir data/market_replay
```

After the first command, the historical dataset row count or `actual_end_utc` should advance when KuCoin has newer completed candles. Fresh OOS can still remain in `READY_AWAITING_FRESH_DATA` until enough future candles exist to complete its longest pre-registered outcome horizon.
