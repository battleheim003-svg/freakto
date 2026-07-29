# Freakto Regime Shadow Gate Activator v6.2.0

## Summary
- status: `SHADOW_REVIEW_REQUIRED`
- generated_utc: `2026-07-29T10:17:46.728588+00:00`
- horizon: `24h`
- min_samples: `30`
- decisions: `121`
- directional_decisions: `52`
- gates_tracked: `11`
- shadow_signals: `39`
- evaluated_shadow_samples: `38`
- pending_shadow_samples: `0`
- confirmed_candidates: `0`
- building_candidates: `11`
- rejected_candidates: `0`

## Gate Metrics
| Gate | Verdict | Signals | Evaluated | Pending | Avg | Win | T1 | Stop | MFE/MAE | Description |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| STRUCTURE_SCORE_GE_10 | SHADOW_BUILDING | 29 | 28 | 0 | 0.3055% | 67.86% | 50.0% | 42.86% | 1.613 | مثبت ولی نیازمند review: structure_score >= 10. |
| HISTORICAL_EDGE_SCORE_GE_1 | SHADOW_BUILDING | 8 | 8 | 0 | -1.2246% | 12.5% | 100.0% | 100.0% | 1.244 | Backtest candidate با stop کمتر: historical_edge_score >= 1. |
| RISK_MEDIUM | SHADOW_BUILDING | 1 | 1 | 0 | 0.5361% | 100.0% | 100.0% | 100.0% | 1.441 | Backtest candidate با sample بیشتر: risk_label = Medium. |
| SCORE_GE_80 | SHADOW_BUILDING | 1 | 1 | 0 | -0.1356% | 0.0% | 0.0% | 0.0% | 0.823 | مثبت کم‌نمونه: score >= 80؛ فقط watchlist تحقیقاتی. |
| REGIME_TRENDING_BEAR__RISK_MEDIUM | SHADOW_BUILDING | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | v6.1 regime proposal: TRENDING_BEAR + risk_label = Medium. |
| REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT | SHADOW_BUILDING | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | v6.1 regime proposal: TRENDING_BEAR + risk_label = Medium + SHORT. |
| REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10 | SHADOW_BUILDING | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | v6.1 regime proposal: TRENDING_BEAR + structure_score >= 10. |
| REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT | SHADOW_BUILDING | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | v6.1 regime proposal: TRENDING_BEAR + structure_score >= 10 + SHORT. |
| VOLUME_SCORE_GE_10 | SHADOW_BUILDING | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | Backtest candidate قوی: volume_score >= 10. |
| DOGE_SHORT_WATCH | SHADOW_BUILDING | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | مثبت کم‌نمونه: DOGE/USDT SHORT. |
| BNB_LONG_SCORE_GE_60 | SHADOW_BUILDING | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | مثبت کم‌نمونه: BNB/USDT LONG + score>=60. |

## Recent Signals
| Gate | Status | Symbol | Side | Score | Return | Candle |
|---|---|---|---|---:|---:|---|
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
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 60 | -0.5316 | 2026-07-21 04:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 65 | -0.9597 | 2026-07-21 12:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 63 | -0.786 | 2026-07-21 16:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 61 | -1.6663 | 2026-07-22 12:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | SHORT | 78 | 1.3158 | 2026-07-23 12:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | SHORT | 54 | 0.9775 | 2026-07-23 16:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | SHORT | 98 | -0.1356 | 2026-07-24 12:00:00 |
| SCORE_GE_80 | EVALUATED | BTC/USDT | SHORT | 98 | -0.1356 | 2026-07-24 12:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 75 | -1.6602 | 2026-07-27 16:00:00 |
| STRUCTURE_SCORE_GE_10 | PARTIAL | BTC/USDT | SHORT | 64 |  | 2026-07-28 12:00:00 |

## Recommendations
- Shadow هنوز در حال ساخت داده است؛ فعال‌ترین gate: STRUCTURE_SCORE_GE_10 | signals=29, evaluated=28.
- برای هر gate حداقل 30 نمونه Forward کامل لازم است.
- Regime Shadow gateهای v6.1 فعال شده‌اند، اما هنوز هیچ تصمیم Forward آن‌ها را پاس نکرده است.
- سه gate پایه که باید زیر نظر بمانند: VOLUME_SCORE_GE_10، RISK_MEDIUM، HISTORICAL_EDGE_SCORE_GE_1.

## Blockers
- No major blocker.

## Safety Notes
- Shadow Gate هیچ Paper Trade و هیچ سفارش واقعی ایجاد نمی‌کند؛ فقط برچسب تحقیقاتی می‌زند.
- Gateهای پایه از Backtest و Gateهای Regime از v6.1 Regime-Gate Matrix آمده‌اند و باید در Forward مستقل تأیید شوند.
- تا وقتی هر gate، مخصوصاً gateهای Regime، حداقل 30 نمونه Forward کامل ندارد، نتیجه آماری قابل اتکا نیست.