# Freakto Score Calibration & Feature Attribution v10.3.0

- Status: **SCORE_MISCALIBRATED_NO_ROBUST_CANDIDATE**
- Rows analyzed: **14174**
- Score verdict: **SCORE_INVERTED_OR_MISCALIBRATED**
- Forward Shadow candidates: **0**

## Test Score Bands

| score_band | samples | win_rate_pct | avg_net_return_pct | profit_factor |
|---|---|---|---|---|
| 50_59 | 1468 | 39.99 | -0.570272 | 0.5912 |
| 60_69 | 968 | 38.12 | -0.708521 | 0.5316 |
| 70_79 | 476 | 35.08 | -0.72889 | 0.511 |
| 80_89 | 155 | 27.74 | -1.074748 | 0.3501 |
| 90_PLUS | 7 | 42.86 | 0.69067 | 1.7568 |

## Feature Attribution

| feature | train_q25 | train_q75 | validation_20_high_minus_low_pct | test_20_high_minus_low_pct | test_20_correlation | verdict |
|---|---|---|---|---|---|---|
| risk_penalty | -8.0 | -2.0 | 0.242583 | 0.159502 | 0.02775 | WEAK_OR_MIXED_ASSOCIATION |
| regime_confidence | 62.0 | 100.0 | -0.340649 | 0.066275 | 0.029693 | UNSTABLE_VALIDATION_TEST_SIGN_FLIP |
| momentum_score | 20.0 | 26.0 | 0.313131 | -0.210603 | -0.032931 | UNSTABLE_VALIDATION_TEST_SIGN_FLIP |
| decision_aligned_score | 54.0 | 67.0 | 0.553816 | -0.298007 | -0.0432 | UNSTABLE_VALIDATION_TEST_SIGN_FLIP |
| volume_score | 0.0 | 9.0 | 0.302982 | -0.31833 | -0.046398 | UNSTABLE_VALIDATION_TEST_SIGN_FLIP |
| structure_score | 6.0 | 8.0 | 0.015519 | -0.412167 | -0.050474 | UNSTABLE_VALIDATION_TEST_SIGN_FLIP |
| trend_score | 28.0 | 28.0 |  |  |  | LOW_VARIANCE_OR_INSUFFICIENT_DATA |
| regime_score | 5.0 | 5.0 |  |  |  | LOW_VARIANCE_OR_INSUFFICIENT_DATA |

## Feature Interactions

| interaction | validation_samples | validation_avg_net_pct | test_samples | test_avg_net_pct | test_profit_factor | verdict |
|---|---|---|---|---|---|---|
| decision_aligned_score>=67.0 & volume_score>=9.0 | 512 | -0.075824 | 539 | -0.945818 | 0.4348 | REJECT_TEST_NET_NON_POSITIVE |
| decision_aligned_score>=67.0 & structure_score>=8.0 | 396 | -0.103048 | 358 | -0.981523 | 0.4032 | REJECT_TEST_NET_NON_POSITIVE |
| volume_score>=9.0 & structure_score>=8.0 | 282 | -0.16193 | 265 | -1.338639 | 0.3866 | REJECT_TEST_NET_NON_POSITIVE |

## Recommendations

- Score نهایی در Test monotonic نیست؛ بالا بردن Threshold به‌تنهایی ممنوع و وزن‌ها باید فقط در Shadow بازطراحی شوند.
- هیچ Interaction مقاوم در Validation/Test پیدا نشد؛ Decision Engine فعلی بدون تغییر بماند و Paper/Live ارتقا نگیرد.
- هر تغییر وزن باید با Config جدا، Replay مجدد، Validation/Test قفل‌شده و سپس Forward Shadow تأیید شود.

## Safety

Research-only. No strategy settings, Paper orders or Live orders are changed.