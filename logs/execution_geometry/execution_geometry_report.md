# Freakto Execution Cost & Trade Geometry Optimizer

- Status: **FAIL**
- Mode: `RESEARCH_OPTIMIZATION_ONLY`
- Selected replay run: `market_replay_20260711_192507`
- Rows loaded/usable: `78452 / 14174`
- Promotion applied: `False`

## Canonical Holdout

```json
{
  "sample_count": 3806,
  "win_count": 1483,
  "loss_count": 2323,
  "flat_count": 0,
  "win_rate": 0.389648,
  "avg_return": -0.540968,
  "median_return": -0.71004,
  "avg_win": 2.383336,
  "avg_loss": 2.407839,
  "payoff_ratio": 0.989824,
  "break_even_win_rate": 0.502557,
  "expectancy": -0.540968,
  "profit_factor": 0.631902,
  "max_drawdown": -2473.745621,
  "total_return": -2058.922502
}
```

## Selected Candidate

```json
{
  "candidate_id": "a5f127855ae17109",
  "scope": "LONG",
  "minimum_score": 70,
  "minimum_target_cost_multiple": 2.0,
  "maximum_cost_to_risk": 0.3,
  "minimum_net_reward_risk": 0.75,
  "geometry": {
    "horizon_candles": 12,
    "stop_multiplier": 1.25,
    "reward_risk": 3.0,
    "management_policy": "TRAILING",
    "break_even_trigger_r": 1.0,
    "trailing_trigger_r": 1.0,
    "trailing_distance_r": 0.75,
    "path_assumption": "STOP_FIRST",
    "cost_multiplier": 1.0
  }
}
```

## Candidate Holdout

```json
{
  "sample_count": 279,
  "win_count": 95,
  "loss_count": 184,
  "flat_count": 0,
  "win_rate": 0.340502,
  "avg_return": -0.948416,
  "median_return": -2.478977,
  "avg_win": 3.0287,
  "avg_loss": 3.001819,
  "payoff_ratio": 1.008955,
  "break_even_win_rate": 0.497771,
  "expectancy": -0.948416,
  "profit_factor": 0.520928,
  "max_drawdown": -292.232485,
  "total_return": -264.608157,
  "eligible_rows": 281,
  "coverage": 0.073305
}
```

## Key findings
- Mean recorded round-trip cost was 0.588468% versus mean baseline risk unit 2.245213%.
- No native ATR percentage column was present; planned stop distance was used as the explicit risk-unit proxy.
- Cost-to-target, cost-to-risk, net reward/risk, side, and score gates use entry-time fields only.
- Break-even and trailing candidates use conservative STOP_FIRST ordering; optimistic path assumptions are not promotion eligible.
- Development eligibility: fixed geometry=0, path-managed diagnostics=3.
- One candidate was selected on development data and audited once on Holdout: a5f127855ae17109.
- The selected gate retained 7.33% of Holdout rows and produced -0.948416% expectancy with PF 0.520928.
- At 50% of recorded execution cost, selected-candidate Holdout expectancy remained -0.562916% with PF 0.656839.
- No runtime geometry or execution-cost policy is recommended for promotion.

## Blockers
- The Optimize-selected candidate failed untouched Holdout promotion constraints.
- The selected break-even/trailing policy is diagnostic-only because aggregate MFE/MAE does not preserve full path order.

## Safety

This tool is research-only. It does not modify runtime score weights, canonical labels, Paper, or Live settings.
