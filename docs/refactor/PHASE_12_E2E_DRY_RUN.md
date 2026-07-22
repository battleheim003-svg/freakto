# Phase 12 controlled end-to-end dry run

## Outcome

A real full Control Center Quick Start completed on 2026-07-22 as job
`quick-20260722-155513-1c84cf`. The detached Windows worker executed all eleven
ordered steps. Ten commands exited 0; the final Go-live check exited 2 and was
accepted as the required fail-closed review result.

## Environment and provider evidence

- KuCoin historical-data build completed for BTC, ETH, SOL, BNB, XRP, and DOGE.
- All 6/6 datasets are `REPLAY_READY`, with 39,729 source rows, 100% reported
  coverage, and zero gaps.
- Full Replay completed with 156,146 rows and passed the no-lookahead leakage
  audit.
- Paper preflight returned `READY_FOR_RESEARCH_PAPER_COLLECTION` with no
  operational blockers.
- Research Paper arming and one real Paper cycle completed.
- Paper state remained `RESEARCH`; live orders and real capital were false and
  allocation remained 0.0%.
- Paper, Forward, and Go-live reports were generated successfully.

The run exposed a Pandas mixed-type inference warning in Replay status loading.
Both Replay CSV readers now use `low_memory=False`; a strict DtypeWarning probe
and replay regression tests verify the fix.

## Research blockers preserved

Operational success is not strategy promotion. The broad Replay remains
`REPLAY_RESEARCH_NOT_VALIDATED`: TEST average net return was -0.804858% and TEST
profit factor was 0.598. The deterministic event/cost-gated development policy
passed its development checks, but Fresh OOS still had 0/300 directional rows
and 0/50 fixed-gate samples. Paper performance contained zero closed trades.

Forward status is `FORWARD_TEST_COLLECTING` with readiness 28/100, 34/100
complete evaluations, 0 closed Paper trades, and 1/30 elapsed Forward days.
These are evidence-collection requirements, not software defects, and were not
bypassed or weakened.

## Repeatable verification

`scripts/verify_e2e_job.py` validates the latest job or a supplied `--job-id`.
It requires exact step order, accepted exits, success status, review-only
Go-live semantics, and explicit zero-capital safety evidence. An optional
`--output` writes a runtime manifest.

```text
python scripts/verify_e2e_job.py --job-id quick-20260722-155513-1c84cf
```

The final repository regression run passed all 385 tests, and 755 canonical
text files passed strict UTF-8 validation.

## Rollback

Generated data, reports, job history, and Paper state are runtime artifacts and
remain outside Git. Use `freakto paper disarm` to stop Research Paper collection.
The Replay CSV inference fix can be reverted independently; it changes loading
strategy only, not data values, strategy logic, or safety policy.
