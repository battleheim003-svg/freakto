# Fresh OOS Replay & Feature Store v2 — Initial Real Result

The completed pipeline was executed against the currently available cumulative Replay dataset.

## Development freeze

```text
Source replay rows      : 78,452
Selected development run: market_replay_20260711_192507
Frozen rows             : 38,670
Frozen directional rows : 14,174
Symbols                 : BNB, BTC, DOGE, ETH, SOL, XRP / USDT
Timeframe               : 4h
Provider                : kucoin
Global known-data cutoff: 2026-07-09T12:00:00+00:00
Development dataset ID  : 820f6692ae099be37832
```

The selected run is preserved in a compressed snapshot. The cutoff is calculated from every timestamp already present in the cumulative source, so an older run with a later market candle cannot leak into the Fresh OOS set.

## Initial Fresh OOS state

```text
Status                 : READY_AWAITING_FRESH_DATA
Fresh rows             : 0
Fresh directional rows : 0
Feature rows           : 0
Outcome path rows      : 0
Promotion applied      : False
Paper/Live enabled     : False
```

This is the expected result, not a software failure. The current source file cannot contain rows strictly after its own global maximum timestamp. A genuine OOS result requires newly collected historical candles or forward-shadow decisions after the cutoff.

## What is now enforced

1. The old dataset is frozen with SHA-256 hashes and an immutable compressed snapshot.
2. Fresh decisions must start at least one full timeframe after the global Development cutoff.
3. The fixed benchmark remains `score >= 70`; Fresh OOS cannot select a different threshold.
4. Entry-time features and future outcomes are written to separate compressed tables.
5. Outcome paths include the execution candle and every subsequent OHLCV candle up to the configured horizon.
6. Stop/Target touches are evaluated candle by candle. When both occur in one candle, the row is marked ambiguous and recorded conservatively as Stop-first.
7. Recorded fee/slippage values have priority; custom exchange/symbol profiles and conservative fallbacks preserve cost provenance.
8. Missing symbols, timeframes, historical paths, duplicates, overlap or leakage block completion.
9. No result automatically activates Paper or Live trading.

## Validation

```text
New tests               : 12 passed
Reconstructed test suite: 89 passed
Python compileall       : passed
```

On the user's current 99-test project, these 12 new tests should bring the total to 111 tests.
