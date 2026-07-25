# Freakto Workflow Control Center

Status: local operations console  
Capital mode: zero real capital  
Live activation: unavailable  
Core engine changes: none

## Start

On Windows:

```text
run_control_center.bat
```

Or directly:

```text
python -X utf8 -m streamlit run freakto_control_center.py
```

The launcher and every child job force:

```text
LIVE_TRADING_ENABLED=false
REAL_CAPITAL_ENABLED=false
```

## Sections

Navigation is intentionally reduced to four stable workspaces:

1. **Operations** — current job, live progress, current/next step, blockers,
   recommended action, quick start, and latest result;
2. **Workflows** — independent Data/Markets, Validation/Paper, and supporting
   Research controls;
3. **Reports** — readiness gates, blockers, job history, step results, retry,
   cancellation, and complete logs;
4. **Settings & Automation** — persisted schedules, scheduler health, the
   fail-closed safety contract, and advanced paths.

Primary actions stay visible. Dates, CSV paths, direct Paper controls, and raw
logs stay inside advanced panels until needed.

## Local automation scheduler

Schedules are persisted under:

```text
.freakto-runtime/control-center/automation/schedules.json
```

Enabling the first schedule starts a detached local scheduler. It continues
after the browser closes, polls due schedules, and launches only fixed,
allowlisted Research/Paper workflows. It never bypasses the single-active-job
lock: a due schedule waits while another job is active. Disabling every
schedule lets the scheduler exit cleanly on its next poll.

Available presets are Data & Replay, Forward & Shadow, report refresh, and
Airdrop outcome refresh. Every spawned process forces
`LIVE_TRADING_ENABLED=false` and `REAL_CAPITAL_ENABLED=false`.

### Data & Replay

Controls the existing crypto data and Replay commands. Long-running actions
require a confirmation checkbox.

### New Markets

- audits EUR/USD and XAU/USD through the external Dukascopy adapters;
- displays the number of adapter manifests;
- runs the unchanged Replay consumer with the documented conservative shared
  costs;
- never writes to `engine/` and never changes a Decision Engine rule.

### Forward & Shadow

Runs one ordered cycle:

1. Paper preflight;
2. Research arm;
3. one zero-capital observation cycle;
4. Forward report;
5. Paper status.

### Showcase Paper

Showcase Paper is a separate, visual simulation mode for observing activity
without waiting for the official Paper evidence gates. When enabled it:

1. reads directional analysis for the configured crypto universe;
2. opens several isolated simulated Long/Short positions up to the chosen
   daily and concurrent limits;
3. marks each open position against current public market prices;
4. closes on Stop, Target, maximum holding time, or an operator stop;
5. produces a portrait PNG card for every Open and Close event.

Runtime data is stored only under:

```text
logs/showcase_paper/
.freakto-runtime/showcase-paper/
```

Every record and card is marked `SHOWCASE_PAPER`, zero-real-capital, and
`official_evidence_eligible=false`. Showcase trades never enter the official
Paper ledger, 60-day campaign statistics, or Go-live evidence. Display
leverage is capped at 5x, and all Live environment flags remain forced off.

The job stops immediately if Preflight, arm, or cycle is blocked. A blocked
gate is not converted into success.

### Airdrop Radar

Runs prediction sync followed by the outcome report. Missing Radar evidence is
accepted only as the explicit `SYNC_BLOCKED` research state so the report can
still explain the missing sample. Wallet connect, signing, and claim automation
are not exposed.

### Cross-Asset Ranking

Rank and evaluation are separate jobs. Inputs must:

- be CSV files;
- exist before launch;
- remain inside the Freakto workspace.

The output remains a research report and is not connected to Decision Engine,
Paper, or Live actions.

### Paper Trading

Uses the existing fail-closed Paper controls and campaign manager. Strategy
Paper still requires its own readiness checks.

### Jobs & logs

Every background job persists:

- workflow kind and options;
- PID and heartbeat;
- current and completed steps;
- exit codes and accepted/blocking status;
- stdout/stderr tails;
- a complete pipeline log.

Runtime state is stored under:

```text
.freakto-runtime/control-center/jobs/
```

This directory is ignored by Git. Jobs can be refreshed, cancelled after the
current step, or retried. Only one background job may run at a time, preventing
concurrent writes to shared research artifacts.

## Safety contract

The dashboard uses fixed allowlisted workflows. It does not expose a free-form
shell, arbitrary Python entry point, or arbitrary file path. Go-live remains a
read-only evidence review and can never enable exchange orders.
