# Airdrop Outcome Tracker Runbook

Status: research-only
Wallet automation: disabled
Claim automation: disabled
Core engine changes: none

## Model

The tracker stores immutable prediction snapshots separately from append-only
outcome observations. It evaluates the first known prediction for each project
against the latest observation, reducing leakage from rescoring after a listing
or claim becomes known.

`PENDING` and projects without observations are right-censored. They are never
counted as failures. Resolved observations are `CLAIMED`, `LISTED`,
`NO_AIRDROP`, `EXPIRED`, or `RUG`, and require an explicit eligibility value
and auditable `source_ref`.

## Sync current radar predictions

```text
python -X utf8 airdrop_backtest_dashboard.py sync
```

The sync is idempotent and does not modify `airdrop_radar.db`.
If that source database does not exist, sync returns `SYNC_BLOCKED` with
`AIRDROP_RADAR_DATABASE_NOT_FOUND`; it does not emit a traceback or create
fabricated predictions.

## Record an observation

Use the immutable project identity shown in the radar database. A manual source
reference is allowed when it identifies durable evidence, for example an
internal claim receipt or dated research note.

```text
python -X utf8 airdrop_backtest_dashboard.py record --identity <id> --status CLAIMED --eligible yes --claimed yes --gross-reward-usd 125 --cost-usd 8 --source-ref <evidence>
```

## Report

```text
python -X utf8 airdrop_backtest_dashboard.py report --min-resolved 30
```

`RESEARCH_CANDIDATE` means evidence is incomplete. `PASSED` only means the
configured minimum resolved sample and observation requirements were met; it
does not mean the strategy is profitable, safe, or ready for automated action.

## Current evidence snapshot

The 2026-07-24 local audit found no `history/airdrop_radar.db`, therefore no
prediction snapshots or resolved outcomes could be imported. The outcome
report correctly remains `RESEARCH_CANDIDATE` with
`NO_PREDICTION_SNAPSHOTS`. The legacy shadow example is only a placeholder and
was not accepted as real outcome evidence.
