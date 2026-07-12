# Freakto Score Attribution & Component Ablation

- Status: **COMPLETE**
- Version: `v10.6.0`
- Dataset: `logs\market_replay\market_replay_evaluations.csv`
- Selected replay run: `market_replay_20260711_192507`
- Rows usable: **14174**
- Return target: `net_signed_return_after_6c_pct`
- Safety: research-only; no Paper/Live weights or gates were changed.

## Key findings

- The multivariate component model failed to generalize on chronological Holdout; direct weight promotion is not justified.
- Higher values were associated with worse future net return for: Momentum.
- Higher values were associated with better future net return for: Regime, Risk Penalty.
- No positive holdout permutation value was observed for: Trend, Volume, Structure.
- Actual win rate was below the payoff-implied break-even win rate; loss magnitude, not only hit rate, is a root cause.
- No adequately sampled score band had positive expectancy and profit factor >= 1; higher total score was not a reliable edge proxy.
- Positive score bands were sparse and non-promotable: 90-100 (n=30).
- Removing these components made fixed-gate holdout expectancy less negative, but did not restore edge: Structure.
- Removing these components reduced fixed-gate holdout expectancy: Volume.
- The full-score threshold selected on Optimize failed on untouched Holdout, confirming temporal instability.
- Ablation findings are diagnostic only; runtime weights remain unchanged until a new walk-forward replay validates them.

## Overall component association

| Component | Spearman vs return | High-minus-low return | Diagnosis |
|---|---:|---:|---|
| Risk Penalty | 0.027418 | 2.581938 | SUPPORTIVE_ASSOCIATION |
| Regime | 0.017416 | 0.650378 | SUPPORTIVE_ASSOCIATION |
| Adaptive Adjustment | -0.009563 | 0.179944 | MIXED_OR_WEAK |
| Volume | -0.002217 | 0.040534 | MIXED_OR_WEAK |
| Structure | 0.004428 | 0.005352 | MIXED_OR_WEAK |
| External Context | 0.000000 | 0.000000 | INACTIVE |
| Historical Edge | 0.000000 | 0.000000 | INACTIVE |
| Momentum | -0.006195 | -0.230566 | HARMFUL_ASSOCIATION |
| Trend | 0.000928 | -0.254844 | MIXED_OR_WEAK |

## Out-of-sample multivariate attribution

| Component | Standardized coefficient | Permutation MSE increase | Holdout value |
|---|---:|---:|---|
| Adaptive Adjustment | -0.01912233 | 0.01220415 | USEFUL |
| Risk Penalty | 0.05871921 | 0.00773356 | USEFUL |
| Regime | 0.04940717 | 0.00308743 | USEFUL |
| Momentum | 0.01058875 | 0.00198561 | USEFUL |
| External Context | 0.00000000 | 0.00000000 | INACTIVE |
| Historical Edge | 0.00000000 | 0.00000000 | INACTIVE |
| Trend | 0.04588330 | -0.00385522 | NO_HOLDOUT_VALUE |
| Volume | 0.08006599 | -0.01928841 | NO_HOLDOUT_VALUE |
| Structure | 0.13369660 | -0.02066780 | NO_HOLDOUT_VALUE |

## Decision economics

| Scope | Samples | Win rate | Avg return | Profit factor | Break-even win rate | Actual minus break-even |
|---|---:|---:|---:|---:|---:|---:|
| ALL | 14174 | 0.386482 | -0.438369 | 0.708966 | 0.470490 | -0.084008 |
| SIDE:LONG | 7453 | 0.402120 | -0.291882 | 0.792666 | 0.459021 | -0.056901 |
| SIDE:SHORT | 6721 | 0.369141 | -0.600810 | 0.628081 | 0.482303 | -0.113162 |

## Fixed-gate holdout ablation (score >= 70)

| Variant | Selected | Expectancy | Profit factor | Delta expectancy vs full | Diagnosis |
|---|---:|---:|---:|---:|---|
| WITHOUT_TREND_SCORE | 0 | 0.000000 | 0.000000 | 0.746615 | INSUFFICIENT_HOLDOUT_SELECTION |
| WITHOUT_MOMENTUM_SCORE | 0 | 0.000000 | 0.000000 | 0.746615 | INSUFFICIENT_HOLDOUT_SELECTION |
| WITHOUT_STRUCTURE_SCORE | 243 | -0.434103 | 0.668691 | 0.312512 | REMOVAL_IMPROVES_BUT_NEGATIVE |
| WITHOUT_ADAPTIVE_ADJUSTMENT | 462 | -0.710597 | 0.514862 | 0.036018 | NEUTRAL_OR_MIXED |
| WITHOUT_REGIME_SCORE | 339 | -0.718192 | 0.507177 | 0.028423 | NEUTRAL_OR_MIXED |
| FULL | 590 | -0.746615 | 0.496742 | 0.000000 | BASELINE |
| WITHOUT_EXTERNAL_CONTEXT_SCORE | 590 | -0.746615 | 0.496742 | 0.000000 | INACTIVE |
| WITHOUT_HISTORICAL_EDGE_SCORE | 590 | -0.746615 | 0.496742 | 0.000000 | INACTIVE |
| WITHOUT_RISK_PENALTY | 888 | -0.768836 | 0.537428 | -0.022221 | NEUTRAL_OR_MIXED |
| WITHOUT_VOLUME_SCORE | 180 | -1.088894 | 0.292121 | -0.342279 | REMOVAL_HURTS |

## Interpretation guardrails

- Association is not causation; correlated components can share the same market information.
- Thresholds were selected on the optimization slice only; Holdout was not used for selection.
- Removing a component from the recorded score is a diagnostic counterfactual, not a claim that the engine has already been safely reweighted.
- Any weight change requires a fresh replay, calibration, segmented validation, and later shadow-mode verification.
