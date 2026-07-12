# Freakto Label & Outcome Economics Audit Runbook

## Purpose

This research-only stage audits whether Freakto's negative out-of-sample results are caused by the canonical six-candle label, Target/Stop ordering, same-candle ambiguity, or execution economics.

It does **not** modify:

- `DecisionEngine`
- score weights
- canonical replay labels
- Paper Trading
- Live Trading
- runtime exit behavior

## Files

- `engine/outcome_economics.py`
  - parses entry, stop and targets
  - reconstructs round-trip costs
  - calculates planned gross/net reward-risk and break-even win rate
  - creates fixed-close and first-touch labels
  - calculates return, payoff and drawdown metrics
- `engine/exit_policy_audit.py`
  - selects the latest independent replay run
  - compares fixed 1/3/6/12-candle outcomes
  - compares conservative and optimistic first-touch assumptions
  - audits adaptive-horizon outcomes
  - measures gross-to-net execution-cost drag
  - audits label consistency and path dependence
  - checks chronological stability
- `label_outcome_economics_analysis.py`
  - command-line entry point

## Run

From the project root:

```bat
python -m pytest
python -X utf8 label_outcome_economics_analysis.py
```

Optional arguments:

```bat
python -X utf8 label_outcome_economics_analysis.py ^
  --dataset logs\market_replay\market_replay_evaluations.csv ^
  --output-dir logs\outcome_economics ^
  --canonical-horizon 6 ^
  --minimum-policy-rows 500
```

To audit a specific replay run:

```bat
python -X utf8 label_outcome_economics_analysis.py --run-id market_replay_YYYYMMDD_HHMMSS
```

## Compared policies

For each supported horizon, the audit compares:

- `FIXED_CLOSE_1C_NET`
- `FIXED_CLOSE_3C_NET`
- `FIXED_CLOSE_6C_NET`
- `FIXED_CLOSE_12C_NET`
- `FIRST_TOUCH_T1_STOP_*_STOP_FIRST`
- `FIRST_TOUCH_T1_STOP_*_TARGET_FIRST`
- `ADAPTIVE_HORIZON_NET`, when recorded

The first-touch policy uses Stop or Target 1 only when the recorded first exit occurred on or before the selected horizon. Otherwise it uses that horizon's fixed-close net return. It never chooses the best outcome after looking into the future.

## Intrabar ambiguity

OHLC data cannot determine whether Stop or Target was touched first when both levels occur inside the same candle. The audit reports both bounds:

- `STOP_FIRST`: conservative
- `TARGET_FIRST`: optimistic sensitivity bound

Neither assumption is promoted automatically. Lower-timeframe data is required to resolve the actual path.

## Generated outputs

The default output directory is `logs/outcome_economics/`:

- `outcome_policy_summary.csv`
- `outcome_policy_stability.csv`
- `execution_cost_drag.csv`
- `label_consistency.csv`
- `planned_trade_economics.csv`
- `intrabar_ambiguity_sensitivity.csv`
- `label_outcome_economics_report.json`
- `label_outcome_economics_report.md`

## Promotion rules

A replacement label policy is only considered a research candidate when it has:

- positive net expectancy
- profit factor at least `1.05`
- at least 500 usable samples
- at least 90% coverage
- at least 0.10 percentage-point improvement over the canonical policy
- positive expectancy and PF >= 1 in at least 3 of 4 chronological folds
- acceptable sensitivity to intrabar ambiguity

Even a passing result does not change runtime behavior automatically.

## Interpretation

`COMPLETE_NO_POLICY_CHANGE` is a valid audit outcome. It means the audit ran correctly, but no alternative outcome policy met the safety and stability requirements.

A positive gross result with a negative net result means execution costs exceed the raw signal edge. This cannot be repaired by relabeling wins and losses.

A high first-touch win rate is not sufficient. Compare it with the payoff-implied break-even win rate and profit factor.

## Safety

The tool is fail-closed and research-only. There is no `--promote` option and no code path that enables Paper or Live trading.
