# Forex and Gold Adapter Runbook

Status: research-only foundation
Paper: disabled
Live: disabled
Legacy engine changes: none

## Purpose

The default credential-free adapter downloads Dukascopy annual daily BID and
ASK candles, constructs MID OHLC, sums the two quote-volume fields, removes
explicit zero-volume placeholder days, validates closed UTC candles, and can
persist a brand-new dataset in the existing replay directory layout. It never
overwrites an existing dataset.

Official provider references:

- `https://www.dukascopy.com/swiss/english/marketwatch/historical/`
- `https://www.dukascopy.com/swiss/english/about/faq/?mob=0`

## Collection

Fetch an explicit UTC range without credentials. Omit `--persist` for a
read-only provider/contract audit.

```text
python -X utf8 market_adapter_dashboard.py forex --symbol EUR/USD --timeframe 1d --start 2023-01-01 --end 2026-01-01
```

Add `--persist` only after reviewing the contract result. Persistence creates a
new cache and adapter manifest and refuses to replace either file.

## Safety gates

1. Config must remain `research_only=true`.
2. Paper and Live flags must remain false.
3. Execution cost status remains `UNVERIFIED` until historical rollover is
   represented; observed spread and published commission are audited inputs,
   not permission to advance the gate.
4. Missing provider volume is blocked; the adapter does not fabricate it.
5. Only fully closed, UTC-aligned candles pass.
6. Existing replay files are never overwritten by the adapter.
7. API keys are accepted at runtime only and never placed in output manifests.

## Current compatibility status

The 2023-01-01 through 2025-12-31 BID/ASK archives were audited for EUR/USD and
XAU/USD. Every absent UTC daily row was represented by an explicit provider
zero-volume placeholder, and BID/ASK alignment had no unexplained gaps after a
bad cached download was rejected and reacquired.

Observed close-spread audit:

| Symbol | Rows | Placeholder days | Median spread | P95 spread | Suggested slippage/side |
| --- | ---: | ---: | ---: | ---: | ---: |
| EUR/USD | 939 | 157 | 0.3644 bps | 5.8273 bps | 3.6421 bps |
| XAU/USD | 934 | 162 | 1.7725 bps | 5.6955 bps | 3.5597 bps |

Suggested slippage is `1.25 × half of observed P95 full spread`. Published
worst-tier commissions are represented separately as 0.35 bps/side for FX and
0.525 bps/side for precious metals. The fee source is the provider's official
fee schedule:
`https://www.dukascopy.com/swiss/english/about/fee-schedule/`.

The compatibility audit still deliberately reports `RESEARCH_DATA_ONLY` with
`ROLLOVER_NOT_MODELED`. Daily positions can cross the provider's overnight
settlement, whose rates vary by instrument and date. No historical rollover
series was available in the downloaded candle archive, so the gate remains
fail-closed. Raw closed-session rows are removed only when the provider marks
them explicitly with zero volume; no gap is synthesized or filled.

Once a validated dataset exists, the unchanged replay command can read its
normal cache path:

```text
freakto replay run --symbols EUR/USD,XAU/USD --timeframe 1d --fee-bps 0.525 --slippage-bps 3.643
```

Do not run this as evidence until the cost fields have audited sources and the
dataset manifest passes review.

## Executed research evidence

The unchanged Replay engine was executed on both persisted datasets with the
more conservative shared inputs (`fee=0.525 bps/side`,
`slippage=3.643 bps/side`, fixed execution costs):

```text
freakto replay run --symbols EUR/USD,XAU/USD --timeframe 1d --start 2023-01-01 --end 2025-12-31 --fee-bps 0.525 --slippage-bps 3.643 --fixed-execution-costs
```

Run `market_replay_20260724_132330` completed 1,609 rows and passed the strict
no-lookahead audit. Test average net return was 0.186435% (profit factor
1.2617); Validation average net return was 0.212079% (profit factor 1.3477).
This is historical research evidence only.

The current Forward status is still `FORWARD_TEST_COLLECTING` with 1/30
observed days, 34/100 complete evaluations, and 0/30 closed Paper trades.
Consequently Shadow/Forward/Paper are not passed, and both Paper and Live flags
remain false.
