# ADR-001: Decision and Outcome Ledger v2

## Decision

Use `.freakto-runtime/evidence-v2/evidence.sqlite3` as the canonical source for
new Forward/Paper evidence. A decision is immutable and keyed by
`decision_id`; an outcome is a single terminal upsert for that decision.

## Invariants

- Decisions contain schema version, source/feature/code hashes and a positive entry price.
- `NEUTRAL` is an abstention and never receives economic return metrics.
- The evaluator enters at next-bar open, limits its horizon, resolves same-bar
  target/stop ambiguity as stop-first, and stores net-of-cost returns.
- Invalid legacy rows are quarantined with their original payload hash; no CSV
  is silently repaired or overwritten.
- All promotion/readiness views consume only unique, directional, terminal v2 rows.

## Migration

1. Create `freakto paper campaign-snapshot` before importing any legacy file.
2. Run `freakto evidence migrate-decisions path/to/decisions.csv`.
3. Investigate the quarantine table; do not force-import rejected rows.
4. Begin v2 collection in dual-write mode. Legacy evidence remains
   `INVALIDATED_DATA_CONTRACT` and cannot advance readiness.

## Consequences

The current campaign continues as an operational observation, but its old CSV
claims cannot be used for promotion. New clean evidence must accumulate over
time; the ledger cannot manufacture the 30/60-day windows.
