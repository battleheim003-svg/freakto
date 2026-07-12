# Freakto Expectancy-Aware Champion–Challenger Report

- Status: **FAIL**
- Mode: **RESEARCH_SHADOW_ONLY**
- Selected replay run: `market_replay_20260711_192507`
- Rows usable: **14,174**
- Recommended variant: `None`
- Recommended threshold: `None`
- Promotion applied: **False**
- Paper/Live enabled: **False**

## Champion Holdout

- Samples: 436
- Expectancy: -0.900106%
- Profit factor: 0.442878
- Max drawdown: -426.342212%

## Challenger Summary

| variant | status | sample_count | expectancy | profit_factor | fixed_zero_ev_sample_count | fixed_zero_ev_expectancy | fixed_zero_ev_profit_factor | max_drawdown | walk_forward_pass_rate | promotable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EXPECTANCY_BASE | FAIL | 85 | -1.450304 | 0.359434 | 1084 | -0.793016 | 0.489276 | -143.768364 | 0.0 | False |
| EXPECTANCY_NO_MOMENTUM | FAIL | 0 | 0.0 | 0.0 | 1032 | -0.889174 | 0.45325 | 0.0 | 0.0 | False |
| EXPECTANCY_STRUCTURE_GATE | FAIL | 0 | 0.0 | 0.0 | 881 | -0.887243 | 0.453976 | 0.0 | 0.0 | False |
| EXPECTANCY_LONG_ONLY | FAIL | 0 | 0.0 | 0.0 | 501 | -1.074534 | 0.38086 | 0.0 | 0.0 | False |
| EXPECTANCY_SHORT_DISABLED | FAIL | 0 | 0.0 | 0.0 | 501 | -1.074534 | 0.38086 | 0.0 | 0.0 | False |

## Key Findings

- Selected latest replay run market_replay_20260711_192507; ignored 3 older runs to avoid repeated market-history counting.
- No challenger is eligible to replace the Champion; runtime weights and Paper/Live settings remain unchanged.
- No Optimize-selected challenger produced positive Holdout expectancy with profit factor >= 1.
- Even the fixed EV>=0 diagnostic remained non-positive across all adequately sampled challengers.
- Expected value includes side-specific win probability, predicted win/loss magnitude, execution buffer, and explicit risk-cost haircut.
- Structure is used as a gate in designated variants; Volume remains a confirmation gate; Momentum is capped or removed.

## Blockers

- No challenger preserved positive, sufficiently sampled, temporally stable edge on untouched Holdout.

## Safety

This report is research-only. It does not replace the runtime Champion, alter score weights, enable Paper/Live trading, or place orders.
