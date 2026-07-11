# Freakto Regime Shadow Gate Activator v6.2.0

## Summary
- status: `SHADOW_COLLECTING_FORWARD_DATA`
- generated_utc: `2026-07-11T22:34:49.919108+00:00`
- horizon: `24h`
- min_samples: `30`
- decisions: `59`
- directional_decisions: `35`
- gates_tracked: `11`
- shadow_signals: `22`
- evaluated_shadow_samples: `19`
- pending_shadow_samples: `1`
- confirmed_candidates: `0`
- building_candidates: `11`
- rejected_candidates: `0`

## Gate Metrics
| Gate | Verdict | Signals | Evaluated | Pending | Avg | Win | T1 | Stop | MFE/MAE | Description |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| STRUCTURE_SCORE_GE_10 | SHADOW_BUILDING | 14 | 14 | 0 | 0.8834% | 100.0% | 100.0% | 85.71% | 1.785 | مثبت ولی نیازمند review: structure_score >= 10. |
| HISTORICAL_EDGE_SCORE_GE_1 | SHADOW_BUILDING | 7 | 4 | 1 | -1.4736% | 25.0% | 50.0% | 50.0% | 0.407 | Backtest candidate با stop کمتر: historical_edge_score >= 1. |
| RISK_MEDIUM | SHADOW_BUILDING | 1 | 1 | 0 | 0.5361% | 100.0% | 0.0% | 0.0% | 2.127 | Backtest candidate با sample بیشتر: risk_label = Medium. |
| REGIME_TRENDING_BEAR__RISK_MEDIUM | SHADOW_BUILDING | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | v6.1 regime proposal: TRENDING_BEAR + risk_label = Medium. |
| REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT | SHADOW_BUILDING | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | v6.1 regime proposal: TRENDING_BEAR + risk_label = Medium + SHORT. |
| REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10 | SHADOW_BUILDING | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | v6.1 regime proposal: TRENDING_BEAR + structure_score >= 10. |
| REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT | SHADOW_BUILDING | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | v6.1 regime proposal: TRENDING_BEAR + structure_score >= 10 + SHORT. |
| VOLUME_SCORE_GE_10 | SHADOW_BUILDING | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | Backtest candidate قوی: volume_score >= 10. |
| SCORE_GE_80 | SHADOW_BUILDING | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | مثبت کم‌نمونه: score >= 80؛ فقط watchlist تحقیقاتی. |
| DOGE_SHORT_WATCH | SHADOW_BUILDING | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | مثبت کم‌نمونه: DOGE/USDT SHORT. |
| BNB_LONG_SCORE_GE_60 | SHADOW_BUILDING | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | مثبت کم‌نمونه: BNB/USDT LONG + score>=60. |

## Recent Signals
| Gate | Status | Symbol | Side | Score | Return | Candle |
|---|---|---|---|---:|---:|---|
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 56 | 0.5531 | 2026-07-03 20:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 65 | 0.562 | 2026-07-03 20:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 70 | 0.4897 | 2026-07-03 20:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 68 | 0.7856 | 2026-07-03 20:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 68 | 0.8566 | 2026-07-03 20:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 67 | 0.9276 | 2026-07-03 20:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 70 | 0.8199 | 2026-07-03 20:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 72 | 0.6401 | 2026-07-03 20:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 70 | 0.7874 | 2026-07-03 20:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 70 | 0.8457 | 2026-07-03 20:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 70 | 0.8086 | 2026-07-03 20:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 70 | 0.8479 | 2026-07-03 20:00:00 |
| HISTORICAL_EDGE_SCORE_GE_1 | EVALUATED | BTC/USDT | LONG | 49 | -2.8398 | 2026-07-07 12:00:00 |
| HISTORICAL_EDGE_SCORE_GE_1 | EVALUATED | BTC/USDT | LONG | 66 | -3.2625 | 2026-07-07 12:00:00 |
| HISTORICAL_EDGE_SCORE_GE_1 | EVALUATED | BTC/USDT | LONG | 75 | -0.3281 | 2026-07-10 08:00:00 |
| RISK_MEDIUM | EVALUATED | BTC/USDT | LONG | 47 | 0.5361 | 2026-07-10 16:00:00 |
| HISTORICAL_EDGE_SCORE_GE_1 | EVALUATED | BTC/USDT | LONG | 47 | 0.5361 | 2026-07-10 16:00:00 |
| HISTORICAL_EDGE_SCORE_GE_1 | PARTIAL | BTC/USDT | LONG | 62 |  | 2026-07-11 04:00:00 |
| HISTORICAL_EDGE_SCORE_GE_1 | PARTIAL | BTC/USDT | LONG | 72 |  | 2026-07-11 12:00:00 |
| HISTORICAL_EDGE_SCORE_GE_1 | PENDING | BTC/USDT | LONG | 67 |  | 2026-07-11 20:00:00 |

## Recommendations
- Shadow هنوز در حال ساخت داده است؛ فعال‌ترین gate: STRUCTURE_SCORE_GE_10 | signals=14, evaluated=14.
- برای هر gate حداقل 30 نمونه Forward کامل لازم است.
- Regime Shadow gateهای v6.1 فعال شده‌اند، اما هنوز هیچ تصمیم Forward آن‌ها را پاس نکرده است.
- سه gate پایه که باید زیر نظر بمانند: VOLUME_SCORE_GE_10، RISK_MEDIUM، HISTORICAL_EDGE_SCORE_GE_1.

## Blockers
- کل نمونه‌های ارزیابی‌شده Shadow کمتر از 30 است: 19

## Safety Notes
- Shadow Gate هیچ Paper Trade و هیچ سفارش واقعی ایجاد نمی‌کند؛ فقط برچسب تحقیقاتی می‌زند.
- Gateهای پایه از Backtest و Gateهای Regime از v6.1 Regime-Gate Matrix آمده‌اند و باید در Forward مستقل تأیید شوند.
- تا وقتی هر gate، مخصوصاً gateهای Regime، حداقل 30 نمونه Forward کامل ندارد، نتیجه آماری قابل اتکا نیست.