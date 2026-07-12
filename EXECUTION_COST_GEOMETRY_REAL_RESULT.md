# Freakto Execution Cost & Trade Geometry Optimizer — Real Result

## Status

```text
Status                 : FAIL
Mode                   : RESEARCH_OPTIMIZATION_ONLY
Selected replay run    : market_replay_20260711_192507
Rows loaded/usable     : 78452 / 14174
Candidates evaluated   : 616
Recommended policy     : None
Promotion applied      : False
Paper/Live enabled     : False
```

## Chronological split

```text
Train    : 6854 rows | 2023-07-30 12:00:00+00:00 → 2024-12-31 20:00:00+00:00
Optimize : 3363 rows | 2025-01-05 04:00:00+00:00 → 2025-10-03 00:00:00+00:00
Holdout  : 3806 rows | 2025-10-08 20:00:00+00:00 → 2026-07-08 12:00:00+00:00
Purge    : 12 candles between partitions
```

## Canonical Holdout

```text
Samples       : 3806
Win rate      : 38.96%
Expectancy    : -0.540968%
Profit factor : 0.631902
Max drawdown  : -2473.745621%
```

## Development eligibility

```text
Fixed geometry eligible     : 0
Break-even eligible         : 0
Trailing diagnostic eligible: 3
```

No fixed stop/target geometry survived the full development constraints. Three statistically eligible development rows were duplicate gate variants of the same path-managed trailing geometry.

## Best development diagnostic

```text
Candidate ID                 : a5f127855ae17109
Scope                        : LONG
Minimum score                : 70
Horizon                      : 12 candles
Stop multiplier              : 1.25 × risk unit
Reward/risk target           : 3.0R
Management                   : TRAILING
Minimum target/cost multiple : 2.0
Maximum cost/risk            : 0.3
Minimum net reward/risk      : 0.75
Path assumption              : STOP_FIRST
Promotion eligible path      : False

Train expectancy             : 0.117933%
Train profit factor          : 1.070508
Optimize expectancy          : 0.803791%
Optimize profit factor       : 1.474934
Walk-forward pass rate       : 100.00%
```

## Untouched Holdout

```text
Samples       : 279
Coverage      : 7.33%
Win rate      : 34.05%
Expectancy    : -0.948416%
Profit factor : 0.520928
Max drawdown  : -292.232485%
Total return  : -264.608157%
```

The development result did not generalize. Expectancy reversed from positive Train/Optimize to strongly negative Holdout.

## Execution-cost sensitivity on Holdout

```text
Cost ×0.50 : expectancy -0.562916% | PF 0.656839
Cost ×0.75 : expectancy -0.707273% | PF 0.592958
Cost ×1.00 : expectancy -0.948416% | PF 0.520928
Cost ×1.25 : expectancy -1.118737% | PF 0.500992
Cost ×1.50 : expectancy -1.577142% | PF 0.406986
```

Even a hypothetical 50% reduction in recorded execution cost did not restore positive Holdout edge. Cost is important, but it is not the only root cause.

## Geometry source

```text
Mean recorded round-trip cost : 0.588468%
Mean baseline risk unit       : 2.245213%
Native ATR coverage           : 0%
Risk unit source              : PLANNED_STOP_PROXY
```

## Conclusion

- Reducing trade frequency with cost/geometry gates did not recover stable net edge.
- No fixed 1R/1.5R/2R/3R geometry passed development requirements.
- The only development-positive diagnostic was a 12-candle LONG trailing configuration with Score ≥70 and a 3R target.
- That configuration failed untouched Holdout and remained negative even at half recorded cost.
- Break-even and trailing promotion remains blocked because the replay stores aggregate MFE/MAE rather than full path ordering.
- Runtime trade geometry, canonical labels, Decision Engine weights, Paper and Live must remain unchanged.
