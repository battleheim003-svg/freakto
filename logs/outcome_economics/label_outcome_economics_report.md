# Freakto Label & Outcome Economics Audit

- Status: **COMPLETE_NO_POLICY_CHANGE**
- Selected replay run: `market_replay_20260711_192507`
- Rows loaded / usable: `78452 / 14174`
- Canonical policy: `FIXED_CLOSE_6C_NET`
- Recommended replacement: `None`
- Policy change applied: `False`

## Key findings

- Selected latest replay run market_replay_20260711_192507; ignored 3 older runs to prevent repeated market-history counting.
- Canonical 6-candle net expectancy was -0.438369% with profit factor 0.708966.
- Best observed net label was FIXED_CLOSE_12C_NET at -0.289699%, but it did not satisfy promotion requirements.
- Gross expectancy was positive while net expectancy was non-positive in 5 all-directional horizon/adaptive comparisons; execution costs are a primary edge eraser.
- Mean round-trip execution cost was 0.588468%.
- Mean planned Target-1/Stop net reward-risk was 0.424390; the implied mean break-even win rate was 70.57%.
- Target 1 and Stop were both touched in 3547 rows, so path order matters even when final fixed-close labels are retained.
- Same-candle stop/target ambiguity affected 0.97% of rows; sensitivity is measurable but not the root cause.
- A target-hit flag must not be treated as a win label because target touches and canonical net losses can coexist.
- Longer fixed horizons reduced the net loss but did not produce positive all-directional net expectancy on the selected replay run.
- Isolated side-specific positive results were non-promotable because they were weak or temporally unstable: LONG FIXED_CLOSE_12C_NET (expectancy=0.011982%, PF=1.006493, positive folds=2/4).

## Blockers

- No alternative label/exit policy preserved positive net expectancy and profit factor >= 1.05.
- No policy met the required chronological stability, coverage, and minimum-sample constraints.
- Canonical labels and runtime exit behavior remain unchanged; this audit is diagnostic only.

## All-directional policy comparison

| Policy | n | Coverage | Expectancy | Win rate | PF |
|---|---:|---:|---:|---:|---:|
| FIXED_CLOSE_1C_NET | 14174 | 100.00% | -0.543044% | 25.98% | 0.356940 |
| FIRST_TOUCH_T1_STOP_1C_STOP_FIRST | 14174 | 100.00% | -0.562625% | 28.86% | 0.323788 |
| FIRST_TOUCH_T1_STOP_1C_TARGET_FIRST | 14174 | 100.00% | -0.543148% | 29.33% | 0.336583 |
| FIXED_CLOSE_3C_NET | 14174 | 100.00% | -0.493119% | 34.46% | 0.575613 |
| FIRST_TOUCH_T1_STOP_3C_STOP_FIRST | 14174 | 100.00% | -0.550343% | 42.85% | 0.470273 |
| FIRST_TOUCH_T1_STOP_3C_TARGET_FIRST | 14174 | 100.00% | -0.517954% | 43.64% | 0.490544 |
| FIXED_CLOSE_6C_NET | 14174 | 100.00% | -0.438369% | 38.65% | 0.708966 |
| FIRST_TOUCH_T1_STOP_6C_STOP_FIRST | 14174 | 100.00% | -0.534581% | 51.04% | 0.537436 |
| FIRST_TOUCH_T1_STOP_6C_TARGET_FIRST | 14174 | 100.00% | -0.496360% | 51.99% | 0.560498 |
| FIXED_CLOSE_12C_NET | 12944 | 91.32% | -0.289699% | 42.43% | 0.852142 |
| FIRST_TOUCH_T1_STOP_12C_STOP_FIRST | 14011 | 98.85% | -0.518273% | 55.63% | 0.572366 |
| FIRST_TOUCH_T1_STOP_12C_TARGET_FIRST | 14011 | 98.85% | -0.479304% | 56.61% | 0.595556 |
| ADAPTIVE_HORIZON_NET | 14174 | 100.00% | -0.320614% | 41.54% | 0.831514 |

## Safety

Research-only. No canonical label, score weight, Paper setting, or Live setting was changed.
