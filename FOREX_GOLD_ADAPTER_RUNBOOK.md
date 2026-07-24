# Forex and Gold Adapter Runbook

Status: research-only foundation
Paper: disabled
Live: disabled
Legacy engine changes: none

## Purpose

The adapter fetches Twelve Data `time_series` records, converts provider fields
to Freakto `ohlcv-v1`, validates closed UTC candles, and can persist a brand-new
dataset in the existing replay directory layout. It never overwrites an existing
dataset.

Official provider references:

- `https://twelvedata.com/docs/volume-indicators`
- `https://twelvedata.com/forex`
- `https://twelvedata.com/commodities`

## Safety gates

1. Config must remain `research_only=true`.
2. Paper and Live flags must remain false.
3. Execution cost status remains `UNVERIFIED`.
4. Missing provider volume is blocked; the adapter does not fabricate it.
5. Only fully closed, UTC-aligned candles pass.
6. Existing replay files are never overwritten by the adapter.
7. API keys are accepted at runtime only and never placed in output manifests.

## Current compatibility status

Data-schema compatibility is implemented and unit-tested. Provider history,
session/DST behavior, volume availability, spreads, rollover, slippage,
contract sizing, and account-currency conversion still require empirical audits
before any Forward, Shadow, or Paper gate.

Once a validated dataset exists, the unchanged replay command can read its
normal cache path:

```text
freakto replay run --symbols EUR/USD --timeframe 4h --fee-bps <audited> --slippage-bps <audited>
```

Do not run this as evidence until the cost fields have audited sources and the
dataset manifest passes review.
