# Phase 3 canonical CLI contract

`freakto` is the stable operational entry point. Existing Python dashboards are
retained implementations and compatibility paths; new automation should call
the CLI contract below.

## Commands

```text
freakto data status [legacy data options]
freakto data build [legacy data options]

freakto replay status [legacy replay options]
freakto replay run [legacy replay options]
freakto replay full [legacy replay options]
freakto replay resume RUN_ID [legacy replay options]

freakto paper preflight
freakto paper arm-research
freakto paper arm-strategy
freakto paper cycle
freakto paper auto
freakto paper status
freakto paper dashboard
freakto paper disarm

freakto report paper [legacy report options]
freakto report research [legacy report options]
freakto report forward [legacy forward-status options]
```

Data/replay options are delegated to `market_replay_dashboard.py`. Report
options are delegated to the corresponding retained dashboard. Delegated
commands intentionally preserve unknown trailing options so the canonical CLI
does not lag every legacy research option. Internal Paper commands remain
strict and reject unknown arguments.

`report forward` is explicitly read-only and accepts only the optional `--send`
flag. Cycle/write options are rejected at the canonical boundary.

## Safety invariants

Every delegated child process receives all of the following, regardless of the
parent environment:

```text
LIVE_TRADING_ENABLED=false
REAL_CAPITAL_ENABLED=false
PYTHONUTF8=1
```

Paper JSON responses also report:

```json
{
  "live_orders_enabled": false,
  "real_capital_enabled": false,
  "allocation_pct": 0.0
}
```

The CLI contains no command for exchange order placement or real-capital
allocation. A parent process cannot opt a delegated command into either mode.

## Exit codes

- `0`: command completed successfully.
- `1`: CLI target was missing, could not start, or the retained command returned
  a general runtime failure.
- `2`: a safety/readiness gate blocked the requested Paper action. Argparse also
  uses `2` for invalid command syntax.
- Delegated commands otherwise propagate the exact child exit code. The CLI does
  not convert failed research/report commands into success.

## Compatibility paths

The existing Python dashboards remain callable during migration. Paper Batch
launchers already used `freakto.cli`; `run_market_replay.bat`,
`run_forward_test_status.bat`, and `run_research_paper_cycle.bat` now call the
canonical interface while retaining their filenames and interactive behavior.
Other specialist launchers remain legacy paths until their responsibility is
migrated in phase 5.

## Verification

- CLI contract and existing Paper consolidation suite: 18 passing tests.
- Real read-only invocation: `freakto data status --compact --no-save` completed
  with six of six local historical datasets ready and a passed no-lookahead
  audit.
- Installed entry point reports version `10.3.0` and renders help on the default
  Windows console encoding.
