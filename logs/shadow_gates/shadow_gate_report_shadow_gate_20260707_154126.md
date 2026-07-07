# Freakto Candidate Gate Shadow Validator v5.3.3

## Summary
- status: `SHADOW_COLLECTING_FORWARD_DATA`
- generated_utc: `2026-07-07T15:41:26.459916+00:00`
- horizon: `24h`
- min_samples: `30`
- decisions: `41`
- directional_decisions: `27`
- gates_tracked: `7`
- shadow_signals: `16`
- evaluated_shadow_samples: `14`
- pending_shadow_samples: `2`
- confirmed_candidates: `0`
- building_candidates: `7`
- rejected_candidates: `0`

## Gate Metrics
| Gate | Verdict | Signals | Evaluated | Pending | Avg | Win | T1 | Stop | MFE/MAE | Description |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| STRUCTURE_SCORE_GE_10 | SHADOW_BUILDING | 14 | 14 | 0 | 0.8834% | 100.0% | 100.0% | 85.71% | 1.785 | مثبت ولی نیازمند review: structure_score >= 10. |
| VOLUME_SCORE_GE_10 | SHADOW_BUILDING | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | Backtest candidate قوی: volume_score >= 10. |
| RISK_MEDIUM | SHADOW_BUILDING | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | Backtest candidate با sample بیشتر: risk_label = Medium. |
| HISTORICAL_EDGE_SCORE_GE_1 | SHADOW_BUILDING | 2 | 0 | 2 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | Backtest candidate با stop کمتر: historical_edge_score >= 1. |
| SCORE_GE_80 | SHADOW_BUILDING | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | مثبت کم‌نمونه: score >= 80؛ فقط watchlist تحقیقاتی. |
| DOGE_SHORT_WATCH | SHADOW_BUILDING | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | مثبت کم‌نمونه: DOGE/USDT SHORT. |
| BNB_LONG_SCORE_GE_60 | SHADOW_BUILDING | 0 | 0 | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0 | مثبت کم‌نمونه: BNB/USDT LONG + score>=60. |

## Recent Signals
| Gate | Status | Symbol | Side | Score | Return | Candle |
|---|---|---|---|---:|---:|---|
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 63 | 1.7091 | 2026-07-03 16:00:00 |
| STRUCTURE_SCORE_GE_10 | EVALUATED | BTC/USDT | LONG | 63 | 1.7343 | 2026-07-03 16:00:00 |
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
| HISTORICAL_EDGE_SCORE_GE_1 | PENDING | BTC/USDT | LONG | 49 |  | 2026-07-07 12:00:00 |
| HISTORICAL_EDGE_SCORE_GE_1 | PENDING | BTC/USDT | LONG | 66 |  | 2026-07-07 12:00:00 |

## Recommendations
- Shadow هنوز در حال ساخت داده است؛ فعال‌ترین gate: STRUCTURE_SCORE_GE_10 | signals=14, evaluated=14.
- برای هر gate حداقل 30 نمونه Forward کامل لازم است.
- سه gate اصلی که باید زیر نظر بمانند: VOLUME_SCORE_GE_10، RISK_MEDIUM، HISTORICAL_EDGE_SCORE_GE_1.

## Blockers
- کل نمونه‌های ارزیابی‌شده Shadow کمتر از 30 است: 14

## Safety Notes
- Shadow Gate هیچ Paper Trade و هیچ سفارش واقعی ایجاد نمی‌کند؛ فقط برچسب تحقیقاتی می‌زند.
- Gateها از خروجی Backtest آمده‌اند و باید در Forward مستقل تأیید شوند.
- تا وقتی هر gate حداقل 30 نمونه Forward کامل ندارد، نتیجه آماری قابل اتکا نیست.