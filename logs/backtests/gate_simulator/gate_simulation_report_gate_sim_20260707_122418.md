# Freakto Backtest Gate Simulator v5.3.2

## Summary
- Status: `GATE_RESEARCH_ONLY`
- Generated UTC: `2026-07-07T12:24:18.663653+00:00`
- Horizon: `4h`
- Min Samples: `30`
- Rows / Complete: `654/654`
- Directional Samples: `295`
- Baseline Avg Return: `-0.1851%`
- Baseline Win Rate: `36.95%`
- Baseline T1 / Stop: `48.14% / 47.12%`
- Gates Tested: `139`
- Positive Gates: `0`
- Research Candidates: `0`
- Small Positive Gates: `5`

## Top Gates
| Gate | Verdict | Family | Samples | Avg | Win | T1 | Stop | MFE/MAE | Research Score |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| SYMBOL_SIDE_SCORE_GE_60_DOGEUSDT_SHORT | SMALL_SAMPLE_POSITIVE | symbol_side_score | 12 | 0.1571% | 66.67% | 50.0% | 33.33% | 1.03 | 0.5191 |
| SYMBOL_SIDE_SCORE_GE_60_BNBUSDT_LONG | SMALL_SAMPLE_POSITIVE | symbol_side_score | 11 | 0.1679% | 54.55% | 72.73% | 54.55% | 1.374 | 0.3891 |
| SYMBOL_SIDE_DOGEUSDT_SHORT | SMALL_SAMPLE_POSITIVE | symbol_side | 25 | 0.039% | 56.0% | 52.0% | 32.0% | 1.207 | 0.3463 |
| REGIME_UNKNOWN | SMALL_SAMPLE_POSITIVE | regime | 10 | 0.0242% | 50.0% | 20.0% | 40.0% | 0.687 | -0.2173 |
| REGIME_SIDEWAYS | SMALL_SAMPLE_POSITIVE | regime | 10 | 0.0185% | 30.0% | 50.0% | 60.0% | 0.876 | -0.4017 |
| SYMBOL_SIDE_BNBUSDT_LONG | NEAR_BREAKEVEN_WATCH | symbol_side | 30 | -0.0022% | 50.0% | 56.67% | 50.0% | 0.972 | 0.0617 |
| SYMBOL_WATCH_OR_ACTIONABLE_BNBUSDT | NEAR_BREAKEVEN_WATCH | symbol_actionability | 36 | -0.0496% | 52.78% | 52.78% | 52.78% | 1.001 | -0.0078 |
| SYMBOL_BNBUSDT | NEAR_BREAKEVEN_WATCH | symbol | 50 | -0.0871% | 52.0% | 50.0% | 48.0% | 0.938 | -0.0433 |
| SYMBOL_DOGEUSDT | NEAR_BREAKEVEN_WATCH | symbol | 48 | -0.0738% | 43.75% | 50.0% | 41.67% | 1.053 | -0.079 |
| SYMBOL_WATCH_OR_ACTIONABLE_DOGEUSDT | NEAR_BREAKEVEN_WATCH | symbol_actionability | 38 | -0.0975% | 42.11% | 50.0% | 42.11% | 1.077 | -0.1293 |
| REGIME_TRENDING_BEAR | REJECT_NEGATIVE_EDGE | regime | 138 | -0.136% | 43.48% | 50.0% | 44.2% | 0.951 | -0.1807 |
| WATCH_OR_ACTIONABLE_SHORT | REJECT_NEGATIVE_EDGE | actionability_side | 105 | -0.1452% | 43.81% | 52.38% | 49.52% | 0.979 | -0.2115 |
| SHORT_ONLY | REJECT_NEGATIVE_EDGE | side | 145 | -0.1484% | 42.76% | 48.97% | 44.83% | 0.912 | -0.2244 |
| SCORE_GE_50_SHORT | REJECT_NEGATIVE_EDGE | score_side | 145 | -0.1484% | 42.76% | 48.97% | 44.83% | 0.912 | -0.2244 |
| SHORT_SCORE_GE_50 | REJECT_NEGATIVE_EDGE | component | 145 | -0.1484% | 42.76% | 48.97% | 44.83% | 0.912 | -0.2244 |
| SCORE_BUCKET_50_59 | REJECT_NEGATIVE_EDGE | score_bucket | 141 | -0.1436% | 41.13% | 47.52% | 44.68% | 0.882 | -0.26 |
| CONFIDENCE_MEDIUM | REJECT_NEGATIVE_EDGE | confidence | 158 | -0.1013% | 38.61% | 50.0% | 49.37% | 0.976 | -0.2682 |
| WATCHLIST_ONLY | REJECT_NEGATIVE_EDGE | actionability | 176 | -0.1222% | 38.07% | 51.14% | 48.3% | 0.949 | -0.2778 |
| SYMBOL_WATCH_OR_ACTIONABLE_ETHUSDT | REJECT_NEGATIVE_EDGE | symbol_actionability | 36 | -0.1389% | 36.11% | 55.56% | 47.22% | 0.848 | -0.279 |
| HISTORICAL_EDGE_SCORE_GE_1 | REJECT_NEGATIVE_EDGE | component | 40 | -0.1534% | 32.5% | 47.5% | 35.0% | 1.066 | -0.2843 |

## All Gate Results
| Gate | Verdict | Family | Samples | Share | Avg | Median | Best | Worst | Win | T1 | Stop | MFE | MAE | MFE/MAE | Description |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| SYMBOL_SIDE_SCORE_GE_60_DOGEUSDT_SHORT | SMALL_SAMPLE_POSITIVE | symbol_side_score | 12 | 4.07% | 0.1571% | 0.2332% | 1.5451% | -1.4176% | 66.67% | 50.0% | 33.33% | 2.4333% | -2.3617% | 1.03 | DOGE/USDT + SHORT + score >= 60. |
| SYMBOL_SIDE_SCORE_GE_60_BNBUSDT_LONG | SMALL_SAMPLE_POSITIVE | symbol_side_score | 11 | 3.73% | 0.1679% | 0.0474% | 1.9275% | -0.9525% | 54.55% | 72.73% | 54.55% | 2.1094% | -1.5351% | 1.374 | BNB/USDT + LONG + score >= 60. |
| SYMBOL_SIDE_DOGEUSDT_SHORT | SMALL_SAMPLE_POSITIVE | symbol_side | 25 | 8.47% | 0.039% | 0.132% | 2.9224% | -2.7253% | 56.0% | 52.0% | 32.0% | 2.6864% | -2.2261% | 1.207 | DOGE/USDT فقط SHORT. |
| REGIME_UNKNOWN | SMALL_SAMPLE_POSITIVE | regime | 10 | 3.39% | 0.0242% | -0.0291% | 1.0741% | -0.9495% | 50.0% | 20.0% | 40.0% | 1.5277% | -2.2235% | 0.687 | فقط regime=UNKNOWN. |
| REGIME_SIDEWAYS | SMALL_SAMPLE_POSITIVE | regime | 10 | 3.39% | 0.0185% | -0.6956% | 4.8272% | -1.7382% | 30.0% | 50.0% | 60.0% | 2.0087% | -2.2926% | 0.876 | فقط regime=SIDEWAYS. |
| SYMBOL_SIDE_BNBUSDT_LONG | NEAR_BREAKEVEN_WATCH | symbol_side | 30 | 10.17% | -0.0022% | 0.0104% | 1.9275% | -1.051% | 50.0% | 56.67% | 50.0% | 1.6431% | -1.6906% | 0.972 | BNB/USDT فقط LONG. |
| SYMBOL_WATCH_OR_ACTIONABLE_BNBUSDT | NEAR_BREAKEVEN_WATCH | symbol_actionability | 36 | 12.2% | -0.0496% | 0.0493% | 1.9275% | -1.6571% | 52.78% | 52.78% | 52.78% | 1.7171% | -1.7145% | 1.001 | BNB/USDT + WATCHLIST/ACTIONABLE. |
| SYMBOL_BNBUSDT | NEAR_BREAKEVEN_WATCH | symbol | 50 | 16.95% | -0.0871% | 0.0364% | 1.9275% | -1.6571% | 52.0% | 50.0% | 48.0% | 1.6255% | -1.7328% | 0.938 | فقط نماد BNB/USDT. |
| SYMBOL_DOGEUSDT | NEAR_BREAKEVEN_WATCH | symbol | 48 | 16.27% | -0.0738% | -0.052% | 2.9224% | -2.7253% | 43.75% | 50.0% | 41.67% | 2.555% | -2.4261% | 1.053 | فقط نماد DOGE/USDT. |
| SYMBOL_WATCH_OR_ACTIONABLE_DOGEUSDT | NEAR_BREAKEVEN_WATCH | symbol_actionability | 38 | 12.88% | -0.0975% | -0.052% | 2.894% | -2.7253% | 42.11% | 50.0% | 42.11% | 2.6617% | -2.4716% | 1.077 | DOGE/USDT + WATCHLIST/ACTIONABLE. |
| REGIME_TRENDING_BEAR | REJECT_NEGATIVE_EDGE | regime | 138 | 46.78% | -0.136% | -0.049% | 2.9224% | -2.9327% | 43.48% | 50.0% | 44.2% | 2.1768% | -2.2881% | 0.951 | فقط regime=TRENDING_BEAR. |
| WATCH_OR_ACTIONABLE_SHORT | REJECT_NEGATIVE_EDGE | actionability_side | 105 | 35.59% | -0.1452% | -0.0393% | 2.7268% | -2.9327% | 43.81% | 52.38% | 49.52% | 2.3087% | -2.3579% | 0.979 | WATCHLIST/ACTIONABLE فقط سمت SHORT. |
| SHORT_ONLY | REJECT_NEGATIVE_EDGE | side | 145 | 49.15% | -0.1484% | -0.0531% | 2.9224% | -2.9327% | 42.76% | 48.97% | 44.83% | 2.13% | -2.3363% | 0.912 | فقط معاملات SHORT. |
| SCORE_GE_50_SHORT | REJECT_NEGATIVE_EDGE | score_side | 145 | 49.15% | -0.1484% | -0.0531% | 2.9224% | -2.9327% | 42.76% | 48.97% | 44.83% | 2.13% | -2.3363% | 0.912 | score >= 50 + SHORT. |
| SHORT_SCORE_GE_50 | REJECT_NEGATIVE_EDGE | component | 145 | 49.15% | -0.1484% | -0.0531% | 2.9224% | -2.9327% | 42.76% | 48.97% | 44.83% | 2.13% | -2.3363% | 0.912 | short_score >= 50. |
| SCORE_BUCKET_50_59 | REJECT_NEGATIVE_EDGE | score_bucket | 141 | 47.8% | -0.1436% | -0.0985% | 4.8272% | -2.9412% | 41.13% | 47.52% | 44.68% | 1.9169% | -2.1737% | 0.882 | score 50-59 |
| CONFIDENCE_MEDIUM | REJECT_NEGATIVE_EDGE | confidence | 158 | 53.56% | -0.1013% | -0.1148% | 4.8272% | -2.7253% | 38.61% | 50.0% | 49.37% | 2.1397% | -2.193% | 0.976 | فقط confidence=Medium. |
| WATCHLIST_ONLY | REJECT_NEGATIVE_EDGE | actionability | 176 | 59.66% | -0.1222% | -0.1287% | 4.8272% | -2.9327% | 38.07% | 51.14% | 48.3% | 2.0962% | -2.2095% | 0.949 | فقط WATCHLIST برای مقایسه با ACTIONABLE. |
| SYMBOL_WATCH_OR_ACTIONABLE_ETHUSDT | REJECT_NEGATIVE_EDGE | symbol_actionability | 36 | 12.2% | -0.1389% | -0.1428% | 2.7268% | -2.3399% | 36.11% | 55.56% | 47.22% | 2.0406% | -2.4071% | 0.848 | ETH/USDT + WATCHLIST/ACTIONABLE. |
| HISTORICAL_EDGE_SCORE_GE_1 | REJECT_NEGATIVE_EDGE | component | 40 | 13.56% | -0.1534% | -0.2067% | 2.0053% | -1.8426% | 32.5% | 47.5% | 35.0% | 1.6298% | -1.5296% | 1.066 | historical_edge_score >= 1. |
| RISK_LOW | REJECT_NEGATIVE_EDGE | risk | 211 | 71.53% | -0.0898% | -0.1181% | 4.8272% | -2.6468% | 40.28% | 45.97% | 49.29% | 1.8012% | -2.1829% | 0.825 | فقط risk_label=Low. |
| SCORE_GE_60_SHORT | REJECT_NEGATIVE_EDGE | score_side | 71 | 24.07% | -0.1622% | -0.0241% | 2.7268% | -2.9327% | 42.25% | 49.3% | 50.7% | 2.1773% | -2.3463% | 0.928 | score >= 60 + SHORT. |
| SHORT_SCORE_GE_60 | REJECT_NEGATIVE_EDGE | component | 71 | 24.07% | -0.1622% | -0.0241% | 2.7268% | -2.9327% | 42.25% | 49.3% | 50.7% | 2.1773% | -2.3463% | 0.928 | short_score >= 60. |
| NOT_ACTIONABLE_ONLY | REJECT_NEGATIVE_EDGE | actionability | 73 | 24.75% | -0.1944% | -0.1085% | 2.9224% | -2.9412% | 41.1% | 42.47% | 38.36% | 1.5825% | -2.111% | 0.75 | NOT_ACTIONABLE فقط برای کنترل منفی؛ معمولاً نباید candidate شود. |
| CONFIDENCE_LOW | REJECT_NEGATIVE_EDGE | confidence | 73 | 24.75% | -0.1944% | -0.1085% | 2.9224% | -2.9412% | 41.1% | 42.47% | 38.36% | 1.5825% | -2.111% | 0.75 | فقط confidence=Low. |
| SYMBOL_ETHUSDT | REJECT_NEGATIVE_EDGE | symbol | 48 | 16.27% | -0.1386% | -0.1137% | 2.7268% | -2.3399% | 35.42% | 50.0% | 43.75% | 1.8564% | -2.3447% | 0.792 | فقط نماد ETH/USDT. |
| SCORE_BUCKET_60_69 | REJECT_NEGATIVE_EDGE | score_bucket | 90 | 30.51% | -0.1105% | -0.1585% | 2.894% | -2.6468% | 36.67% | 47.78% | 47.78% | 2.0368% | -2.1567% | 0.944 | score 60-69 |
| VOLUME_SCORE_GE_10 | REJECT_NEGATIVE_EDGE | component | 34 | 11.53% | -0.2745% | -0.5034% | 4.8272% | -2.9327% | 23.53% | 76.47% | 44.12% | 2.7339% | -2.0804% | 1.314 | volume_score >= 10. |
| MOMENTUM_SCORE_GE_15 | REJECT_NEGATIVE_EDGE | component | 289 | 97.97% | -0.1827% | -0.1675% | 4.8272% | -2.9412% | 37.02% | 48.44% | 47.06% | 1.9509% | -2.2088% | 0.883 | momentum_score >= 15. |
| TREND_SCORE_GE_10 | REJECT_NEGATIVE_EDGE | component | 293 | 99.32% | -0.1815% | -0.1675% | 4.8272% | -2.9412% | 37.2% | 48.12% | 47.1% | 1.9213% | -2.1882% | 0.878 | trend_score >= 10. |
| BASELINE_DIRECTIONAL | REJECT_NEGATIVE_EDGE | baseline | 295 | 100.0% | -0.1851% | -0.1713% | 4.8272% | -2.9412% | 36.95% | 48.14% | 47.12% | 1.9292% | -2.2058% | 0.875 | تمام تصمیم‌های جهت‌دار کامل؛ فقط برای مقایسه. |
| SCORE_GE_50 | REJECT_NEGATIVE_EDGE | score | 295 | 100.0% | -0.1851% | -0.1713% | 4.8272% | -2.9412% | 36.95% | 48.14% | 47.12% | 1.9292% | -2.2058% | 0.875 | score >= 50 |
| TREND_SCORE_GE_5 | REJECT_NEGATIVE_EDGE | component | 295 | 100.0% | -0.1851% | -0.1713% | 4.8272% | -2.9412% | 36.95% | 48.14% | 47.12% | 1.9292% | -2.2058% | 0.875 | trend_score >= 5. |
| MOMENTUM_SCORE_GE_5 | REJECT_NEGATIVE_EDGE | component | 295 | 100.0% | -0.1851% | -0.1713% | 4.8272% | -2.9412% | 36.95% | 48.14% | 47.12% | 1.9292% | -2.2058% | 0.875 | momentum_score >= 5. |
| MOMENTUM_SCORE_GE_10 | REJECT_NEGATIVE_EDGE | component | 295 | 100.0% | -0.1851% | -0.1713% | 4.8272% | -2.9412% | 36.95% | 48.14% | 47.12% | 1.9292% | -2.2058% | 0.875 | momentum_score >= 10. |
| TREND_SCORE_GE_15 | REJECT_NEGATIVE_EDGE | component | 292 | 98.98% | -0.1867% | -0.1694% | 4.8272% | -2.9412% | 36.99% | 47.95% | 47.26% | 1.9192% | -2.1949% | 0.874 | trend_score >= 15. |
| SYMBOL_BTCUSDT | REJECT_NEGATIVE_EDGE | symbol | 55 | 18.64% | -0.1049% | -0.1653% | 2.0053% | -1.8426% | 34.55% | 41.82% | 45.45% | 1.4701% | -1.7444% | 0.843 | فقط نماد BTC/USDT. |
| SYMBOL_SIDE_BTCUSDT_LONG | REJECT_NEGATIVE_EDGE | symbol_side | 36 | 12.2% | -0.1184% | -0.2423% | 1.4814% | -1.3798% | 30.56% | 44.44% | 41.67% | 1.2707% | -1.5117% | 0.841 | BTC/USDT فقط LONG. |
| WATCHLIST_OR_ACTIONABLE | REJECT_NEGATIVE_EDGE | actionability | 222 | 75.25% | -0.1821% | -0.1864% | 4.8272% | -2.9327% | 35.59% | 50.0% | 50.0% | 2.0431% | -2.237% | 0.913 | WATCHLIST یا ACTIONABLE؛ گیت نیمه‌محافظه‌کار. |
| STRUCTURE_SCORE_GE_5 | REJECT_NEGATIVE_EDGE | component | 240 | 81.36% | -0.2236% | -0.1762% | 2.9224% | -2.9412% | 35.0% | 48.75% | 46.67% | 1.9543% | -2.1468% | 0.91 | structure_score >= 5. |
| HISTORICAL_EDGE_SCORE_GE_5 | REJECT_NEGATIVE_EDGE | component | 30 | 10.17% | -0.1585% | -0.2067% | 1.4814% | -1.3798% | 30.0% | 40.0% | 36.67% | 1.2445% | -1.5062% | 0.826 | historical_edge_score >= 5. |
| SYMBOL_WATCH_OR_ACTIONABLE_SOLUSDT | REJECT_NEGATIVE_EDGE | symbol_actionability | 40 | 13.56% | -0.2253% | -0.1827% | 4.8272% | -2.9327% | 35.0% | 52.5% | 52.5% | 2.3949% | -2.5927% | 0.924 | SOL/USDT + WATCHLIST/ACTIONABLE. |
| RISK_MEDIUM | REJECT_NEGATIVE_EDGE | risk | 76 | 25.76% | -0.32% | -0.2599% | 2.7268% | -2.9327% | 31.58% | 53.95% | 42.11% | 2.201% | -2.1233% | 1.037 | فقط risk_label=Medium. |
| SCORE_GE_60 | REJECT_NEGATIVE_EDGE | score | 154 | 52.2% | -0.2232% | -0.2459% | 2.894% | -2.9327% | 33.12% | 48.7% | 49.35% | 1.9403% | -2.2353% | 0.868 | score >= 60 |
| VOLUME_SCORE_GE_5 | REJECT_NEGATIVE_EDGE | component | 142 | 48.14% | -0.2848% | -0.2803% | 4.8272% | -2.9412% | 32.39% | 50.7% | 47.18% | 2.1814% | -2.4578% | 0.888 | volume_score >= 5. |
| LONG_ONLY | REJECT_NEGATIVE_EDGE | side | 150 | 50.85% | -0.2207% | -0.2492% | 4.8272% | -2.9412% | 31.33% | 47.33% | 49.33% | 1.735% | -2.0798% | 0.834 | فقط معاملات LONG. |
| SCORE_GE_50_LONG | REJECT_NEGATIVE_EDGE | score_side | 150 | 50.85% | -0.2207% | -0.2492% | 4.8272% | -2.9412% | 31.33% | 47.33% | 49.33% | 1.735% | -2.0798% | 0.834 | score >= 50 + LONG. |
| LONG_SCORE_GE_50 | REJECT_NEGATIVE_EDGE | component | 150 | 50.85% | -0.2207% | -0.2492% | 4.8272% | -2.9412% | 31.33% | 47.33% | 49.33% | 1.735% | -2.0798% | 0.834 | long_score >= 50. |
| WATCH_OR_ACTIONABLE_LONG | REJECT_NEGATIVE_EDGE | actionability_side | 117 | 39.66% | -0.2152% | -0.2628% | 4.8272% | -2.6468% | 28.21% | 47.86% | 50.43% | 1.8048% | -2.1285% | 0.848 | WATCHLIST/ACTIONABLE فقط سمت LONG. |
| SYMBOL_WATCH_OR_ACTIONABLE_BTCUSDT | REJECT_NEGATIVE_EDGE | symbol_actionability | 40 | 13.56% | -0.1759% | -0.256% | 2.0053% | -1.8426% | 27.5% | 42.5% | 50.0% | 1.5604% | -1.8953% | 0.823 | BTC/USDT + WATCHLIST/ACTIONABLE. |
| REGIME_TRENDING_BULL | REJECT_NEGATIVE_EDGE | regime | 136 | 46.1% | -0.2681% | -0.2547% | 2.894% | -2.9412% | 29.41% | 48.53% | 50.0% | 1.7052% | -2.1211% | 0.804 | فقط regime=TRENDING_BULL. |
| STRUCTURE_SCORE_GE_10 | REJECT_NEGATIVE_EDGE | component | 86 | 29.15% | -0.3977% | -0.3906% | 2.7268% | -2.9327% | 27.91% | 53.49% | 44.19% | 2.0978% | -2.1147% | 0.992 | structure_score >= 10. |
| SCORE_GE_60_LONG | REJECT_NEGATIVE_EDGE | score_side | 83 | 28.14% | -0.2753% | -0.2718% | 2.894% | -2.6468% | 25.3% | 48.19% | 48.19% | 1.7376% | -2.1403% | 0.812 | score >= 60 + LONG. |
| LONG_SCORE_GE_60 | REJECT_NEGATIVE_EDGE | component | 83 | 28.14% | -0.2753% | -0.2718% | 2.894% | -2.6468% | 25.3% | 48.19% | 48.19% | 1.7376% | -2.1403% | 0.812 | long_score >= 60. |
| SYMBOL_SOLUSDT | REJECT_NEGATIVE_EDGE | symbol | 53 | 17.97% | -0.325% | -0.3153% | 4.8272% | -2.9327% | 30.19% | 47.17% | 52.83% | 2.2285% | -2.7729% | 0.804 | فقط نماد SOL/USDT. |
| SCORE_GE_70_LONG | REJECT_NEGATIVE_EDGE | score_side | 43 | 14.58% | -0.3187% | -0.2718% | 1.9275% | -1.7141% | 25.58% | 51.16% | 53.49% | 1.6671% | -2.3532% | 0.708 | score >= 70 + LONG. |
| LONG_SCORE_GE_70 | REJECT_NEGATIVE_EDGE | component | 43 | 14.58% | -0.3187% | -0.2718% | 1.9275% | -1.7141% | 25.58% | 51.16% | 53.49% | 1.6671% | -2.3532% | 0.708 | long_score >= 70. |
| SCORE_GE_70 | REJECT_NEGATIVE_EDGE | score | 64 | 21.69% | -0.3816% | -0.3474% | 1.9275% | -2.9327% | 28.12% | 50.0% | 51.56% | 1.8048% | -2.3458% | 0.769 | score >= 70 |
| CONFIDENCE_MEDIUM-HIGH | REJECT_NEGATIVE_EDGE | confidence | 57 | 19.32% | -0.4108% | -0.3756% | 1.9275% | -2.9327% | 28.07% | 50.88% | 50.88% | 1.8206% | -2.3836% | 0.764 | فقط confidence=Medium-High. |
| SYMBOL_XRPUSDT | REJECT_NEGATIVE_EDGE | symbol | 41 | 13.9% | -0.4162% | -0.4399% | 1.7921% | -2.9412% | 24.39% | 51.22% | 51.22% | 1.8807% | -2.2483% | 0.836 | فقط نماد XRP/USDT. |
| SCORE_BUCKET_70_79 | REJECT_NEGATIVE_EDGE | score_bucket | 44 | 14.92% | -0.4371% | -0.3906% | 1.4814% | -2.9327% | 29.55% | 45.45% | 52.27% | 1.7045% | -2.4927% | 0.684 | score 70-79 |
| ACTIONABLE_ONLY | REJECT_NEGATIVE_EDGE | actionability | 46 | 15.59% | -0.4113% | -0.4584% | 1.9275% | -1.7141% | 26.09% | 45.65% | 56.52% | 1.8402% | -2.3423% | 0.786 | فقط تصمیم‌هایی که موتور ACTIONABLE کرده است. |
| ACTIONABLE_SCORE_GE_50 | REJECT_NEGATIVE_EDGE | actionability_score | 46 | 15.59% | -0.4113% | -0.4584% | 1.9275% | -1.7141% | 26.09% | 45.65% | 56.52% | 1.8402% | -2.3423% | 0.786 | ACTIONABLE + score >= 50. |
| ACTIONABLE_SCORE_GE_60 | REJECT_NEGATIVE_EDGE | actionability_score | 46 | 15.59% | -0.4113% | -0.4584% | 1.9275% | -1.7141% | 26.09% | 45.65% | 56.52% | 1.8402% | -2.3423% | 0.786 | ACTIONABLE + score >= 60. |
| ACTIONABLE_SCORE_GE_70 | REJECT_NEGATIVE_EDGE | actionability_score | 46 | 15.59% | -0.4113% | -0.4584% | 1.9275% | -1.7141% | 26.09% | 45.65% | 56.52% | 1.8402% | -2.3423% | 0.786 | ACTIONABLE + score >= 70. |
| QUALITY_CORE_SCORE60_ACTIONABLE | REJECT_NEGATIVE_EDGE | composite | 46 | 15.59% | -0.4113% | -0.4584% | 1.9275% | -1.7141% | 26.09% | 45.65% | 56.52% | 1.8402% | -2.3423% | 0.786 | ACTIONABLE + score>=60 + risk not High. |
| SYMBOL_WATCH_OR_ACTIONABLE_XRPUSDT | REJECT_NEGATIVE_EDGE | symbol_actionability | 32 | 10.85% | -0.4339% | -0.4759% | 1.7329% | -2.0103% | 18.75% | 46.88% | 56.25% | 1.8419% | -2.3376% | 0.788 | XRP/USDT + WATCHLIST/ACTIONABLE. |
| ACTIONABLE_LONG | REJECT_NEGATIVE_EDGE | actionability_side | 30 | 10.17% | -0.4473% | -0.4894% | 1.9275% | -1.7141% | 20.0% | 50.0% | 60.0% | 1.8006% | -2.4222% | 0.743 | ACTIONABLE فقط سمت LONG. |
| ACTIONABLE_SCORE_GE_50_LONG | REJECT_NEGATIVE_EDGE | actionability_score_side | 30 | 10.17% | -0.4473% | -0.4894% | 1.9275% | -1.7141% | 20.0% | 50.0% | 60.0% | 1.8006% | -2.4222% | 0.743 | ACTIONABLE + score >= 50 + LONG. |
| ACTIONABLE_SCORE_GE_60_LONG | REJECT_NEGATIVE_EDGE | actionability_score_side | 30 | 10.17% | -0.4473% | -0.4894% | 1.9275% | -1.7141% | 20.0% | 50.0% | 60.0% | 1.8006% | -2.4222% | 0.743 | ACTIONABLE + score >= 60 + LONG. |
| ACTIONABLE_SCORE_GE_70_LONG | REJECT_NEGATIVE_EDGE | actionability_score_side | 30 | 10.17% | -0.4473% | -0.4894% | 1.9275% | -1.7141% | 20.0% | 50.0% | 60.0% | 1.8006% | -2.4222% | 0.743 | ACTIONABLE + score >= 70 + LONG. |
| LONG_SCORE60_ACTIONABLE | REJECT_NEGATIVE_EDGE | composite | 30 | 10.17% | -0.4473% | -0.4894% | 1.9275% | -1.7141% | 20.0% | 50.0% | 60.0% | 1.8006% | -2.4222% | 0.743 | LONG + ACTIONABLE + score>=60. |
| SYMBOL_SIDE_SCORE_GE_60_BNBUSDT_SHORT | REJECT_INSUFFICIENT_SAMPLE | symbol_side_score | 11 | 3.73% | -0.1935% | 0.0511% | 0.3837% | -1.6571% | 54.55% | 45.45% | 54.55% | 1.9282% | -1.7658% | 1.092 | BNB/USDT + SHORT + score >= 60. |
| SYMBOL_SIDE_SCORE_GE_60_SOLUSDT_SHORT | REJECT_INSUFFICIENT_SAMPLE | symbol_side_score | 13 | 4.41% | -0.1319% | -0.0241% | 1.7755% | -2.9327% | 46.15% | 53.85% | 53.85% | 2.5528% | -2.6822% | 0.952 | SOL/USDT + SHORT + score >= 60. |
| SYMBOL_SIDE_BNBUSDT_SHORT | REJECT_INSUFFICIENT_SAMPLE | symbol_side | 20 | 6.78% | -0.2145% | 0.0382% | 0.6813% | -1.6571% | 55.0% | 40.0% | 45.0% | 1.5992% | -1.7962% | 0.89 | BNB/USDT فقط SHORT. |
| SYMBOL_SIDE_ETHUSDT_SHORT | REJECT_INSUFFICIENT_SAMPLE | symbol_side | 28 | 9.49% | -0.0507% | -0.0993% | 2.7268% | -2.3399% | 35.71% | 50.0% | 39.29% | 2.007% | -2.3344% | 0.86 | ETH/USDT فقط SHORT. |
| SYMBOL_SIDE_SCORE_GE_60_DOGEUSDT_LONG | REJECT_INSUFFICIENT_SAMPLE | symbol_side_score | 15 | 5.08% | -0.0916% | -0.2331% | 2.894% | -1.7141% | 40.0% | 46.67% | 46.67% | 2.1405% | -2.5641% | 0.835 | DOGE/USDT + LONG + score >= 60. |
| SYMBOL_SIDE_SCORE_GE_60_ETHUSDT_SHORT | REJECT_INSUFFICIENT_SAMPLE | symbol_side_score | 11 | 3.73% | -0.0079% | -0.0895% | 2.7268% | -2.3399% | 36.36% | 45.45% | 54.55% | 2.358% | -2.6642% | 0.885 | ETH/USDT + SHORT + score >= 60. |
| SYMBOL_SIDE_BTCUSDT_SHORT | REJECT_INSUFFICIENT_SAMPLE | symbol_side | 19 | 6.44% | -0.0794% | -0.0173% | 2.0053% | -1.8426% | 42.11% | 36.84% | 52.63% | 1.8481% | -2.1853% | 0.846 | BTC/USDT فقط SHORT. |
| SYMBOL_SIDE_XRPUSDT_SHORT | REJECT_INSUFFICIENT_SAMPLE | symbol_side | 24 | 8.14% | -0.2579% | -0.2713% | 1.7921% | -2.0103% | 33.33% | 62.5% | 50.0% | 2.0466% | -2.0814% | 0.983 | XRP/USDT فقط SHORT. |
| SYMBOL_SIDE_SCORE_GE_60_XRPUSDT_SHORT | REJECT_INSUFFICIENT_SAMPLE | symbol_side_score | 15 | 5.08% | -0.3156% | -0.4472% | 1.7329% | -1.5204% | 26.67% | 66.67% | 46.67% | 2.2003% | -2.0223% | 1.088 | XRP/USDT + SHORT + score >= 60. |
| SCORE_BUCKET_80_89 | REJECT_INSUFFICIENT_SAMPLE | score_bucket | 19 | 6.44% | -0.2592% | -0.3192% | 1.9275% | -1.6795% | 26.32% | 63.16% | 47.37% | 2.1026% | -2.0101% | 1.046 | score 80-89 |
| SCORE_GE_80_LONG | REJECT_INSUFFICIENT_SAMPLE | score_side | 16 | 5.42% | -0.1488% | -0.2509% | 1.9275% | -1.6795% | 31.25% | 56.25% | 56.25% | 1.8005% | -2.023% | 0.89 | score >= 80 + LONG. |
| SYMBOL_SIDE_SCORE_GE_60_BTCUSDT_LONG | REJECT_INSUFFICIENT_SAMPLE | symbol_side_score | 22 | 7.46% | -0.1366% | -0.256% | 1.4814% | -0.8639% | 22.73% | 45.45% | 36.36% | 1.3381% | -1.5521% | 0.862 | BTC/USDT + LONG + score >= 60. |
| SYMBOL_SIDE_ETHUSDT_LONG | REJECT_INSUFFICIENT_SAMPLE | symbol_side | 20 | 6.78% | -0.2618% | -0.1428% | 0.7287% | -1.532% | 35.0% | 50.0% | 50.0% | 1.6455% | -2.359% | 0.698 | ETH/USDT فقط LONG. |
| SCORE_GE_80 | REJECT_INSUFFICIENT_SAMPLE | score | 20 | 6.78% | -0.2594% | -0.2955% | 1.9275% | -1.6795% | 25.0% | 60.0% | 50.0% | 2.0254% | -2.0227% | 1.001 | score >= 80 |
| QUALITY_CORE_SCORE80_WATCH_OR_ACTIONABLE | REJECT_INSUFFICIENT_SAMPLE | composite | 20 | 6.78% | -0.2594% | -0.2955% | 1.9275% | -1.6795% | 25.0% | 60.0% | 50.0% | 2.0254% | -2.0227% | 1.001 | WATCHLIST/ACTIONABLE + score>=80. |
| SYMBOL_SIDE_DOGEUSDT_LONG | REJECT_INSUFFICIENT_SAMPLE | symbol_side | 23 | 7.8% | -0.1965% | -0.239% | 2.894% | -1.7141% | 30.43% | 47.83% | 52.17% | 2.4122% | -2.6435% | 0.912 | DOGE/USDT فقط LONG. |
| SYMBOL_SIDE_SOLUSDT_SHORT | REJECT_INSUFFICIENT_SAMPLE | symbol_side | 29 | 9.83% | -0.3132% | -0.1907% | 1.7755% | -2.9327% | 37.93% | 48.28% | 51.72% | 2.3891% | -3.1154% | 0.767 | SOL/USDT فقط SHORT. |
| ACTIONABLE_SCORE_GE_80_LONG | REJECT_INSUFFICIENT_SAMPLE | actionability_score_side | 15 | 5.08% | -0.1992% | -0.2628% | 1.9275% | -1.6795% | 26.67% | 53.33% | 60.0% | 1.7859% | -2.1556% | 0.828 | ACTIONABLE + score >= 80 + LONG. |
| ACTIONABLE_SHORT | REJECT_INSUFFICIENT_SAMPLE | actionability_side | 16 | 5.42% | -0.3437% | -0.3888% | 0.4043% | -1.4176% | 37.5% | 37.5% | 50.0% | 1.9146% | -2.1925% | 0.873 | ACTIONABLE فقط سمت SHORT. |
| ACTIONABLE_SCORE_GE_50_SHORT | REJECT_INSUFFICIENT_SAMPLE | actionability_score_side | 16 | 5.42% | -0.3437% | -0.3888% | 0.4043% | -1.4176% | 37.5% | 37.5% | 50.0% | 1.9146% | -2.1925% | 0.873 | ACTIONABLE + score >= 50 + SHORT. |
| ACTIONABLE_SCORE_GE_60_SHORT | REJECT_INSUFFICIENT_SAMPLE | actionability_score_side | 16 | 5.42% | -0.3437% | -0.3888% | 0.4043% | -1.4176% | 37.5% | 37.5% | 50.0% | 1.9146% | -2.1925% | 0.873 | ACTIONABLE + score >= 60 + SHORT. |
| ACTIONABLE_SCORE_GE_70_SHORT | REJECT_INSUFFICIENT_SAMPLE | actionability_score_side | 16 | 5.42% | -0.3437% | -0.3888% | 0.4043% | -1.4176% | 37.5% | 37.5% | 50.0% | 1.9146% | -2.1925% | 0.873 | ACTIONABLE + score >= 70 + SHORT. |
| SHORT_SCORE60_ACTIONABLE | REJECT_INSUFFICIENT_SAMPLE | composite | 16 | 5.42% | -0.3437% | -0.3888% | 0.4043% | -1.4176% | 37.5% | 37.5% | 50.0% | 1.9146% | -2.1925% | 0.873 | SHORT + ACTIONABLE + score>=60. |
| SYMBOL_SIDE_SCORE_GE_60_ETHUSDT_LONG | REJECT_INSUFFICIENT_SAMPLE | symbol_side_score | 11 | 3.73% | -0.3635% | -0.4108% | 0.413% | -1.3422% | 27.27% | 45.45% | 45.45% | 1.7215% | -2.3947% | 0.719 | ETH/USDT + LONG + score >= 60. |
| ACTIONABLE_SCORE_GE_80 | REJECT_INSUFFICIENT_SAMPLE | actionability_score | 18 | 6.1% | -0.3042% | -0.352% | 1.9275% | -1.6795% | 22.22% | 55.56% | 55.56% | 1.9623% | -2.2019% | 0.891 | ACTIONABLE + score >= 80. |
| SCORE_GE_70_SHORT | REJECT_INSUFFICIENT_SAMPLE | score_side | 21 | 7.12% | -0.5103% | -0.4844% | 0.4043% | -2.9327% | 33.33% | 47.62% | 47.62% | 2.0866% | -2.3307% | 0.895 | score >= 70 + SHORT. |
| SHORT_SCORE_GE_70 | REJECT_INSUFFICIENT_SAMPLE | component | 21 | 7.12% | -0.5103% | -0.4844% | 0.4043% | -2.9327% | 33.33% | 47.62% | 47.62% | 2.0866% | -2.3307% | 0.895 | short_score >= 70. |
| HISTORICAL_EDGE_SCORE_GE_10 | REJECT_INSUFFICIENT_SAMPLE | component | 14 | 4.75% | -0.2337% | -0.2524% | 0.6391% | -1.2393% | 21.43% | 28.57% | 35.71% | 1.0227% | -1.6945% | 0.604 | historical_edge_score >= 10. |
| SYMBOL_SIDE_SOLUSDT_LONG | REJECT_INSUFFICIENT_SAMPLE | symbol_side | 24 | 8.14% | -0.3392% | -0.4763% | 4.8272% | -2.6468% | 20.83% | 45.83% | 54.17% | 2.0345% | -2.359% | 0.862 | SOL/USDT فقط LONG. |
| SYMBOL_SIDE_SCORE_GE_60_SOLUSDT_LONG | REJECT_INSUFFICIENT_SAMPLE | symbol_side_score | 15 | 5.08% | -0.6914% | -0.6263% | 0.0475% | -2.6468% | 6.67% | 46.67% | 53.33% | 1.6051% | -2.4854% | 0.646 | SOL/USDT + LONG + score >= 60. |
| SYMBOL_ACTIONABLE_DOGEUSDT | REJECT_INSUFFICIENT_SAMPLE | symbol_actionability | 10 | 3.39% | -0.8977% | -0.9202% | 0.132% | -1.7141% | 10.0% | 40.0% | 50.0% | 2.0676% | -2.7929% | 0.74 | DOGE/USDT + ACTIONABLE. |
| SYMBOL_SIDE_XRPUSDT_LONG | REJECT_INSUFFICIENT_SAMPLE | symbol_side | 17 | 5.76% | -0.6399% | -0.5136% | 0.2898% | -2.9412% | 11.76% | 35.29% | 52.94% | 1.6464% | -2.4839% | 0.663 | XRP/USDT فقط LONG. |
| SYMBOL_SIDE_ACTIONABLE_BNBUSDT_LONG | REJECT_TOO_SMALL | symbol_side_actionability | 6 | 2.03% | 0.4061% | 0.1716% | 1.9275% | -0.4323% | 66.67% | 100.0% | 33.33% | 2.5255% | -0.9158% | 2.758 | BNB/USDT + LONG + ACTIONABLE. |
| SYMBOL_ACTIONABLE_BNBUSDT | REJECT_TOO_SMALL | symbol_actionability | 9 | 3.05% | 0.2036% | 0.0474% | 1.9275% | -0.5032% | 55.56% | 88.89% | 33.33% | 2.8408% | -1.1226% | 2.531 | BNB/USDT + ACTIONABLE. |
| SYMBOL_SIDE_SCORE_GE_80_ETHUSDT_LONG | REJECT_TOO_SMALL | symbol_side_score | 2 | 0.68% | 0.3281% | 0.3281% | 0.413% | 0.2431% | 100.0% | 50.0% | 50.0% | 2.0627% | -1.6347% | 1.262 | ETH/USDT + LONG + score >= 80. |
| REGIME_QUIET | REJECT_TOO_SMALL | regime | 1 | 0.34% | 0.1866% | 0.1866% | 0.1866% | 0.1866% | 100.0% | 0.0% | 0.0% | 1.4364% | -1.3413% | 1.071 | فقط regime=QUIET. |
| SYMBOL_SIDE_SCORE_GE_80_BNBUSDT_LONG | REJECT_TOO_SMALL | symbol_side_score | 4 | 1.36% | 0.5232% | 0.2989% | 1.9275% | -0.4323% | 50.0% | 100.0% | 50.0% | 1.9031% | -1.151% | 1.653 | BNB/USDT + LONG + score >= 80. |
| SYMBOL_SIDE_ACTIONABLE_XRPUSDT_SHORT | REJECT_TOO_SMALL | symbol_side_actionability | 3 | 1.02% | -0.2238% | 0.2574% | 0.2612% | -1.1899% | 66.67% | 66.67% | 33.33% | 2.1014% | -1.4861% | 1.414 | XRP/USDT + SHORT + ACTIONABLE. |
| SYMBOL_SIDE_SCORE_GE_80_BNBUSDT_SHORT | REJECT_TOO_SMALL | symbol_side_score | 1 | 0.34% | -0.4844% | -0.4844% | -0.4844% | -0.4844% | 0.0% | 100.0% | 0.0% | 4.2989% | -0.9139% | 4.704 | BNB/USDT + SHORT + score >= 80. |
| SYMBOL_SIDE_SCORE_GE_80_BTCUSDT_SHORT | REJECT_TOO_SMALL | symbol_side_score | 1 | 0.34% | -0.3192% | -0.3192% | -0.3192% | -0.3192% | 0.0% | 100.0% | 0.0% | 3.1668% | -0.7856% | 4.031 | BTC/USDT + SHORT + score >= 80. |
| SYMBOL_SIDE_SCORE_GE_80_XRPUSDT_LONG | REJECT_TOO_SMALL | symbol_side_score | 1 | 0.34% | -0.548% | -0.548% | -0.548% | -0.548% | 0.0% | 100.0% | 0.0% | 4.7767% | -1.3503% | 3.538 | XRP/USDT + LONG + score >= 80. |
| SYMBOL_SIDE_ACTIONABLE_BNBUSDT_SHORT | REJECT_TOO_SMALL | symbol_side_actionability | 3 | 1.02% | -0.2013% | -0.4844% | 0.3837% | -0.5032% | 33.33% | 66.67% | 33.33% | 3.4714% | -1.5362% | 2.26 | BNB/USDT + SHORT + ACTIONABLE. |
| SYMBOL_ACTIONABLE_XRPUSDT | REJECT_TOO_SMALL | symbol_actionability | 5 | 1.69% | -0.4206% | -0.548% | 0.2612% | -1.1899% | 40.0% | 60.0% | 40.0% | 2.2592% | -1.8324% | 1.233 | XRP/USDT + ACTIONABLE. |
| VOLUME_SCORE_GE_15 | REJECT_TOO_SMALL | component | 6 | 2.03% | -0.5937% | -0.5642% | -0.3192% | -0.9032% | 0.0% | 83.33% | 33.33% | 2.8219% | -1.7596% | 1.604 | volume_score >= 15. |
| SCORE_GE_80_SHORT | REJECT_TOO_SMALL | score_side | 4 | 1.36% | -0.7016% | -0.5349% | -0.3192% | -1.4176% | 0.0% | 75.0% | 25.0% | 2.925% | -2.0213% | 1.447 | score >= 80 + SHORT. |
| SYMBOL_SIDE_ACTIONABLE_DOGEUSDT_SHORT | REJECT_TOO_SMALL | symbol_side_actionability | 3 | 1.02% | -0.6236% | -0.5853% | 0.132% | -1.4176% | 33.33% | 33.33% | 33.33% | 1.987% | -2.7957% | 0.711 | DOGE/USDT + SHORT + ACTIONABLE. |
| CONFIDENCE_HIGH | REJECT_TOO_SMALL | confidence | 7 | 2.37% | -0.144% | -0.2628% | 0.7254% | -0.5853% | 28.57% | 42.86% | 57.14% | 1.6763% | -2.0381% | 0.822 | فقط confidence=High. |
| ACTIONABLE_SCORE_GE_80_SHORT | REJECT_TOO_SMALL | actionability_score_side | 3 | 1.02% | -0.8291% | -0.5853% | -0.4844% | -1.4176% | 0.0% | 66.67% | 33.33% | 2.8444% | -2.4332% | 1.169 | ACTIONABLE + score >= 80 + SHORT. |
| SYMBOL_SIDE_ACTIONABLE_ETHUSDT_LONG | REJECT_TOO_SMALL | symbol_side_actionability | 4 | 1.36% | -0.3265% | -0.1884% | 0.413% | -1.3422% | 50.0% | 25.0% | 75.0% | 1.1054% | -3.2809% | 0.337 | ETH/USDT + LONG + ACTIONABLE. |
| SYMBOL_SIDE_ACTIONABLE_SOLUSDT_SHORT | REJECT_TOO_SMALL | symbol_side_actionability | 2 | 0.68% | -0.4813% | -0.4813% | 0.0716% | -1.0341% | 50.0% | 0.0% | 50.0% | 0.6274% | -1.7275% | 0.363 | SOL/USDT + SHORT + ACTIONABLE. |
| SYMBOL_SIDE_SCORE_GE_80_DOGEUSDT_LONG | REJECT_TOO_SMALL | symbol_side_score | 3 | 1.02% | -1.0491% | -1.2289% | -0.239% | -1.6795% | 0.0% | 66.67% | 33.33% | 3.0634% | -2.3749% | 1.29 | DOGE/USDT + LONG + score >= 80. |
| SYMBOL_SIDE_ACTIONABLE_XRPUSDT_LONG | REJECT_TOO_SMALL | symbol_side_actionability | 2 | 0.68% | -0.716% | -0.716% | -0.548% | -0.8839% | 0.0% | 50.0% | 50.0% | 2.496% | -2.3518% | 1.061 | XRP/USDT + LONG + ACTIONABLE. |
| SYMBOL_ACTIONABLE_ETHUSDT | REJECT_TOO_SMALL | symbol_actionability | 7 | 2.37% | -0.4012% | -0.53% | 0.413% | -1.3422% | 28.57% | 28.57% | 71.43% | 1.4168% | -3.2597% | 0.435 | ETH/USDT + ACTIONABLE. |
| SYMBOL_SIDE_SCORE_GE_80_DOGEUSDT_SHORT | REJECT_TOO_SMALL | symbol_side_score | 2 | 0.68% | -1.0014% | -1.0014% | -0.5853% | -1.4176% | 0.0% | 50.0% | 50.0% | 2.1172% | -3.1928% | 0.663 | DOGE/USDT + SHORT + score >= 80. |
| SYMBOL_SIDE_ACTIONABLE_BTCUSDT_SHORT | REJECT_TOO_SMALL | symbol_side_actionability | 2 | 0.68% | 0.0556% | 0.0556% | 0.4043% | -0.2931% | 50.0% | 0.0% | 100.0% | 0.6015% | -2.238% | 0.269 | BTC/USDT + SHORT + ACTIONABLE. |
| SYMBOL_ACTIONABLE_SOLUSDT | REJECT_TOO_SMALL | symbol_actionability | 8 | 2.71% | -0.6543% | -0.6699% | 0.0716% | -1.2905% | 12.5% | 37.5% | 62.5% | 1.6163% | -2.6592% | 0.608 | SOL/USDT + ACTIONABLE. |
| SYMBOL_SIDE_SCORE_GE_80_BTCUSDT_LONG | REJECT_TOO_SMALL | symbol_side_score | 5 | 1.69% | -0.1777% | -0.2628% | 0.6072% | -0.8639% | 20.0% | 20.0% | 80.0% | 0.6001% | -2.3296% | 0.258 | BTC/USDT + LONG + score >= 80. |
| SYMBOL_SIDE_SCORE_GE_60_BTCUSDT_SHORT | REJECT_TOO_SMALL | symbol_side_score | 9 | 3.05% | -0.5263% | -0.3192% | 0.6816% | -1.8426% | 22.22% | 22.22% | 66.67% | 1.3389% | -2.7013% | 0.496 | BTC/USDT + SHORT + score >= 60. |
| SYMBOL_SIDE_ACTIONABLE_SOLUSDT_LONG | REJECT_TOO_SMALL | symbol_side_actionability | 6 | 2.03% | -0.712% | -0.6699% | -0.2197% | -1.2905% | 0.0% | 50.0% | 66.67% | 1.9459% | -2.9698% | 0.655 | SOL/USDT + LONG + ACTIONABLE. |
| SYMBOL_SIDE_ACTIONABLE_ETHUSDT_SHORT | REJECT_TOO_SMALL | symbol_side_actionability | 3 | 1.02% | -0.5008% | -0.53% | -0.1092% | -0.8632% | 0.0% | 33.33% | 66.67% | 1.8321% | -3.2316% | 0.567 | ETH/USDT + SHORT + ACTIONABLE. |
| RISK_HIGH | REJECT_TOO_SMALL | risk | 8 | 2.71% | -1.4192% | -1.0515% | -0.3153% | -2.9412% | 0.0% | 50.0% | 37.5% | 2.7212% | -3.5938% | 0.757 | فقط risk_label=High. |
| SYMBOL_SIDE_ACTIONABLE_DOGEUSDT_LONG | REJECT_TOO_SMALL | symbol_side_actionability | 7 | 2.37% | -1.0151% | -1.2289% | -0.1811% | -1.7141% | 0.0% | 42.86% | 57.14% | 2.1022% | -2.7917% | 0.753 | DOGE/USDT + LONG + ACTIONABLE. |
| SYMBOL_ACTIONABLE_BTCUSDT | REJECT_TOO_SMALL | symbol_actionability | 7 | 2.37% | -0.2325% | -0.2628% | 0.4043% | -0.8639% | 14.29% | 14.29% | 85.71% | 0.609% | -2.3515% | 0.259 | BTC/USDT + ACTIONABLE. |
| SYMBOL_SIDE_SCORE_GE_60_XRPUSDT_LONG | REJECT_TOO_SMALL | symbol_side_score | 9 | 3.05% | -0.6611% | -0.548% | -0.2493% | -1.1899% | 0.0% | 33.33% | 66.67% | 1.8289% | -2.7252% | 0.671 | XRP/USDT + LONG + score >= 60. |
| SYMBOL_SIDE_ACTIONABLE_BTCUSDT_LONG | REJECT_TOO_SMALL | symbol_side_actionability | 5 | 1.69% | -0.3477% | -0.2628% | -0.0973% | -0.8639% | 0.0% | 20.0% | 80.0% | 0.612% | -2.3969% | 0.255 | BTC/USDT + LONG + ACTIONABLE. |
| SCORE_BUCKET_90_PLUS | REJECT_TOO_SMALL | score_bucket | 1 | 0.34% | -0.2628% | -0.2628% | -0.2628% | -0.2628% | 0.0% | 0.0% | 100.0% | 0.5583% | -2.2619% | 0.247 | score >= 90 |
| SYMBOL_SIDE_SCORE_GE_80_SOLUSDT_LONG | REJECT_TOO_SMALL | symbol_side_score | 1 | 0.34% | -0.5464% | -0.5464% | -0.5464% | -0.5464% | 0.0% | 0.0% | 100.0% | 0.1025% | -4.3716% | 0.023 | SOL/USDT + LONG + score >= 80. |

## Research Blockers
- Baseline Backtest هنوز میانگین مثبت ندارد.

## Recommendations
- فقط candidateهای مثبت کم‌نمونه پیدا شد؛ بهترین: SYMBOL_SIDE_SCORE_GE_60_DOGEUSDT_SHORT | avg=0.1571% | samples=12.
- این gate باید تا حداقل 30 sample در Backtest/Forward گسترش داده شود؛ فعلاً Paper جدی مجاز نیست.
- ACTIONABLE فعلی هنوز مثبت نیست: avg=-0.4113%، stop=56.52%. گیت actionability باید سخت‌تر شود.
- score>=80 را جدا نگه دار: samples=20, avg=-0.2594%. اگر sample کم است، فقط research watchlist باشد.

## Safety Notes
- Gate Simulator فقط فیلترهای live-known را تست می‌کند؛ target/stop/return/MFE/MAE برای فیلتر استفاده نشده‌اند.
- BACKTEST جای FORWARD_TEST و Paper واقعی را نمی‌گیرد؛ candidateها فقط برای تحقیق هستند.
- subsetهای کم‌نمونه می‌توانند overfit باشند؛ sample حداقل و تأیید forward لازم است.