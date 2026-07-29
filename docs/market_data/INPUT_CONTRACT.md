# Freakto Market-Data Input Contract

Status: phase-0 audit, schema version `ohlcv-v1`  
Scope: new provider and asset-class adapters only  
Core changes: none

## Canonical row

Every adapter must emit one chronological dataset per symbol and timeframe with
these required columns:

| Column | Contract |
| --- | --- |
| `timestamp` | UTC bar-open time; epoch milliseconds or a UTC-parseable value |
| `open` | finite number greater than zero |
| `high` | finite number greater than zero and not below OHLC values |
| `low` | finite number greater than zero and not above OHLC values |
| `close` | finite number greater than zero |
| `volume` | finite number greater than or equal to zero |

`provider` is optional provenance metadata. New adapters may retain more
metadata outside the replay CSV, but must not add it as an implicit model
feature.

## Time semantics

- Timestamps identify the beginning of a candle, never its close.
- Timestamps are aligned to UTC timeframe boundaries.
- Only fully closed candles may cross into replay or decision evaluation.
- Rows are strictly chronological and unique by timestamp.
- A missing market session remains a gap. Adapters must not forward-fill prices,
  manufacture zero-range candles, or pretend that FX and gold trade 24/7.
- Session calendars, DST, holidays, and early closes belong to asset-specific
  metadata. They are used to explain expected gaps, not rewrite timestamps.

## Price and volume semantics

- Forex/gold adapters must declare whether prices are `bid`, `ask`, `mid`, or
  `last`. Mixing bases inside one dataset is forbidden.
- OHLC must use the same price basis throughout a dataset.
- FX tick volume is not exchange trade volume. If real volume is unavailable,
  the adapter must label the chosen proxy in its manifest.
- Negative volume is invalid. Zero volume is accepted with a warning and a
  declared meaning.
- Symbol identifiers are canonical `BASE/QUOTE` values such as `EUR/USD` and
  `XAU/USD`; provider-specific codes remain adapter details.

## Dataset invariants

- A single provider and price basis are used per symbol/timeframe dataset.
- Numeric coercion, duplicate removal, resampling, and timezone conversion must
  be explicit in the adapter report; no silent repair is allowed.
- Adapter output includes a schema version, provider, source symbol, fetch time,
  price basis, volume semantics, timezone source, and deterministic data hash.
- Credentials are read from environment variables and never written to reports,
  manifests, logs, fixtures, or commits.

## Execution boundary

OHLCV compatibility does not imply execution compatibility. Spread, bid/ask
fills, slippage, rollover, account-currency conversion, leverage, margin,
contract size, and trading-session rules are separate asset-class contracts.
Until those contracts pass their own audit, new markets remain research-only
and must not enter Paper or Live workflows.

## Fail-closed validation

Use `freakto.market_data.inspect_ohlcv(frame, timeframe)` before an adapter
persists replay input. Any `ERROR` blocks the dataset. `WARNING` requires
provenance in the adapter manifest. The validator is read-only: it neither
sorts, fills, removes, nor rewrites input rows.

## Existing implementation findings

The v10.3 historical store normalizes the six required columns, converts
timestamps to UTC, sorts and de-duplicates rows, and persists an optional
`provider` field. Replay again parses UTC timestamps and expects valid OHLCV.
Feature computation consumes price and volume directly. Consequently, adapter
validation must occur before persistence so legacy normalization cannot hide a
provider defect.
