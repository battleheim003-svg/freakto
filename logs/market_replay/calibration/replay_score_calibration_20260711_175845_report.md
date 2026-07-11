# Freakto Score Calibration & Feature Attribution v10.2.0

- Status: **SCORE_MISCALIBRATED_NO_ROBUST_CANDIDATE**
- Rows analyzed: **14746**
- Score verdict: **SCORE_INVERTED_OR_MISCALIBRATED**
- Forward Shadow candidates: **0**

## Test Score Bands

| score_band | samples | win_rate_pct | avg_net_return_pct | profit_factor |
|---|---|---|---|---|
| 50_59 | 1516 | 43.47 | -0.29135 | 0.7623 |
| 60_69 | 1004 | 41.14 | -0.449144 | 0.6677 |
| 70_79 | 507 | 38.26 | -0.479623 | 0.6377 |
| 80_89 | 167 | 29.34 | -0.809512 | 0.4403 |
| 90_PLUS | 7 | 42.86 | 0.924178 | 2.1719 |

## Feature Attribution

| feature | train_q25 | train_q75 | validation_20_high_minus_low_pct | test_20_high_minus_low_pct | test_20_correlation | verdict |
|---|---|---|---|---|---|---|
| risk_penalty | -8.0 | 0.0 | 0.279164 | 0.089707 | 0.020794 | WEAK_OR_MIXED_ASSOCIATION |
| regime_confidence | 62.0 | 100.0 | -0.337642 | 0.052972 | 0.023375 | UNSTABLE_VALIDATION_TEST_SIGN_FLIP |
| momentum_score | 20.0 | 26.0 | 0.311563 | -0.167815 | -0.027776 | UNSTABLE_VALIDATION_TEST_SIGN_FLIP |
| volume_score | 0.0 | 9.0 | 0.299276 | -0.283338 | -0.043401 | UNSTABLE_VALIDATION_TEST_SIGN_FLIP |
| decision_aligned_score | 55.0 | 67.0 | 0.424148 | -0.298904 | -0.049075 | UNSTABLE_VALIDATION_TEST_SIGN_FLIP |
| structure_score | 6.0 | 8.0 | 0.027568 | -0.418852 | -0.054205 | UNSTABLE_VALIDATION_TEST_SIGN_FLIP |
| trend_score | 28.0 | 28.0 |  |  |  | LOW_VARIANCE_OR_INSUFFICIENT_DATA |
| regime_score | 5.0 | 5.0 |  |  |  | LOW_VARIANCE_OR_INSUFFICIENT_DATA |

## Feature Interactions

| interaction | validation_samples | validation_avg_net_pct | test_samples | test_avg_net_pct | test_profit_factor | verdict |
|---|---|---|---|---|---|---|
| regime_confidence>=100.0 & momentum_score>=26.0 | 170 | 0.561001 | 189 | 0.03834 | 1.0315 | RESEARCH_ONLY_UNSTABLE_INTERACTION |
| risk_penalty>=0.0 & regime_confidence>=100.0 | 144 | 0.354092 | 216 | -0.068836 | 0.9324 | REJECT_TEST_NET_NON_POSITIVE |
| risk_penalty>=0.0 & momentum_score>=26.0 | 309 | 0.405495 | 409 | -0.245075 | 0.7378 | REJECT_TEST_NET_NON_POSITIVE |
| momentum_score>=26.0 & decision_aligned_score>=67.0 | 449 | 0.362009 | 499 | -0.30835 | 0.751 | REJECT_TEST_NET_NON_POSITIVE |
| momentum_score>=26.0 & volume_score>=9.0 | 390 | 0.387277 | 423 | -0.364035 | 0.7252 | REJECT_TEST_NET_NON_POSITIVE |
| risk_penalty>=0.0 & decision_aligned_score>=67.0 | 209 | 0.37987 | 285 | -0.383383 | 0.6471 | REJECT_TEST_NET_NON_POSITIVE |
| regime_confidence>=100.0 & decision_aligned_score>=67.0 | 370 | 0.176151 | 362 | -0.464919 | 0.6631 | OVERFIT_INTERACTION |
| momentum_score>=26.0 & structure_score>=8.0 | 229 | 0.024316 | 219 | -0.622822 | 0.5461 | REJECT_TEST_NET_NON_POSITIVE |
| regime_confidence>=100.0 & structure_score>=8.0 | 546 | -0.088953 | 489 | -0.648859 | 0.5989 | OVERFIT_INTERACTION |
| risk_penalty>=0.0 & volume_score>=9.0 | 162 | -0.07253 | 183 | -0.65372 | 0.4485 | REJECT_TEST_NET_NON_POSITIVE |
| volume_score>=9.0 & decision_aligned_score>=67.0 | 549 | 0.214192 | 587 | -0.664763 | 0.5475 | OVERFIT_INTERACTION |
| decision_aligned_score>=67.0 & structure_score>=8.0 | 410 | 0.164782 | 376 | -0.745406 | 0.4916 | OVERFIT_INTERACTION |
| risk_penalty>=0.0 & structure_score>=8.0 | 61 | 0.330448 | 86 | -0.76073 | 0.3768 | REJECT_TEST_NET_NON_POSITIVE |
| regime_confidence>=100.0 & volume_score>=9.0 | 319 | 0.061351 | 342 | -0.801143 | 0.5676 | REJECT_TEST_NET_NON_POSITIVE |
| volume_score>=9.0 & structure_score>=8.0 | 298 | 0.124668 | 282 | -1.077465 | 0.4527 | OVERFIT_INTERACTION |

## Recommendations

- Score نهایی در Test monotonic نیست؛ بالا بردن Threshold به‌تنهایی ممنوع و وزن‌ها باید فقط در Shadow بازطراحی شوند.
- هیچ Interaction مقاوم در Validation/Test پیدا نشد؛ Decision Engine فعلی بدون تغییر بماند و Paper/Live ارتقا نگیرد.
- هر تغییر وزن باید با Config جدا، Replay مجدد، Validation/Test قفل‌شده و سپس Forward Shadow تأیید شود.

## Safety

Research-only. No strategy settings, Paper orders or Live orders are changed.