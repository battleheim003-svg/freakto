# Showcase Paper Risk Lab

This dashboard area is an isolated visual test harness. It never writes to the
official Paper ledger, Forward evidence, or Go-live evidence, and it always
forces real-capital and live-order flags off.

## Session styles

- **Precision** uses risk tolerance `0`, strict score/confidence admission, a
  small position cap, and the live public-data path.
- **Balanced** accepts qualified watchlist observations and scans once per
  minute.
- **Rapid test** uses risk tolerance `70`, scans every 15 seconds, holds for at
  most five minutes, and advances through cached OHLCV locally. This produces
  observable Open/Close lifecycles without pretending cached data is live.

Risk tolerance changes only the Showcase admission wrapper: minimum score,
minimum confidence, accepted recommendation classes, maximum simultaneous
positions, virtual notional, stop/target geometry, and re-entry cooldown. It
does not mutate Decision Engine thresholds or weights.

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
