# Freakto Regime Shadow Gate Activator v6.2.0

## Summary
- status: `SHADOW_COLLECTING_FORWARD_DATA`
- generated_utc: `2026-07-21T23:43:42.563711+00:00`
- horizon: `24h`
- min_samples: `30`
- decisions: `97`
- directional_decisions: `46`
- gates_tracked: `11`
- shadow_signals: `32`
- evaluated_shadow_samples: `29`
- pending_shadow_samples: `1`
- confirmed_candidates: `0`
- building_candidates: `11`
- rejected_candidates: `0`

## Gate Metrics
| Gate | Verdict | Signals | Evaluated | Pending | Avg | Win | T1 | Stop | MFE/MAE | Description |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| STRUCTURE_SCORE_GE_10 | SHADOW_BUILDING | 23 | 20 | 1 | 0.6001% | 85.0% | 70.0% | 60.0% | 2.757 | مثبت ولی نیازمند review: structure_score >= 10. |
| HISTORICAL_EDGE_SCORE_GE_1 | SHADOW_BUILDING | 8 | 8 | 0 | -1.2246% | 12.5% | 100.0% | 100.0% | 1.244 | Backtest candidate با stop کمتر: historical_edge_score >= 1. |
| RISK_MEDIUM | SHADOW_BUILDING | 1 | 1 | 0 | 0.5361% | 100.0% | 100.0% | 100.0% | 1.441 | Backtest candidate با sample بیشتر: risk_label = Medium. |
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
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 70 | 0.8086 | 2026-07-03 20:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 70 | 0.8479 | 2026-07-03 20:00:00 |
| HISTORICAL_EDGE_SCORE_GE_1 | EVALUATED | BTC/USDT | LONG | 49 | -2.8398 | 2026-07-07 12:00:00 |
| HISTORICAL_EDGE_SCORE_GE_1 | EVALUATED | BTC/USDT | LONG | 66 | -3.2625 | 2026-07-07 12:00:00 |
| HISTORICAL_EDGE_SCORE_GE_1 | EVALUATED | BTC/USDT | LONG | 75 | -0.3281 | 2026-07-10 08:00:00 |
| RISK_MEDIUM | EVALUATED | BTC/USDT | LONG | 47 | 0.5361 | 2026-07-10 16:00:00 |
| HISTORICAL_EDGE_SCORE_GE_1 | EVALUATED | BTC/USDT | LONG | 47 | 0.5361 | 2026-07-10 16:00:00 |
| HISTORICAL_EDGE_SCORE_GE_1 | EVALUATED | BTC/USDT | LONG | 62 | -0.5226 | 2026-07-11 04:00:00 |
| HISTORICAL_EDGE_SCORE_GE_1 | EVALUATED | BTC/USDT | LONG | 72 | -0.3786 | 2026-07-11 12:00:00 |
| HISTORICAL_EDGE_SCORE_GE_1 | EVALUATED | BTC/USDT | LONG | 67 | -0.8127 | 2026-07-11 20:00:00 |
| HISTORICAL_EDGE_SCORE_GE_1 | EVALUATED | BTC/USDT | LONG | 73 | -2.1886 | 2026-07-12 00:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | SHORT | 57 | 0.6924 | 2026-07-13 04:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 69 | -1.0821 | 2026-07-15 16:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 57 | -1.9251 | 2026-07-16 12:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 52 | 0.6156 | 2026-07-17 16:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 70 | -0.6667 | 2026-07-19 04:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 52 | 1.9995 | 2026-07-20 16:00:00 |
| STRUCTURE_SCORE_GE_10 | PARTIAL | BTC/USDT | LONG | 60 |  | 2026-07-21 04:00:00 |
| STRUCTURE_SCORE_GE_10 | PARTIAL | BTC/USDT | LONG | 65 |  | 2026-07-21 12:00:00 |
| STRUCTURE_SCORE_GE_10 | PENDING | BTC/USDT | LONG | 63 |  | 2026-07-21 16:00:00 |

## Recommendations
- Shadow هنوز در حال ساخت داده است؛ فعال‌ترین gate: STRUCTURE_SCORE_GE_10 | signals=23, evaluated=20.
- برای هر gate حداقل 30 نمونه Forward کامل لازم است.
- Regime Shadow gateهای v6.1 فعال شده‌اند، اما هنوز هیچ تصمیم Forward آن‌ها را پاس نکرده است.
- سه gate پایه که باید زیر نظر بمانند: VOLUME_SCORE_GE_10، RISK_MEDIUM، HISTORICAL_EDGE_SCORE_GE_1.

## Blockers
- کل نمونه‌های ارزیابی‌شده Shadow کمتر از 30 است: 29

## Safety Notes
- Shadow Gate هیچ Paper Trade و هیچ سفارش واقعی ایجاد نمی‌کند؛ فقط برچسب تحقیقاتی می‌زند.
- Gateهای پایه از Backtest و Gateهای Regime از v6.1 Regime-Gate Matrix آمده‌اند و باید در Forward مستقل تأیید شوند.
- تا وقتی هر gate، مخصوصاً gateهای Regime، حداقل 30 نمونه Forward کامل ندارد، نتیجه آماری قابل اتکا نیست.