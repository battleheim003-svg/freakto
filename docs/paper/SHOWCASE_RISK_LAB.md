# Showcase Paper Risk Lab

This dashboard area is an isolated visual test harness. It never writes to the
official Paper ledger, Forward evidence, or Go-live evidence, and it always
forces real-capital and live-order flags off.

## Session styles

- **Precision** uses risk tolerance `0`, strict score/confidence admission, a
  small position cap, and the live public-data path.
- **Balanced** accepts qualified watchlist observations and scans once per
  minute.
- **Rapid test** uses risk tolerance `100`, scans every 15 seconds, holds for at
  most five minutes, and advances through cached OHLCV locally. This produces
  observable Open/Close lifecycles without pretending cached data is live.

Risk tolerance changes only the Showcase admission wrapper. Increasing it also
increases technical-analysis depth from a focused 3-tool vote to a full
12-tool confluence stack: EMA trend pairs, price momentum, RSI, MACD,
Bollinger position, ROC, Stochastic, volume confirmation, 20-bar breakout,
candle structure, and ATR regime. Every simulated trade stores the indicator
votes and resulting confluence percentage. It does not mutate Decision Engine
thresholds or weights.

The same confluence engine is used in both modes. `LIVE_PUBLIC` evaluates the
latest fully closed public `5m` candles without credentials; `ACCELERATED_REPLAY`
advances causally through the local archive when public providers are blocked
or when a fast repeatable UI test is preferred.

Session trade count is unlimited (`daily_trade_limit=0`). A symbol may re-enter
after its previous position closes and the selected policy cooldown expires;
active-test and exploratory levels use no re-entry cooldown. The engine still
prevents duplicate simultaneous positions for the same symbol and cannot open
more simultaneous positions than the configured symbol universe. Those are
correctness/resource guards, not a session trade quota.

Every image card records its source mode and risk level and is marked
`NOT GO-LIVE EVIDENCE`.

## Cloud versus local execution

The existing `Freakto Paper Cloud Cycle` GitHub Action is the correct cloud
path for canonical one-shot evidence collection. It runs six times per day and
persists state on the dedicated `paper-state` branch. It is intentionally not
an always-running Showcase service.

Use the local detached worker for rapid interactive sessions. A future
always-on visual service should use a persistent VPS/container with durable
storage and health monitoring, not a long-running GitHub-hosted runner.
