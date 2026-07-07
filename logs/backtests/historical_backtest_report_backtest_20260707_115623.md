# Freakto Historical Backfill & Backtest Report v5.3

## Run
- Run ID: `backtest_20260707_115623`
- Started UTC: `2026-07-07T11:56:23.845732+00:00`
- Finished UTC: `2026-07-07T11:57:21.792295+00:00`
- OK: `True`
- Symbols: `6/6`
- Rows written: `642`

## Summary
- Status: `BACKTEST_BUILDING`
- Rows: `642`
- Complete rows: `642`
- Actionable rows: `46`
- Directional samples: `289`
- Directional Win Rate: `45.67%`
- Target 1 Hit Rate: `47.40%`
- Stop Hit Rate: `47.40%`
- Avg 24h Return: `-0.2592%`

## By Symbol
| Symbol | Rows | Complete | Dir Samples | Dir Win | T1 Hit | Stop | Avg 24h |
|---|---:|---:|---:|---:|---:|---:|---:|
| BNB/USDT | 107 | 107 | 50 | 46.0% | 50.0% | 48.0% | -0.161% |
| BTC/USDT | 107 | 107 | 49 | 46.94% | 36.73% | 46.94% | -0.3222% |
| DOGE/USDT | 107 | 107 | 48 | 39.58% | 50.0% | 41.67% | -0.1383% |
| ETH/USDT | 107 | 107 | 48 | 45.83% | 50.0% | 43.75% | -0.3824% |
| SOL/USDT | 107 | 107 | 53 | 45.28% | 47.17% | 52.83% | -0.3751% |
| XRP/USDT | 107 | 107 | 41 | 51.22% | 51.22% | 51.22% | -0.151% |

## By Actionability
| Actionability | Rows | Complete | Dir Samples | Dir Win | T1 Hit | Stop | Avg 24h |
|---|---:|---:|---:|---:|---:|---:|---:|
| MONITOR_ONLY | 353 | 353 | 0 | 0.0% | 0.0% | 0.0% | 0.0% |
| WATCHLIST | 173 | 173 | 173 | 46.24% | 50.29% | 48.55% | -0.2335% |
| NOT_ACTIONABLE | 70 | 70 | 70 | 42.86% | 41.43% | 38.57% | -0.3993% |
| ACTIONABLE | 46 | 46 | 46 | 47.83% | 45.65% | 56.52% | -0.1425% |

## Blockers
- میانگین بازده 24h در Backtest مثبت نیست.

## Safety Notes
- BACKTEST با FORWARD_TEST یکی نیست؛ خروجی تاریخی فقط برای تحقیق و اعتبارسنجی اولیه است.
- برای جلوگیری از اعتماد کاذب، Live/Paper جدی فقط بعد از Forward/Paper کافی مجاز است.