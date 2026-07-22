# Phase 13 — Frozen Paper evidence campaign

Status: **active**

Campaign `paper-20260722-161631` started at
`2026-07-22T16:16:31.350645+00:00`. Its earliest time-based completion is
`2026-09-20T16:16:31.350645+00:00`; completion also requires at least 200
closed Paper trades. Time and sample requirements are conjunctive and cannot be
bypassed by replaying or editing historical samples.

## Frozen contract and safety

- Policy: `config/paper_go_live_policy.json`
- Frozen contract SHA-256:
  `bc4ff61e88232e15cc0faa48435cfd1f27885927c8e47f624c1db0a2eb459f36`
- Symbols: BTC, ETH, SOL, BNB, XRP, and DOGE against USDT on closed 4-hour bars.
- `LIVE_TRADING_ENABLED=false`, `REAL_CAPITAL_ENABLED=false`, allocation 0%.
- Research arming does not enable exchange orders or real capital.

## Persistence and recovery

`FreaktoPaperCampaign` is a current-user Windows Scheduled Task. It runs
`run_paper_campaign.bat` at logon and was started immediately when installed.
Task settings reject duplicate instances, start missed work when available, and
retry a failed launch three times. The orchestrator's own process lock provides
an additional duplicate-run guard.

The worker aligns runs to closed 4-hour candles and writes its heartbeat and
lock under `logs/paper_cycle/`. Campaign state is stored atomically at
`.freakto-runtime/paper-campaign/state.json`; a restarted dashboard reconciles
that state with the live heartbeat PID.

Status can be inspected from the Control Center Paper page or with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\paper_campaign_status.ps1
```

If Task Scheduler metadata is not readable in a restricted terminal, the script
still prints authoritative application campaign state.

## Stop and resume

The Control Center stop action writes `logs/paper_cycle/campaign_stop.flag`.
The worker exits before the next cycle, or after the current cycle finishes.
Starting again removes the stop flag, reruns preflight and research arming, and
preserves the original evidence start time. No worker is force-killed midway
through a cycle.

## Verification

- Campaign-specific, Control Center, and orchestrator tests: 25 passed.
- Scheduled task state at installation: `Running`.
- Worker heartbeat: `WAITING_FOR_NEXT_CANDLE`, live orders disabled.
- Full project suite must remain green before hand-off.

## Rollback

First request a cooperative stop in the Control Center and wait for the task to
become Ready. An administrator can then remove only the registered task:

```powershell
Unregister-ScheduledTask -TaskName FreaktoPaperCampaign -Confirm:$false
```

Removing the task does not delete campaign state, evidence, logs, or the frozen
contract. Reinstalling it with `scripts\install_paper_campaign_task.ps1` resumes
the same campaign window.
