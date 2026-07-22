# Phase 10 Paper readiness and go-live criteria

## Outcome

The evaluation contract and go-live review gates are now executable and
fail-closed. This phase does **not** enable live orders. Its strongest possible
result is `ELIGIBLE_FOR_MANUAL_GO_LIVE_REVIEW`; real-capital activation remains
unimplemented, requires a separate controlled change, and always reports:

- `live_orders_enabled: false`;
- `real_capital_enabled: false`;
- `allocation_pct: 0.0`.

## Frozen evaluation contract

`config/paper_go_live_policy.json` freezes the deterministic strategy, six-symbol
universe, 4-hour timeframe, closed-candle rule, next-open fill model, and the
feature/model/calibration/execution/split versions. Tests require these version
identifiers to match `engine.model_contract.CURRENT_MODEL_CONTRACT`.

An evidence record must repeat the frozen contract exactly and identify a
completed evaluation window with start/end timestamps and a data fingerprint.
Changing strategy, data, thresholds, or model versions invalidates the window;
the operator must start a new untouched evaluation instead of editing evidence.

## Required gates

All gates are conjunctive:

- at least 200 closed Paper trades over at least 60 observation days;
- after-cost expectancy of at least 0.05R, with the 95% lower bound strictly
  above zero and profit factor at least 1.10;
- absolute maximum drawdown no greater than 12R;
- at least three regimes with 30 trades each and positive expectancy in at
  least two thirds of adequately sampled regimes;
- cycle success and data freshness rates of at least 99%, with zero critical
  incidents;
- verified operator-stop, stale-data, loss-limit, and restart-fail-closed
  kill-switch drills;
- at least two independent approvals.

No gate is optional and missing/malformed evidence is blocked.

## Verification

- 15 focused go-live contract tests passed, including one negative test per
  critical gate and an all-gates-positive review-only case;
- the canonical CLI returned exit code 2 with no runtime evidence present;
- the complete regression suite passed all 364 tests;
- the policy and example evidence parsed as strict JSON;
- 743 canonical text files passed the UTF-8 validator.

## Operation

Copy `docs/paper/go_live_evidence.example.json` to the runtime-only path
`logs/paper_launch_v2/go_live_evidence.json`, then populate it only from a
completed frozen evaluation. Run:

```text
freakto paper go-live-check
```

Exit code `2` means blocked; exit code `0` means eligible for independent manual
review, not authorized for trading. The JSON result lists every gate, actual and
required values, and blockers.

## Rollback and change control

Removing the runtime evidence file immediately restores the blocked state. A
policy change requires a new policy version, tests, approvals, and a new
evaluation window. Compatibility Paper commands remain unchanged. Any future
live adapter must be introduced as a separately reviewed phase and must not
reinterpret this review result as an execution token.
