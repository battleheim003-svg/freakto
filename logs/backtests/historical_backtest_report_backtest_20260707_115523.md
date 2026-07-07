# Freakto Historical Backfill & Backtest Report v5.3

## Run
- Run ID: `backtest_20260707_115523`
- Started UTC: `2026-07-07T11:55:23.687436+00:00`
- Finished UTC: `2026-07-07T11:55:57.193569+00:00`
- OK: `True`
- Symbols: `1/1`
- Rows written: `12`

## Summary
- Status: `BACKTEST_BUILDING`
- Rows: `12`
- Complete rows: `12`
- Actionable rows: `0`
- Directional samples: `6`
- Directional Win Rate: `66.67%`
- Target 1 Hit Rate: `83.33%`
- Stop Hit Rate: `33.33%`
- Avg 24h Return: `0.1463%`

## By Symbol
| Symbol | Rows | Complete | Dir Samples | Dir Win | T1 Hit | Stop | Avg 24h |
|---|---:|---:|---:|---:|---:|---:|---:|
| BTC/USDT | 12 | 12 | 6 | 66.67% | 83.33% | 33.33% | 0.1463% |

## By Actionability
| Actionability | Rows | Complete | Dir Samples | Dir Win | T1 Hit | Stop | Avg 24h |
|---|---:|---:|---:|---:|---:|---:|---:|
| MONITOR_ONLY | 6 | 6 | 0 | 0.0% | 0.0% | 0.0% | 0.0% |
| NOT_ACTIONABLE | 3 | 3 | 3 | 66.67% | 66.67% | 33.33% | 0.9441% |
| WATCHLIST | 3 | 3 | 3 | 66.67% | 100.0% | 33.33% | -0.6514% |

## Blockers
- Backtest complete samples کمتر از 100 است: 12
- Directional backtest samples کمتر از 30 است: 6

## Safety Notes
- BACKTEST با FORWARD_TEST یکی نیست؛ خروجی تاریخی فقط برای تحقیق و اعتبارسنجی اولیه است.
- برای جلوگیری از اعتماد کاذب، Live/Paper جدی فقط بعد از Forward/Paper کافی مجاز است.