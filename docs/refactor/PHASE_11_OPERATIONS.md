# Phase 11 background jobs and observability

## Outcome

Control Center Quick Start now launches a detached, persistent worker instead
of running the workflow inside the Streamlit request. Closing or refreshing the
browser no longer interrupts the job. All worker commands continue to force
live-order and real-capital flags off.

Runtime job state lives under the ignored directory
`.freakto-runtime/control-center/jobs/<job-id>/`. Each job records:

- queued, running, cancel-requested, succeeded, failed, cancelled, or
  interrupted status;
- process ID, timestamps, heartbeat, current step, and total progress;
- command, exit code, acceptance result, and bounded stdout/stderr tails for
  every completed step;
- a consolidated pipeline log and worker stdout/stderr logs.

State writes use a temporary file plus atomic replacement so the dashboard does
not observe partial JSON.

## Operator workflow

Start Quick Start from Overview, then use **Jobs & logs / اجراها و لاگ‌ها** to
inspect progress. Only one Quick Start job may be active at a time.

Cancel is cooperative and persistent: it is checked before and after every
step. A long Data/Replay step is allowed to finish before cancellation, which
avoids corrupting caches or checkpoints. Terminal jobs can be retried; retry
creates a new auditable job rather than rewriting history.

If a worker process disappears, the next dashboard refresh reconciles its state
to `INTERRUPTED`. Worker-launch failure is recorded as `FAILED` instead of
leaving a permanently queued job.

## Verification

- worker success including accepted review-only Go-live exit code 2;
- fail-fast behavior on the first unexpected command exit;
- cooperative cancellation before and after a step;
- safe environment overrides in the detached process;
- rejection of a second concurrent job;
- real child-process worker smoke test;
- bilingual Streamlit navigation and background-job controls;
- complete regression suite: 378 tests passed.

## Rollback

Stopping the dashboard does not stop an active worker. Request cancellation in
the Jobs page and wait for the current step to finish. Removing Control Center
job history is not required for rollback because it is ignored runtime evidence
and has no influence on trading decisions, Paper state, or Go-live evidence.
