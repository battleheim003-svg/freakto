# Freakto operations

The installed `freakto` command is the canonical operator interface.

## Historical data

```text
freakto data status --compact
freakto data build --symbols BTC/USDT,ETH/USDT --timeframe 4h --years 3
```

## Causal replay

```text
freakto replay status --compact
freakto replay run --symbols BTC/USDT,ETH/USDT --timeframe 4h
freakto replay full --symbols BTC/USDT,ETH/USDT --timeframe 4h --years 3
freakto replay resume RUN_ID --compact
```

## Paper research

```text
freakto paper preflight
freakto paper arm-research
freakto paper cycle
freakto paper auto
freakto paper status
freakto paper dashboard
freakto paper disarm
freakto paper go-live-check
```

`go-live-check` evaluates the frozen Paper evidence contract. Even a passing
result is only eligible for independent manual review; it never enables live
orders or real-capital allocation. See
[`Phase 10 go-live criteria`](refactor/PHASE_10_GO_LIVE.md).

Real orders, real capital, and non-zero allocation remain unavailable through
the CLI. Readiness exit code `2` means blocked, not a runtime crash.

## Reports

```text
freakto report paper --no-plot
freakto report research
freakto report forward
```

`report forward` is read-only and only accepts optional `--send`.

## Unified control center

On Windows, launch the local management dashboard with:

```text
run_control_center.bat
```

Or run it directly:

```text
python -m streamlit run freakto_control_center.py
```

The control center combines Data, Replay, Paper, reports, and Go-live evidence
in one local interface. Every child command forces live-order and real-capital
flags off. Long-running Data/Replay actions and state-changing Paper actions
require explicit confirmation in the UI.

The language selector switches the complete interface between Persian (RTL)
and English (LTR). Smart Quick Start can run the ordered zero-capital workflow:
Data status/build, Replay status/run, Paper preflight, Research arming, one
Paper cycle, Paper/Forward reports, and the final review-only Go-live check. It
stops on the first unexpected exit code and preserves the per-step results.

Quick Start runs as a persistent background job. Monitor, cancel, retry, and
inspect it from **Jobs & logs / اجراها و لاگ‌ها**. Cancellation is cooperative:
the current Data/Replay step finishes before the worker stops, preventing a
partially written cache. Job history and logs are stored below
`.freakto-runtime/control-center/jobs/` and are intentionally excluded from Git.

## Runtime state

Mutable logs/history are excluded from the source branch. See
[Phase 6 storage](refactor/PHASE_6_RUNTIME_STORAGE.md) before copying or moving
state. Never use `--move` while a Paper or Shadow worker is running.

## Deeper protocols

- Paper readiness: [`PAPER_TRADE_READINESS_RUNBOOK.md`](../PAPER_TRADE_READINESS_RUNBOOK.md)
- Market replay: [`MARKET_REPLAY_RUNBOOK.md`](../MARKET_REPLAY_RUNBOOK.md)
- Forward testing: [`FORWARD_TEST_RUNBOOK.md`](../FORWARD_TEST_RUNBOOK.md)
