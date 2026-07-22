# Phase 7 CI hardening

Phase 7 separates feedback by risk and removes blanket error suppression from
all GitHub workflows.

## Pull-request CI

`freakto-ci.yml` now has independent jobs:

| Job | Scope | Failure policy |
|---|---|---|
| Quality and architecture | Ruff, Mypy, compile, architecture/storage/CLI contracts, secret scan | required |
| Tests (fast) | `not slow` — currently 310 tests | required |
| Tests (slow) | `slow` — currently 15 tests | required |
| Safety contract (paper) | `paper and not slow` — currently 73 tests | required |
| Safety contract (replay) | `replay and not slow` — currently 21 tests | required |

Matrix jobs use `fail-fast: false`, so one failure does not hide results from
the other suites. Safety jobs intentionally duplicate a focused subset to make
Paper and replay causality regressions visible by name.

The quality job parses all workflow YAML files with pinned PyYAML before tests.

## Operational component policy

`scripts/ci_component_runner.py` executes each component without a shell and
requires an explicit policy:

- `required`: non-zero child exit propagates and fails the step;
- `optional`: non-zero child exit returns success to permit artifact upload but
  records `DEGRADED`, the original exit code, command, timestamps, and output
  tails.

Every result is appended atomically to `logs/ci/component-results.json`, added
to the GitHub Step Summary, and emitted as a workflow warning/error annotation.
Optional therefore means advisory, not invisible.

`scripts/ci_advisory_suite.py` defines two reviewed profiles with 14 uniquely
named diagnostics:

- `forward`: collectors may update forward research observations;
- `health`: event fetch is disabled and regime labeling is dry-run.

## Required workflow behavior

- The core Forward cycle uses `--stop-on-error`; required task failures stop the
  cycle.
- Explicit validation and downstream research diagnostics are optional but
  visible through component reports.
- Scheduled/manual Forward status remains required.
- Paper Cloud restore fails if a `paper-state` branch exists without a valid,
  non-empty `cloud_state.tar.gz`; it cannot silently replace lost state with an
  empty run.
- Artifact upload remains `if: always()` so failure evidence is retained.

## Suppression audit

All workflow occurrences of shell `|| true` and the Forward
`--continue-on-error` flag were removed. Recovery branches now use explicit
conditions and required checks.

## Verification

Unit tests cover required exit propagation, optional degradation, atomic report
append, GitHub summary visibility, and the Forward/Health profile differences.
An actual optional probe exiting `7` produced `DEGRADED`, retained exit code 7,
and returned zero only because its policy was explicitly optional.
