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
