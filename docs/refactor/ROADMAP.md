# Freakto consolidation roadmap

This document is the canonical sequence for the repository consolidation work.
The order is deliberate: later phases must preserve the safety and compatibility
contracts established by earlier phases.

## Phase 1 — Stabilize the current worktree

Status: **complete (2026-07-22)**

- Record the exact Git baseline and classify pre-existing local changes.
- Preserve user-owned source changes without stashing, resetting, staging, or
  overwriting them.
- Separate source changes, runtime state, generated evidence, and local assets
  conceptually before any refactor begins.
- Establish verification results and explicit preservation rules.

Evidence and rules: `docs/refactor/WORKTREE_BASELINE.md`.

## Phase 2 — Standardize project tooling

Status: **complete (2026-07-22)**

- Add `pyproject.toml` as the canonical project and tool configuration.
- Configure linting, formatting, targeted type checking, and test markers.
- Separate runtime and development dependencies while preserving the existing
  Windows installation path.

Implemented by `pyproject.toml`, `requirements-dev.txt`, the headless test
bootstrap in `tests/conftest.py`, and the quality gates in Freakto CI.

## Phase 3 — Establish one canonical CLI

Status: **complete (2026-07-22)**

- Define stable `freakto data`, `replay`, `paper`, and `report` commands.
- Keep compatibility wrappers for existing batch files and dashboards.
- Document exit codes, safety invariants, and supported execution paths.

Implemented by `freakto/cli.py`, `docs/refactor/PHASE_3_CLI.md`, CLI contract
tests, and compatibility updates to the relevant Windows launchers.

## Phase 4 — Separate the architecture

Status: **complete (2026-07-22)**

- Organize responsibilities into `core`, `research`, `paper`, `providers`, and
  `ui` boundaries.
- Remove circular and root-script dependencies incrementally.
- Preserve replay causality and fail-closed paper/live safety contracts.

Implemented by the five packages under `freakto/`, composition-root cleanup,
and executable dependency-direction tests documented in
`docs/refactor/PHASE_4_ARCHITECTURE.md`.

## Phase 5 — Migrate scripts incrementally

Status: **complete (2026-07-22)**

- Move orchestration out of presentation modules.
- Convert legacy root entry points into thin compatibility wrappers.
- Verify behavior after every migration slice.

Eight operational entry points were migrated to packaged modules with thin root
wrappers. The manifest and compatibility rules are recorded in
`docs/refactor/PHASE_5_MIGRATION.md`.

## Phase 6 — Separate artifacts and persistent state

Status: **complete (2026-07-22)**

- Define which datasets are fixtures, reproducible research inputs, generated
  outputs, and mutable runtime state.
- Move mutable state away from the source branch and provide migration tools.
- Keep only small, intentional fixtures in Git.

Implemented through the runtime storage contract, dry-run-first migration tool,
Git tracking policy, and artifact classification documented in
`docs/refactor/PHASE_6_RUNTIME_STORAGE.md`.

## Phase 7 — Harden CI

Status: **complete (2026-07-22)**

- Split fast unit, integration, slow, network, replay, and paper suites.
- Replace blanket error suppression with explicit required/optional policies.
- Report degraded components while failing closed for safety-critical checks.

Implemented by the split CI matrix, explicit component-policy runner, advisory
profiles, and fail-closed cloud-state restoration documented in
`docs/refactor/PHASE_7_CI.md`.

## Phase 8 — Normalize encoding and documentation

Status: **complete (2026-07-22)**

- Standardize UTF-8 and line-ending behavior across Windows and Linux.
- Consolidate runbooks around canonical commands.
- Archive superseded release and implementation notes without losing history.

Implemented by repository text contracts, strict encoding validation, canonical
documentation indexes, and the historical archive described in
`docs/refactor/PHASE_8_ENCODING_DOCS.md`.

## Phase 9 — Run regression and migration verification

Status: **complete (2026-07-22)**

- Run the complete test matrix and compare canonical outputs against baselines.
- Validate clean installation, Windows workflows, and GitHub Actions workflows.
- Resolve regressions before removing compatibility paths.

Completed with the 335-test baseline passing across the fast/slow partition,
independent Paper and Replay shards, an isolated wheel install,
canonical/legacy callable parity, Windows launcher checks, and parsed GitHub
Actions workflows. The expanded final suite passed all 349 tests. Evidence, the
resolved package-version regression, and rollback rules are recorded in
`docs/refactor/PHASE_9_VERIFICATION.md`.

## Phase 10 — Formalize paper readiness and go-live criteria

Status: **complete (2026-07-22)**

- Freeze strategy/data contracts for the evaluation window.
- Define minimum sample size, after-cost expectancy, drawdown, regime stability,
  operational reliability, and kill-switch requirements.
- Keep real-capital execution disabled until every approved gate is satisfied.

Implemented as the frozen `paper-go-live-v1` contract and the fail-closed
`freakto paper go-live-check` evidence evaluator. The thresholds, operational
procedure, tests, and rollback rules are recorded in
`docs/refactor/PHASE_10_GO_LIVE.md`. Passing only permits manual review; live
activation remains unimplemented and zero-capital invariants remain enforced.

## Phase 11 — Background jobs and observability

Status: **complete (2026-07-22)**

- Run Quick Start outside the Streamlit request lifecycle.
- Persist progress, history, step results, and logs atomically.
- Provide cooperative cancellation, retry, concurrency protection, and worker
  interruption detection.
- Keep every background command zero-capital and fail-closed.

Implemented by the Control Center job manager, detached worker, bilingual Jobs
page, runtime audit trail, and verification documented in
`docs/refactor/PHASE_11_OPERATIONS.md`.

## Phase 12 — Controlled end-to-end operational dry run

Status: **complete (2026-07-22)**

- Execute the full background Quick Start against real local data and providers.
- Distinguish operational defects from intentional research/readiness blockers.
- Resolve reproducible environment/provider regressions without weakening gates.
- Persist repeatable machine-verifiable evidence.

All eleven steps completed under job `quick-20260722-155513-1c84cf`; details,
metrics, the Replay CSV warning fix, and rollback procedure are recorded in
`docs/refactor/PHASE_12_E2E_DRY_RUN.md`.

## Phase 13 — Frozen Paper evidence campaign

Status: **active (started 2026-07-22)**

- Freeze the approved Paper contract and record its SHA-256 identity.
- Persist campaign progress and reconcile it with the live worker heartbeat.
- Run the zero-capital orchestrator through a restart-safe Windows task.
- Require both 60 real elapsed days and at least 200 closed Paper trades.

Campaign `paper-20260722-161631` is running with its earliest time threshold at
`2026-09-20T16:16:31.350645+00:00`. Implementation, recovery, verification, and
rollback details are recorded in `docs/refactor/PHASE_13_PAPER_CAMPAIGN.md`.

## Remaining delivery phases

- Phase 13: collect 60 real days and at least 200 closed Paper trades.
- Phase 14: automate evidence aggregation and independent review packaging.
- Phase 15: build a signed, one-click Windows installation and recovery bundle.

## Change-control rule

Only one phase is active at a time. A phase is complete only when its changes,
tests, migration notes, and rollback path are recorded. Pre-existing user work
listed in the phase-1 baseline must never be overwritten or silently absorbed.
