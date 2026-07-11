# Freakto v10.2.0 — Validation Results

Validation was run against the user's real Market Replay ledger:

- Total Replay rows: **39,782**
- Complete directional rows analyzed: **14,746**
- Chronological splits: **TRAIN_60 / VALIDATION_20 / TEST_20**
- Primary evaluation horizon: **1 day / 6 × 4h candles**

## Score calibration

- Status: `SCORE_MISCALIBRATED_NO_ROBUST_CANDIDATE`
- Score verdict: `SCORE_INVERTED_OR_MISCALIBRATED`
- Test band monotonicity: **-1.0**
- Adjacent band violations: **3**
- High-score minus low-score Test Net: **-0.207144%**

### Test score bands

| Score band | Samples | Win rate | Avg net | Profit factor |
|---|---:|---:|---:|---:|
| 50–59 | 1,516 | 43.47% | -0.291350% | 0.7623 |
| 60–69 | 1,004 | 41.14% | -0.449144% | 0.6677 |
| 70–79 | 507 | 38.26% | -0.479623% | 0.6377 |
| 80–89 | 167 | 29.34% | -0.809512% | 0.4403 |
| 90+ | 7 | 42.86% | +0.924178% | 2.1719 |

The 90+ bucket is not eligible because it has only seven Test samples.

## Feature attribution

No feature passed the stable positive association rule across Train, Validation and Test.

Most important Test observations:

| Feature | Test Spearman | Test Q4−Q1 net | Verdict |
|---|---:|---:|---|
| risk_penalty | +0.020794 | +0.089707% | Weak/mixed |
| regime_confidence | +0.023375 | +0.052972% | Validation/Test sign flip |
| momentum_score | -0.027776 | -0.167815% | Validation/Test sign flip |
| volume_score | -0.043401 | -0.283338% | Validation/Test sign flip |
| decision_aligned_score | -0.049075 | -0.298904% | Validation/Test sign flip |
| structure_score | -0.054205 | -0.418852% | Validation/Test sign flip |

Trend and Regime component scores had insufficient variance for meaningful quartile attribution in this dataset.

## Feature interactions

- Robust Forward Shadow candidates: **0**
- One interaction was positive only in Test but unstable across earlier splits:
  `regime_confidence >= 100 & momentum_score >= 26`
- No interaction passed the requirement of positive Train, Validation and Test Net with Validation/Test PF above 1.

## Segment analysis

No Symbol, Regime or Side segment was positive in Test after costs. The least-negative Test regime was `SIDEWAYS`, followed by `TRENDING_BEAR`.

## Decision

The current score is not calibrated as a quality ranking. Increasing the score threshold does not improve out-of-sample performance and generally makes it worse. No automatic weight change was applied. Any future weight redesign must use a separate candidate configuration, a fresh replay experiment, locked Validation/Test rules and Forward Shadow confirmation.
