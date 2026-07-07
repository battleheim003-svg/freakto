# Freakto Backtest Gate Simulator v5.3.2

## Summary
- Status: `GATE_RESEARCH_CANDIDATES_FOUND`
- Generated UTC: `2026-07-07T12:23:57.169569+00:00`
- Horizon: `24h`
- Min Samples: `30`
- Rows / Complete: `654/654`
- Directional Samples: `295`
- Baseline Avg Return: `-0.2509%`
- Baseline Win Rate: `46.10%`
- Baseline T1 / Stop: `48.14% / 47.12%`
- Gates Tested: `139`
- Positive Gates: `4`
- Research Candidates: `3`
- Small Positive Gates: `11`

## Top Gates
| Gate | Verdict | Family | Samples | Avg | Win | T1 | Stop | MFE/MAE | Research Score |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| VOLUME_SCORE_GE_10 | RESEARCH_CANDIDATE | component | 34 | 0.7131% | 64.71% | 76.47% | 44.12% | 1.314 | 1.2887 |
| RISK_MEDIUM | RESEARCH_CANDIDATE | risk | 76 | 0.2106% | 51.32% | 53.95% | 42.11% | 1.037 | 0.3525 |
| HISTORICAL_EDGE_SCORE_GE_1 | RESEARCH_CANDIDATE | component | 40 | 0.1026% | 57.5% | 47.5% | 35.0% | 1.066 | 0.3467 |
| STRUCTURE_SCORE_GE_10 | POSITIVE_BUT_NEEDS_REVIEW | component | 86 | 0.266% | 52.33% | 53.49% | 44.19% | 0.992 | 0.3931 |
| SYMBOL_SIDE_SCORE_GE_60_BNBUSDT_LONG | SMALL_SAMPLE_POSITIVE | symbol_side_score | 11 | 0.5033% | 72.73% | 72.73% | 54.55% | 1.374 | 0.8649 |
| SCORE_BUCKET_80_89 | SMALL_SAMPLE_POSITIVE | score_bucket | 19 | 0.3758% | 57.89% | 63.16% | 47.37% | 1.046 | 0.5799 |
| SCORE_GE_80 | SMALL_SAMPLE_POSITIVE | score | 20 | 0.3797% | 60.0% | 60.0% | 50.0% | 1.001 | 0.5601 |
| QUALITY_CORE_SCORE80_WATCH_OR_ACTIONABLE | SMALL_SAMPLE_POSITIVE | composite | 20 | 0.3797% | 60.0% | 60.0% | 50.0% | 1.001 | 0.5601 |
| SYMBOL_SIDE_DOGEUSDT_SHORT | SMALL_SAMPLE_POSITIVE | symbol_side | 25 | 0.2309% | 40.0% | 52.0% | 32.0% | 1.207 | 0.2815 |
| ACTIONABLE_SCORE_GE_80 | SMALL_SAMPLE_POSITIVE | actionability_score | 18 | 0.2069% | 55.56% | 55.56% | 55.56% | 0.891 | 0.2328 |
| SCORE_GE_80_LONG | SMALL_SAMPLE_POSITIVE | score_side | 16 | 0.1384% | 56.25% | 56.25% | 56.25% | 0.89 | 0.1838 |
| SYMBOL_SIDE_SCORE_GE_60_XRPUSDT_SHORT | SMALL_SAMPLE_POSITIVE | symbol_side_score | 15 | 0.013% | 46.67% | 66.67% | 46.67% | 1.088 | 0.168 |
| SYMBOL_SIDE_SCORE_GE_60_DOGEUSDT_SHORT | SMALL_SAMPLE_POSITIVE | symbol_side_score | 12 | 0.1437% | 41.67% | 50.0% | 33.33% | 1.03 | 0.1356 |
| ACTIONABLE_SCORE_GE_80_LONG | SMALL_SAMPLE_POSITIVE | actionability_score_side | 15 | 0.031% | 53.33% | 53.33% | 60.0% | 0.828 | -0.012 |
| SYMBOL_SIDE_SCORE_GE_60_BNBUSDT_SHORT | SMALL_SAMPLE_POSITIVE | symbol_side_score | 11 | 0.0706% | 45.45% | 45.45% | 54.55% | 1.092 | -0.1073 |
| SYMBOL_SIDE_BNBUSDT_LONG | NEAR_BREAKEVEN_WATCH | symbol_side | 30 | -0.0784% | 53.33% | 56.67% | 50.0% | 0.972 | 0.0354 |
| SYMBOL_WATCH_OR_ACTIONABLE_BNBUSDT | NEAR_BREAKEVEN_WATCH | symbol_actionability | 36 | -0.063% | 50.0% | 52.78% | 52.78% | 1.001 | -0.0629 |
| SCORE_BUCKET_60_69 | NEAR_BREAKEVEN_WATCH | score_bucket | 90 | -0.0554% | 47.78% | 47.78% | 47.78% | 0.944 | -0.0943 |
| SCORE_GE_60_LONG | REJECT_NEGATIVE_EDGE | score_side | 83 | -0.1223% | 55.42% | 48.19% | 48.19% | 0.812 | -0.0598 |
| LONG_SCORE_GE_60 | REJECT_NEGATIVE_EDGE | component | 83 | -0.1223% | 55.42% | 48.19% | 48.19% | 0.812 | -0.0598 |

## All Gate Results
| Gate | Verdict | Family | Samples | Share | Avg | Median | Best | Worst | Win | T1 | Stop | MFE | MAE | MFE/MAE | Description |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| VOLUME_SCORE_GE_10 | RESEARCH_CANDIDATE | component | 34 | 11.53% | 0.7131% | 1.1114% | 4.6531% | -5.0698% | 64.71% | 76.47% | 44.12% | 2.7339% | -2.0804% | 1.314 | volume_score >= 10. |
| RISK_MEDIUM | RESEARCH_CANDIDATE | risk | 76 | 25.76% | 0.2106% | 0.1673% | 9.0062% | -10.3172% | 51.32% | 53.95% | 42.11% | 2.201% | -2.1233% | 1.037 | فقط risk_label=Medium. |
| HISTORICAL_EDGE_SCORE_GE_1 | RESEARCH_CANDIDATE | component | 40 | 13.56% | 0.1026% | 0.3952% | 5.98% | -5.1034% | 57.5% | 47.5% | 35.0% | 1.6298% | -1.5296% | 1.066 | historical_edge_score >= 1. |
| STRUCTURE_SCORE_GE_10 | POSITIVE_BUT_NEEDS_REVIEW | component | 86 | 29.15% | 0.266% | 0.1673% | 5.6706% | -5.0698% | 52.33% | 53.49% | 44.19% | 2.0978% | -2.1147% | 0.992 | structure_score >= 10. |
| SYMBOL_SIDE_SCORE_GE_60_BNBUSDT_LONG | SMALL_SAMPLE_POSITIVE | symbol_side_score | 11 | 3.73% | 0.5033% | 0.7693% | 2.9778% | -3.3654% | 72.73% | 72.73% | 54.55% | 2.1094% | -1.5351% | 1.374 | BNB/USDT + LONG + score >= 60. |
| SCORE_BUCKET_80_89 | SMALL_SAMPLE_POSITIVE | score_bucket | 19 | 6.44% | 0.3758% | 1.0517% | 4.6531% | -3.94% | 57.89% | 63.16% | 47.37% | 2.1026% | -2.0101% | 1.046 | score 80-89 |
| SCORE_GE_80 | SMALL_SAMPLE_POSITIVE | score | 20 | 6.78% | 0.3797% | 0.9105% | 4.6531% | -3.94% | 60.0% | 60.0% | 50.0% | 2.0254% | -2.0227% | 1.001 | score >= 80 |
| QUALITY_CORE_SCORE80_WATCH_OR_ACTIONABLE | SMALL_SAMPLE_POSITIVE | composite | 20 | 6.78% | 0.3797% | 0.9105% | 4.6531% | -3.94% | 60.0% | 60.0% | 50.0% | 2.0254% | -2.0227% | 1.001 | WATCHLIST/ACTIONABLE + score>=80. |
| SYMBOL_SIDE_DOGEUSDT_SHORT | SMALL_SAMPLE_POSITIVE | symbol_side | 25 | 8.47% | 0.2309% | -0.5225% | 9.0062% | -4.8751% | 40.0% | 52.0% | 32.0% | 2.6864% | -2.2261% | 1.207 | DOGE/USDT فقط SHORT. |
| ACTIONABLE_SCORE_GE_80 | SMALL_SAMPLE_POSITIVE | actionability_score | 18 | 6.1% | 0.2069% | 0.6111% | 4.6531% | -3.94% | 55.56% | 55.56% | 55.56% | 1.9623% | -2.2019% | 0.891 | ACTIONABLE + score >= 80. |
| SCORE_GE_80_LONG | SMALL_SAMPLE_POSITIVE | score_side | 16 | 5.42% | 0.1384% | 0.6111% | 4.6531% | -3.94% | 56.25% | 56.25% | 56.25% | 1.8005% | -2.023% | 0.89 | score >= 80 + LONG. |
| SYMBOL_SIDE_SCORE_GE_60_XRPUSDT_SHORT | SMALL_SAMPLE_POSITIVE | symbol_side_score | 15 | 5.08% | 0.013% | -0.3861% | 3.1476% | -3.613% | 46.67% | 66.67% | 46.67% | 2.2003% | -2.0223% | 1.088 | XRP/USDT + SHORT + score >= 60. |
| SYMBOL_SIDE_SCORE_GE_60_DOGEUSDT_SHORT | SMALL_SAMPLE_POSITIVE | symbol_side_score | 12 | 4.07% | 0.1437% | -0.7664% | 5.1951% | -4.8751% | 41.67% | 50.0% | 33.33% | 2.4333% | -2.3617% | 1.03 | DOGE/USDT + SHORT + score >= 60. |
| ACTIONABLE_SCORE_GE_80_LONG | SMALL_SAMPLE_POSITIVE | actionability_score_side | 15 | 5.08% | 0.031% | 0.453% | 4.6531% | -3.94% | 53.33% | 53.33% | 60.0% | 1.7859% | -2.1556% | 0.828 | ACTIONABLE + score >= 80 + LONG. |
| SYMBOL_SIDE_SCORE_GE_60_BNBUSDT_SHORT | SMALL_SAMPLE_POSITIVE | symbol_side_score | 11 | 3.73% | 0.0706% | -0.171% | 3.3114% | -2.8205% | 45.45% | 45.45% | 54.55% | 1.9282% | -1.7658% | 1.092 | BNB/USDT + SHORT + score >= 60. |
| SYMBOL_SIDE_BNBUSDT_LONG | NEAR_BREAKEVEN_WATCH | symbol_side | 30 | 10.17% | -0.0784% | 0.2327% | 2.9778% | -3.3654% | 53.33% | 56.67% | 50.0% | 1.6431% | -1.6906% | 0.972 | BNB/USDT فقط LONG. |
| SYMBOL_WATCH_OR_ACTIONABLE_BNBUSDT | NEAR_BREAKEVEN_WATCH | symbol_actionability | 36 | 12.2% | -0.063% | 0.0539% | 3.3114% | -3.3654% | 50.0% | 52.78% | 52.78% | 1.7171% | -1.7145% | 1.001 | BNB/USDT + WATCHLIST/ACTIONABLE. |
| SCORE_BUCKET_60_69 | NEAR_BREAKEVEN_WATCH | score_bucket | 90 | 30.51% | -0.0554% | -0.1521% | 5.6706% | -5.2498% | 47.78% | 47.78% | 47.78% | 2.0368% | -2.1567% | 0.944 | score 60-69 |
| SCORE_GE_60_LONG | REJECT_NEGATIVE_EDGE | score_side | 83 | 28.14% | -0.1223% | 0.1781% | 5.4035% | -6.4619% | 55.42% | 48.19% | 48.19% | 1.7376% | -2.1403% | 0.812 | score >= 60 + LONG. |
| LONG_SCORE_GE_60 | REJECT_NEGATIVE_EDGE | component | 83 | 28.14% | -0.1223% | 0.1781% | 5.4035% | -6.4619% | 55.42% | 48.19% | 48.19% | 1.7376% | -2.1403% | 0.812 | long_score >= 60. |
| SYMBOL_SIDE_BTCUSDT_LONG | REJECT_NEGATIVE_EDGE | symbol_side | 36 | 12.2% | -0.1739% | 0.3577% | 2.7195% | -3.5171% | 55.56% | 44.44% | 41.67% | 1.2707% | -1.5117% | 0.841 | BTC/USDT فقط LONG. |
| STRUCTURE_SCORE_GE_5 | REJECT_NEGATIVE_EDGE | component | 240 | 81.36% | -0.1027% | -0.1562% | 9.0062% | -10.3172% | 47.5% | 48.75% | 46.67% | 1.9543% | -2.1468% | 0.91 | structure_score >= 5. |
| HISTORICAL_EDGE_SCORE_GE_5 | REJECT_NEGATIVE_EDGE | component | 30 | 10.17% | -0.1957% | 0.2496% | 2.7195% | -3.3236% | 53.33% | 40.0% | 36.67% | 1.2445% | -1.5062% | 0.826 | historical_edge_score >= 5. |
| ACTIONABLE_LONG | REJECT_NEGATIVE_EDGE | actionability_side | 30 | 10.17% | -0.0682% | 0.2951% | 5.4035% | -5.0698% | 53.33% | 50.0% | 60.0% | 1.8006% | -2.4222% | 0.743 | ACTIONABLE فقط سمت LONG. |
| ACTIONABLE_SCORE_GE_50_LONG | REJECT_NEGATIVE_EDGE | actionability_score_side | 30 | 10.17% | -0.0682% | 0.2951% | 5.4035% | -5.0698% | 53.33% | 50.0% | 60.0% | 1.8006% | -2.4222% | 0.743 | ACTIONABLE + score >= 50 + LONG. |
| ACTIONABLE_SCORE_GE_60_LONG | REJECT_NEGATIVE_EDGE | actionability_score_side | 30 | 10.17% | -0.0682% | 0.2951% | 5.4035% | -5.0698% | 53.33% | 50.0% | 60.0% | 1.8006% | -2.4222% | 0.743 | ACTIONABLE + score >= 60 + LONG. |
| ACTIONABLE_SCORE_GE_70_LONG | REJECT_NEGATIVE_EDGE | actionability_score_side | 30 | 10.17% | -0.0682% | 0.2951% | 5.4035% | -5.0698% | 53.33% | 50.0% | 60.0% | 1.8006% | -2.4222% | 0.743 | ACTIONABLE + score >= 70 + LONG. |
| LONG_SCORE60_ACTIONABLE | REJECT_NEGATIVE_EDGE | composite | 30 | 10.17% | -0.0682% | 0.2951% | 5.4035% | -5.0698% | 53.33% | 50.0% | 60.0% | 1.8006% | -2.4222% | 0.743 | LONG + ACTIONABLE + score>=60. |
| SYMBOL_XRPUSDT | REJECT_NEGATIVE_EDGE | symbol | 41 | 13.9% | -0.151% | 0.0624% | 4.6531% | -4.3192% | 51.22% | 51.22% | 51.22% | 1.8807% | -2.2483% | 0.836 | فقط نماد XRP/USDT. |
| SYMBOL_WATCH_OR_ACTIONABLE_SOLUSDT | REJECT_NEGATIVE_EDGE | symbol_actionability | 40 | 13.56% | -0.1278% | -0.1213% | 6.9713% | -10.3172% | 47.5% | 52.5% | 52.5% | 2.3949% | -2.5927% | 0.924 | SOL/USDT + WATCHLIST/ACTIONABLE. |
| REGIME_TRENDING_BULL | REJECT_NEGATIVE_EDGE | regime | 136 | 46.1% | -0.1985% | 0.1493% | 5.4035% | -6.4619% | 53.68% | 48.53% | 50.0% | 1.7052% | -2.1211% | 0.804 | فقط regime=TRENDING_BULL. |
| SCORE_GE_60 | REJECT_NEGATIVE_EDGE | score | 154 | 52.2% | -0.1423% | -0.1501% | 5.6706% | -6.4619% | 48.05% | 48.7% | 49.35% | 1.9403% | -2.2353% | 0.868 | score >= 60 |
| SYMBOL_DOGEUSDT | REJECT_NEGATIVE_EDGE | symbol | 48 | 16.27% | -0.1383% | -0.4938% | 9.0062% | -6.4619% | 39.58% | 50.0% | 41.67% | 2.555% | -2.4261% | 1.053 | فقط نماد DOGE/USDT. |
| SYMBOL_BNBUSDT | REJECT_NEGATIVE_EDGE | symbol | 50 | 16.95% | -0.161% | -0.1765% | 3.3114% | -3.3654% | 46.0% | 50.0% | 48.0% | 1.6255% | -1.7328% | 0.938 | فقط نماد BNB/USDT. |
| VOLUME_SCORE_GE_5 | REJECT_NEGATIVE_EDGE | component | 142 | 48.14% | -0.1907% | -0.1691% | 9.0062% | -10.3172% | 47.18% | 50.7% | 47.18% | 2.1814% | -2.4578% | 0.888 | volume_score >= 5. |
| SYMBOL_WATCH_OR_ACTIONABLE_ETHUSDT | REJECT_NEGATIVE_EDGE | symbol_actionability | 36 | 12.2% | -0.3211% | 0.1296% | 5.6706% | -5.6986% | 52.78% | 55.56% | 47.22% | 2.0406% | -2.4071% | 0.848 | ETH/USDT + WATCHLIST/ACTIONABLE. |
| SYMBOL_WATCH_OR_ACTIONABLE_DOGEUSDT | REJECT_NEGATIVE_EDGE | symbol_actionability | 38 | 12.88% | -0.159% | -0.4938% | 9.0062% | -6.4619% | 39.47% | 50.0% | 42.11% | 2.6617% | -2.4716% | 1.077 | DOGE/USDT + WATCHLIST/ACTIONABLE. |
| LONG_ONLY | REJECT_NEGATIVE_EDGE | side | 150 | 50.85% | -0.2283% | 0.1159% | 5.4035% | -6.4619% | 52.0% | 47.33% | 49.33% | 1.735% | -2.0798% | 0.834 | فقط معاملات LONG. |
| SCORE_GE_50_LONG | REJECT_NEGATIVE_EDGE | score_side | 150 | 50.85% | -0.2283% | 0.1159% | 5.4035% | -6.4619% | 52.0% | 47.33% | 49.33% | 1.735% | -2.0798% | 0.834 | score >= 50 + LONG. |
| LONG_SCORE_GE_50 | REJECT_NEGATIVE_EDGE | component | 150 | 50.85% | -0.2283% | 0.1159% | 5.4035% | -6.4619% | 52.0% | 47.33% | 49.33% | 1.735% | -2.0798% | 0.834 | long_score >= 50. |
| CONFIDENCE_MEDIUM | REJECT_NEGATIVE_EDGE | confidence | 158 | 53.56% | -0.2024% | -0.265% | 9.0062% | -10.3172% | 46.2% | 50.0% | 49.37% | 2.1397% | -2.193% | 0.976 | فقط confidence=Medium. |
| REGIME_TRENDING_BEAR | REJECT_NEGATIVE_EDGE | regime | 138 | 46.78% | -0.1894% | -0.4333% | 9.0062% | -10.3172% | 41.3% | 50.0% | 44.2% | 2.1768% | -2.2881% | 0.951 | فقط regime=TRENDING_BEAR. |
| WATCH_OR_ACTIONABLE_LONG | REJECT_NEGATIVE_EDGE | actionability_side | 117 | 39.66% | -0.2713% | 0.1371% | 5.4035% | -6.4619% | 52.99% | 47.86% | 50.43% | 1.8048% | -2.1285% | 0.848 | WATCHLIST/ACTIONABLE فقط سمت LONG. |
| WATCHLIST_ONLY | REJECT_NEGATIVE_EDGE | actionability | 176 | 59.66% | -0.2406% | -0.2015% | 9.0062% | -10.3172% | 46.59% | 51.14% | 48.3% | 2.0962% | -2.2095% | 0.949 | فقط WATCHLIST برای مقایسه با ACTIONABLE. |
| SCORE_GE_70_LONG | REJECT_NEGATIVE_EDGE | score_side | 43 | 14.58% | -0.2758% | 0.3539% | 5.4035% | -6.4619% | 53.49% | 51.16% | 53.49% | 1.6671% | -2.3532% | 0.708 | score >= 70 + LONG. |
| LONG_SCORE_GE_70 | REJECT_NEGATIVE_EDGE | component | 43 | 14.58% | -0.2758% | 0.3539% | 5.4035% | -6.4619% | 53.49% | 51.16% | 53.49% | 1.6671% | -2.3532% | 0.708 | long_score >= 70. |
| WATCHLIST_OR_ACTIONABLE | REJECT_NEGATIVE_EDGE | actionability | 222 | 75.25% | -0.2203% | -0.2015% | 9.0062% | -10.3172% | 46.85% | 50.0% | 50.0% | 2.0431% | -2.237% | 0.913 | WATCHLIST یا ACTIONABLE؛ گیت نیمه‌محافظه‌کار. |
| WATCH_OR_ACTIONABLE_SHORT | REJECT_NEGATIVE_EDGE | actionability_side | 105 | 35.59% | -0.1634% | -0.4944% | 9.0062% | -10.3172% | 40.0% | 52.38% | 49.52% | 2.3087% | -2.3579% | 0.979 | WATCHLIST/ACTIONABLE فقط سمت SHORT. |
| MOMENTUM_SCORE_GE_15 | REJECT_NEGATIVE_EDGE | component | 289 | 97.97% | -0.2463% | -0.2506% | 9.0062% | -10.3172% | 46.37% | 48.44% | 47.06% | 1.9509% | -2.2088% | 0.883 | momentum_score >= 15. |
| TREND_SCORE_GE_10 | REJECT_NEGATIVE_EDGE | component | 293 | 99.32% | -0.2382% | -0.2506% | 9.0062% | -10.3172% | 46.08% | 48.12% | 47.1% | 1.9213% | -2.1882% | 0.878 | trend_score >= 10. |
| ACTIONABLE_ONLY | REJECT_NEGATIVE_EDGE | actionability | 46 | 15.59% | -0.1425% | -0.2782% | 5.4035% | -5.0698% | 47.83% | 45.65% | 56.52% | 1.8402% | -2.3423% | 0.786 | فقط تصمیم‌هایی که موتور ACTIONABLE کرده است. |
| ACTIONABLE_SCORE_GE_50 | REJECT_NEGATIVE_EDGE | actionability_score | 46 | 15.59% | -0.1425% | -0.2782% | 5.4035% | -5.0698% | 47.83% | 45.65% | 56.52% | 1.8402% | -2.3423% | 0.786 | ACTIONABLE + score >= 50. |
| ACTIONABLE_SCORE_GE_60 | REJECT_NEGATIVE_EDGE | actionability_score | 46 | 15.59% | -0.1425% | -0.2782% | 5.4035% | -5.0698% | 47.83% | 45.65% | 56.52% | 1.8402% | -2.3423% | 0.786 | ACTIONABLE + score >= 60. |
| ACTIONABLE_SCORE_GE_70 | REJECT_NEGATIVE_EDGE | actionability_score | 46 | 15.59% | -0.1425% | -0.2782% | 5.4035% | -5.0698% | 47.83% | 45.65% | 56.52% | 1.8402% | -2.3423% | 0.786 | ACTIONABLE + score >= 70. |
| QUALITY_CORE_SCORE60_ACTIONABLE | REJECT_NEGATIVE_EDGE | composite | 46 | 15.59% | -0.1425% | -0.2782% | 5.4035% | -5.0698% | 47.83% | 45.65% | 56.52% | 1.8402% | -2.3423% | 0.786 | ACTIONABLE + score>=60 + risk not High. |
| BASELINE_DIRECTIONAL | REJECT_NEGATIVE_EDGE | baseline | 295 | 100.0% | -0.2509% | -0.2506% | 9.0062% | -10.3172% | 46.1% | 48.14% | 47.12% | 1.9292% | -2.2058% | 0.875 | تمام تصمیم‌های جهت‌دار کامل؛ فقط برای مقایسه. |
| SCORE_GE_50 | REJECT_NEGATIVE_EDGE | score | 295 | 100.0% | -0.2509% | -0.2506% | 9.0062% | -10.3172% | 46.1% | 48.14% | 47.12% | 1.9292% | -2.2058% | 0.875 | score >= 50 |
| TREND_SCORE_GE_5 | REJECT_NEGATIVE_EDGE | component | 295 | 100.0% | -0.2509% | -0.2506% | 9.0062% | -10.3172% | 46.1% | 48.14% | 47.12% | 1.9292% | -2.2058% | 0.875 | trend_score >= 5. |
| MOMENTUM_SCORE_GE_5 | REJECT_NEGATIVE_EDGE | component | 295 | 100.0% | -0.2509% | -0.2506% | 9.0062% | -10.3172% | 46.1% | 48.14% | 47.12% | 1.9292% | -2.2058% | 0.875 | momentum_score >= 5. |
| MOMENTUM_SCORE_GE_10 | REJECT_NEGATIVE_EDGE | component | 295 | 100.0% | -0.2509% | -0.2506% | 9.0062% | -10.3172% | 46.1% | 48.14% | 47.12% | 1.9292% | -2.2058% | 0.875 | momentum_score >= 10. |
| TREND_SCORE_GE_15 | REJECT_NEGATIVE_EDGE | component | 292 | 98.98% | -0.2451% | -0.2644% | 9.0062% | -10.3172% | 45.89% | 47.95% | 47.26% | 1.9192% | -2.1949% | 0.874 | trend_score >= 15. |
| SCORE_GE_70 | REJECT_NEGATIVE_EDGE | score | 64 | 21.69% | -0.2644% | -0.1213% | 5.4035% | -6.4619% | 48.44% | 50.0% | 51.56% | 1.8048% | -2.3458% | 0.769 | score >= 70 |
| SYMBOL_BTCUSDT | REJECT_NEGATIVE_EDGE | symbol | 55 | 18.64% | -0.2711% | -0.1331% | 5.98% | -5.1034% | 49.09% | 41.82% | 45.45% | 1.4701% | -1.7444% | 0.843 | فقط نماد BTC/USDT. |
| SCORE_GE_60_SHORT | REJECT_NEGATIVE_EDGE | score_side | 71 | 24.07% | -0.1656% | -0.4944% | 5.6706% | -5.2498% | 39.44% | 49.3% | 50.7% | 2.1773% | -2.3463% | 0.928 | score >= 60 + SHORT. |
| SHORT_SCORE_GE_60 | REJECT_NEGATIVE_EDGE | component | 71 | 24.07% | -0.1656% | -0.4944% | 5.6706% | -5.2498% | 39.44% | 49.3% | 50.7% | 2.1773% | -2.3463% | 0.928 | short_score >= 60. |
| CONFIDENCE_MEDIUM-HIGH | REJECT_NEGATIVE_EDGE | confidence | 57 | 19.32% | -0.3086% | -0.1671% | 5.4035% | -6.4619% | 47.37% | 50.88% | 50.88% | 1.8206% | -2.3836% | 0.764 | فقط confidence=Medium-High. |
| SHORT_ONLY | REJECT_NEGATIVE_EDGE | side | 145 | 49.15% | -0.2744% | -0.5225% | 9.0062% | -10.3172% | 40.0% | 48.97% | 44.83% | 2.13% | -2.3363% | 0.912 | فقط معاملات SHORT. |
| SCORE_GE_50_SHORT | REJECT_NEGATIVE_EDGE | score_side | 145 | 49.15% | -0.2744% | -0.5225% | 9.0062% | -10.3172% | 40.0% | 48.97% | 44.83% | 2.13% | -2.3363% | 0.912 | score >= 50 + SHORT. |
| SHORT_SCORE_GE_50 | REJECT_NEGATIVE_EDGE | component | 145 | 49.15% | -0.2744% | -0.5225% | 9.0062% | -10.3172% | 40.0% | 48.97% | 44.83% | 2.13% | -2.3363% | 0.912 | short_score >= 50. |
| SYMBOL_ETHUSDT | REJECT_NEGATIVE_EDGE | symbol | 48 | 16.27% | -0.3824% | -0.2551% | 5.6706% | -5.6986% | 45.83% | 50.0% | 43.75% | 1.8564% | -2.3447% | 0.792 | فقط نماد ETH/USDT. |
| NOT_ACTIONABLE_ONLY | REJECT_NEGATIVE_EDGE | actionability | 73 | 24.75% | -0.3441% | -0.4916% | 3.8682% | -7.4519% | 43.84% | 42.47% | 38.36% | 1.5825% | -2.111% | 0.75 | NOT_ACTIONABLE فقط برای کنترل منفی؛ معمولاً نباید candidate شود. |
| CONFIDENCE_LOW | REJECT_NEGATIVE_EDGE | confidence | 73 | 24.75% | -0.3441% | -0.4916% | 3.8682% | -7.4519% | 43.84% | 42.47% | 38.36% | 1.5825% | -2.111% | 0.75 | فقط confidence=Low. |
| SCORE_BUCKET_50_59 | REJECT_NEGATIVE_EDGE | score_bucket | 141 | 47.8% | -0.3696% | -0.5225% | 9.0062% | -10.3172% | 43.97% | 47.52% | 44.68% | 1.9169% | -2.1737% | 0.882 | score 50-59 |
| SYMBOL_WATCH_OR_ACTIONABLE_BTCUSDT | REJECT_NEGATIVE_EDGE | symbol_actionability | 40 | 13.56% | -0.3534% | -0.1508% | 5.98% | -5.1034% | 47.5% | 42.5% | 50.0% | 1.5604% | -1.8953% | 0.823 | BTC/USDT + WATCHLIST/ACTIONABLE. |
| SYMBOL_WATCH_OR_ACTIONABLE_XRPUSDT | REJECT_NEGATIVE_EDGE | symbol_actionability | 32 | 10.85% | -0.3059% | -0.5692% | 4.6531% | -4.0671% | 43.75% | 46.88% | 56.25% | 1.8419% | -2.3376% | 0.788 | XRP/USDT + WATCHLIST/ACTIONABLE. |
| SYMBOL_SOLUSDT | REJECT_NEGATIVE_EDGE | symbol | 53 | 17.97% | -0.3751% | -0.3641% | 6.9713% | -10.3172% | 45.28% | 47.17% | 52.83% | 2.2285% | -2.7729% | 0.804 | فقط نماد SOL/USDT. |
| RISK_LOW | REJECT_NEGATIVE_EDGE | risk | 211 | 71.53% | -0.4105% | -0.4932% | 6.9713% | -7.4519% | 44.08% | 45.97% | 49.29% | 1.8012% | -2.1829% | 0.825 | فقط risk_label=Low. |
| SCORE_BUCKET_70_79 | REJECT_NEGATIVE_EDGE | score_bucket | 44 | 14.92% | -0.5572% | -0.2789% | 5.4035% | -6.4619% | 43.18% | 45.45% | 52.27% | 1.7045% | -2.4927% | 0.684 | score 70-79 |
| SYMBOL_SIDE_SCORE_GE_60_BTCUSDT_LONG | REJECT_INSUFFICIENT_SAMPLE | symbol_side_score | 22 | 7.46% | -0.0837% | 0.4034% | 2.7195% | -3.5171% | 59.09% | 45.45% | 36.36% | 1.3381% | -1.5521% | 0.862 | BTC/USDT + LONG + score >= 60. |
| SYMBOL_SIDE_XRPUSDT_SHORT | REJECT_INSUFFICIENT_SAMPLE | symbol_side | 24 | 8.14% | -0.032% | -0.1308% | 3.1476% | -3.613% | 50.0% | 62.5% | 50.0% | 2.0466% | -2.0814% | 0.983 | XRP/USDT فقط SHORT. |
| SYMBOL_SIDE_SCORE_GE_60_SOLUSDT_LONG | REJECT_INSUFFICIENT_SAMPLE | symbol_side_score | 15 | 5.08% | -0.1358% | 0.1781% | 5.4035% | -4.6855% | 60.0% | 46.67% | 53.33% | 1.6051% | -2.4854% | 0.646 | SOL/USDT + LONG + score >= 60. |
| SYMBOL_SIDE_SOLUSDT_LONG | REJECT_INSUFFICIENT_SAMPLE | symbol_side | 24 | 8.14% | -0.0637% | 0.1365% | 5.4035% | -4.6855% | 54.17% | 45.83% | 54.17% | 2.0345% | -2.359% | 0.862 | SOL/USDT فقط LONG. |
| SYMBOL_SIDE_SCORE_GE_60_ETHUSDT_LONG | REJECT_INSUFFICIENT_SAMPLE | symbol_side_score | 11 | 3.73% | -0.2584% | 0.6531% | 2.8769% | -5.0698% | 54.55% | 45.45% | 45.45% | 1.7215% | -2.3947% | 0.719 | ETH/USDT + LONG + score >= 60. |
| SYMBOL_ACTIONABLE_DOGEUSDT | REJECT_INSUFFICIENT_SAMPLE | symbol_actionability | 10 | 3.39% | -0.1371% | -0.1261% | 3.5409% | -3.94% | 50.0% | 40.0% | 50.0% | 2.0676% | -2.7929% | 0.74 | DOGE/USDT + ACTIONABLE. |
| SYMBOL_SIDE_ETHUSDT_LONG | REJECT_INSUFFICIENT_SAMPLE | symbol_side | 20 | 6.78% | -0.3133% | 0.3026% | 2.8769% | -5.6986% | 55.0% | 50.0% | 50.0% | 1.6455% | -2.359% | 0.698 | ETH/USDT فقط LONG. |
| SYMBOL_SIDE_SCORE_GE_60_ETHUSDT_SHORT | REJECT_INSUFFICIENT_SAMPLE | symbol_side_score | 11 | 3.73% | -0.2758% | -0.5649% | 5.6706% | -4.3116% | 45.45% | 45.45% | 54.55% | 2.358% | -2.6642% | 0.885 | ETH/USDT + SHORT + score >= 60. |
| SYMBOL_SIDE_SCORE_GE_60_SOLUSDT_SHORT | REJECT_INSUFFICIENT_SAMPLE | symbol_side_score | 13 | 4.41% | -0.0705% | -0.3641% | 4.6736% | -5.2498% | 30.77% | 53.85% | 53.85% | 2.5528% | -2.6822% | 0.952 | SOL/USDT + SHORT + score >= 60. |
| HISTORICAL_EDGE_SCORE_GE_10 | REJECT_INSUFFICIENT_SAMPLE | component | 14 | 4.75% | -0.3625% | -0.0116% | 1.75% | -3.3236% | 50.0% | 28.57% | 35.71% | 1.0227% | -1.6945% | 0.604 | historical_edge_score >= 10. |
| SCORE_GE_70_SHORT | REJECT_INSUFFICIENT_SAMPLE | score_side | 21 | 7.12% | -0.2412% | -0.6433% | 3.3114% | -5.1034% | 38.1% | 47.62% | 47.62% | 2.0866% | -2.3307% | 0.895 | score >= 70 + SHORT. |
| SHORT_SCORE_GE_70 | REJECT_INSUFFICIENT_SAMPLE | component | 21 | 7.12% | -0.2412% | -0.6433% | 3.3114% | -5.1034% | 38.1% | 47.62% | 47.62% | 2.0866% | -2.3307% | 0.895 | short_score >= 70. |
| SYMBOL_SIDE_XRPUSDT_LONG | REJECT_INSUFFICIENT_SAMPLE | symbol_side | 17 | 5.76% | -0.319% | 0.0624% | 4.6531% | -4.3192% | 52.94% | 35.29% | 52.94% | 1.6464% | -2.4839% | 0.663 | XRP/USDT فقط LONG. |
| SYMBOL_SIDE_ETHUSDT_SHORT | REJECT_INSUFFICIENT_SAMPLE | symbol_side | 28 | 9.49% | -0.4317% | -0.4215% | 5.6706% | -4.4434% | 39.29% | 50.0% | 39.29% | 2.007% | -2.3344% | 0.86 | ETH/USDT فقط SHORT. |
| SYMBOL_SIDE_BNBUSDT_SHORT | REJECT_INSUFFICIENT_SAMPLE | symbol_side | 20 | 6.78% | -0.285% | -0.832% | 3.3114% | -2.8205% | 35.0% | 40.0% | 45.0% | 1.5992% | -1.7962% | 0.89 | BNB/USDT فقط SHORT. |
| ACTIONABLE_SHORT | REJECT_INSUFFICIENT_SAMPLE | actionability_side | 16 | 5.42% | -0.2818% | -1.0805% | 3.3114% | -3.5864% | 37.5% | 37.5% | 50.0% | 1.9146% | -2.1925% | 0.873 | ACTIONABLE فقط سمت SHORT. |
| ACTIONABLE_SCORE_GE_50_SHORT | REJECT_INSUFFICIENT_SAMPLE | actionability_score_side | 16 | 5.42% | -0.2818% | -1.0805% | 3.3114% | -3.5864% | 37.5% | 37.5% | 50.0% | 1.9146% | -2.1925% | 0.873 | ACTIONABLE + score >= 50 + SHORT. |
| ACTIONABLE_SCORE_GE_60_SHORT | REJECT_INSUFFICIENT_SAMPLE | actionability_score_side | 16 | 5.42% | -0.2818% | -1.0805% | 3.3114% | -3.5864% | 37.5% | 37.5% | 50.0% | 1.9146% | -2.1925% | 0.873 | ACTIONABLE + score >= 60 + SHORT. |
| ACTIONABLE_SCORE_GE_70_SHORT | REJECT_INSUFFICIENT_SAMPLE | actionability_score_side | 16 | 5.42% | -0.2818% | -1.0805% | 3.3114% | -3.5864% | 37.5% | 37.5% | 50.0% | 1.9146% | -2.1925% | 0.873 | ACTIONABLE + score >= 70 + SHORT. |
| SHORT_SCORE60_ACTIONABLE | REJECT_INSUFFICIENT_SAMPLE | composite | 16 | 5.42% | -0.2818% | -1.0805% | 3.3114% | -3.5864% | 37.5% | 37.5% | 50.0% | 1.9146% | -2.1925% | 0.873 | SHORT + ACTIONABLE + score>=60. |
| SYMBOL_SIDE_SCORE_GE_60_DOGEUSDT_LONG | REJECT_INSUFFICIENT_SAMPLE | symbol_side_score | 15 | 5.08% | -0.5703% | -0.3893% | 3.5409% | -6.4619% | 40.0% | 46.67% | 46.67% | 2.1405% | -2.5641% | 0.835 | DOGE/USDT + LONG + score >= 60. |
| REGIME_SIDEWAYS | REJECT_INSUFFICIENT_SAMPLE | regime | 10 | 3.39% | -0.5985% | -1.1648% | 1.9481% | -3.3227% | 40.0% | 50.0% | 60.0% | 2.0087% | -2.2926% | 0.876 | فقط regime=SIDEWAYS. |
| SYMBOL_SIDE_DOGEUSDT_LONG | REJECT_INSUFFICIENT_SAMPLE | symbol_side | 23 | 7.8% | -0.5396% | -0.4916% | 3.9741% | -6.4619% | 39.13% | 47.83% | 52.17% | 2.4122% | -2.6435% | 0.912 | DOGE/USDT فقط LONG. |
| SYMBOL_SIDE_BTCUSDT_SHORT | REJECT_INSUFFICIENT_SAMPLE | symbol_side | 19 | 6.44% | -0.4553% | -0.4804% | 5.98% | -5.1034% | 36.84% | 36.84% | 52.63% | 1.8481% | -2.1853% | 0.846 | BTC/USDT فقط SHORT. |
| SYMBOL_SIDE_SOLUSDT_SHORT | REJECT_INSUFFICIENT_SAMPLE | symbol_side | 29 | 9.83% | -0.6327% | -0.5433% | 6.9713% | -10.3172% | 37.93% | 48.28% | 51.72% | 2.3891% | -3.1154% | 0.767 | SOL/USDT فقط SHORT. |
| REGIME_UNKNOWN | REJECT_INSUFFICIENT_SAMPLE | regime | 10 | 3.39% | -1.4731% | -1.4772% | 0.8196% | -5.3012% | 20.0% | 20.0% | 40.0% | 1.5277% | -2.2235% | 0.687 | فقط regime=UNKNOWN. |
| SYMBOL_SIDE_SCORE_GE_80_XRPUSDT_LONG | REJECT_TOO_SMALL | symbol_side_score | 1 | 0.34% | 4.6531% | 4.6531% | 4.6531% | 4.6531% | 100.0% | 100.0% | 0.0% | 4.7767% | -1.3503% | 3.538 | XRP/USDT + LONG + score >= 80. |
| SYMBOL_SIDE_SCORE_GE_80_BNBUSDT_SHORT | REJECT_TOO_SMALL | symbol_side_score | 1 | 0.34% | 3.3114% | 3.3114% | 3.3114% | 3.3114% | 100.0% | 100.0% | 0.0% | 4.2989% | -0.9139% | 4.704 | BNB/USDT + SHORT + score >= 80. |
| SYMBOL_SIDE_SCORE_GE_80_BTCUSDT_SHORT | REJECT_TOO_SMALL | symbol_side_score | 1 | 0.34% | 2.1183% | 2.1183% | 2.1183% | 2.1183% | 100.0% | 100.0% | 0.0% | 3.1668% | -0.7856% | 4.031 | BTC/USDT + SHORT + score >= 80. |
| SYMBOL_SIDE_ACTIONABLE_BNBUSDT_LONG | REJECT_TOO_SMALL | symbol_side_actionability | 6 | 2.03% | 0.9173% | 1.1622% | 1.788% | -0.6931% | 83.33% | 100.0% | 33.33% | 2.5255% | -0.9158% | 2.758 | BNB/USDT + LONG + ACTIONABLE. |
| SYMBOL_ACTIONABLE_BNBUSDT | REJECT_TOO_SMALL | symbol_actionability | 9 | 3.05% | 1.0104% | 1.2726% | 3.3114% | -2.4441% | 77.78% | 88.89% | 33.33% | 2.8408% | -1.1226% | 2.531 | BNB/USDT + ACTIONABLE. |
| SCORE_GE_80_SHORT | REJECT_TOO_SMALL | score_side | 4 | 1.36% | 1.3445% | 2.5575% | 3.3114% | -3.0484% | 75.0% | 75.0% | 25.0% | 2.925% | -2.0213% | 1.447 | score >= 80 + SHORT. |
| VOLUME_SCORE_GE_15 | REJECT_TOO_SMALL | component | 6 | 2.03% | 0.9725% | 1.3481% | 3.2087% | -1.6931% | 66.67% | 83.33% | 33.33% | 2.8219% | -1.7596% | 1.604 | volume_score >= 15. |
| SYMBOL_SIDE_SCORE_GE_80_BNBUSDT_LONG | REJECT_TOO_SMALL | symbol_side_score | 4 | 1.36% | 0.729% | 0.9105% | 1.788% | -0.6931% | 75.0% | 100.0% | 50.0% | 1.9031% | -1.151% | 1.653 | BNB/USDT + LONG + score >= 80. |
| SYMBOL_SIDE_ACTIONABLE_BNBUSDT_SHORT | REJECT_TOO_SMALL | symbol_side_actionability | 3 | 1.02% | 1.1968% | 2.7232% | 3.3114% | -2.4441% | 66.67% | 66.67% | 33.33% | 3.4714% | -1.5362% | 2.26 | BNB/USDT + SHORT + ACTIONABLE. |
| ACTIONABLE_SCORE_GE_80_SHORT | REJECT_TOO_SMALL | actionability_score_side | 3 | 1.02% | 1.0865% | 2.9966% | 3.3114% | -3.0484% | 66.67% | 66.67% | 33.33% | 2.8444% | -2.4332% | 1.169 | ACTIONABLE + score >= 80 + SHORT. |
| SYMBOL_SIDE_SCORE_GE_80_DOGEUSDT_LONG | REJECT_TOO_SMALL | symbol_side_score | 3 | 1.02% | 0.8025% | 2.8066% | 3.5409% | -3.94% | 66.67% | 66.67% | 33.33% | 3.0634% | -2.3749% | 1.29 | DOGE/USDT + LONG + score >= 80. |
| SYMBOL_ACTIONABLE_XRPUSDT | REJECT_TOO_SMALL | symbol_actionability | 5 | 1.69% | 1.0802% | 0.1246% | 4.6531% | -1.3162% | 60.0% | 60.0% | 40.0% | 2.2592% | -1.8324% | 1.233 | XRP/USDT + ACTIONABLE. |
| SYMBOL_SIDE_ACTIONABLE_XRPUSDT_SHORT | REJECT_TOO_SMALL | symbol_side_actionability | 3 | 1.02% | 0.4143% | 0.1246% | 2.4345% | -1.3162% | 66.67% | 66.67% | 33.33% | 2.1014% | -1.4861% | 1.414 | XRP/USDT + SHORT + ACTIONABLE. |
| SYMBOL_SIDE_ACTIONABLE_XRPUSDT_LONG | REJECT_TOO_SMALL | symbol_side_actionability | 2 | 0.68% | 2.079% | 2.079% | 4.6531% | -0.4951% | 50.0% | 50.0% | 50.0% | 2.496% | -2.3518% | 1.061 | XRP/USDT + LONG + ACTIONABLE. |
| SYMBOL_SIDE_SCORE_GE_80_ETHUSDT_LONG | REJECT_TOO_SMALL | symbol_side_score | 2 | 0.68% | 0.5208% | 0.5208% | 2.0919% | -1.0502% | 50.0% | 50.0% | 50.0% | 2.0627% | -1.6347% | 1.262 | ETH/USDT + LONG + score >= 80. |
| CONFIDENCE_HIGH | REJECT_TOO_SMALL | confidence | 7 | 2.37% | 0.0955% | 0.453% | 3.3114% | -3.7227% | 57.14% | 42.86% | 57.14% | 1.6763% | -2.0381% | 0.822 | فقط confidence=High. |
| SYMBOL_SIDE_SCORE_GE_80_DOGEUSDT_SHORT | REJECT_TOO_SMALL | symbol_side_score | 2 | 0.68% | -0.0259% | -0.0259% | 2.9966% | -3.0484% | 50.0% | 50.0% | 50.0% | 2.1172% | -3.1928% | 0.663 | DOGE/USDT + SHORT + score >= 80. |
| SYMBOL_SIDE_ACTIONABLE_DOGEUSDT_LONG | REJECT_TOO_SMALL | symbol_side_actionability | 7 | 2.37% | 0.0017% | 0.1371% | 3.5409% | -3.94% | 57.14% | 42.86% | 57.14% | 2.1022% | -2.7917% | 0.753 | DOGE/USDT + LONG + ACTIONABLE. |
| RISK_HIGH | REJECT_TOO_SMALL | risk | 8 | 2.71% | -0.4264% | -0.0551% | 2.8058% | -4.3192% | 50.0% | 50.0% | 37.5% | 2.7212% | -3.5938% | 0.757 | فقط risk_label=High. |
| SCORE_BUCKET_90_PLUS | REJECT_TOO_SMALL | score_bucket | 1 | 0.34% | 0.453% | 0.453% | 0.453% | 0.453% | 100.0% | 0.0% | 100.0% | 0.5583% | -2.2619% | 0.247 | score >= 90 |
| SYMBOL_SIDE_ACTIONABLE_SOLUSDT_LONG | REJECT_TOO_SMALL | symbol_side_actionability | 6 | 2.03% | -0.3615% | -1.1837% | 5.4035% | -4.6855% | 50.0% | 50.0% | 66.67% | 1.9459% | -2.9698% | 0.655 | SOL/USDT + LONG + ACTIONABLE. |
| SYMBOL_SIDE_ACTIONABLE_DOGEUSDT_SHORT | REJECT_TOO_SMALL | symbol_side_actionability | 3 | 1.02% | -0.4608% | -1.3307% | 2.9966% | -3.0484% | 33.33% | 33.33% | 33.33% | 1.987% | -2.7957% | 0.711 | DOGE/USDT + SHORT + ACTIONABLE. |
| SYMBOL_SIDE_SCORE_GE_60_XRPUSDT_LONG | REJECT_TOO_SMALL | symbol_side_score | 9 | 3.05% | -0.0458% | -0.4951% | 4.6531% | -3.3416% | 44.44% | 33.33% | 66.67% | 1.8289% | -2.7252% | 0.671 | XRP/USDT + LONG + score >= 60. |
| SYMBOL_ACTIONABLE_SOLUSDT | REJECT_TOO_SMALL | symbol_actionability | 8 | 2.71% | -0.4213% | -0.6006% | 5.4035% | -4.6855% | 37.5% | 37.5% | 62.5% | 1.6163% | -2.6592% | 0.608 | SOL/USDT + ACTIONABLE. |
| REGIME_QUIET | REJECT_TOO_SMALL | regime | 1 | 0.34% | -0.182% | -0.182% | -0.182% | -0.182% | 0.0% | 0.0% | 0.0% | 1.4364% | -1.3413% | 1.071 | فقط regime=QUIET. |
| SYMBOL_SIDE_ACTIONABLE_ETHUSDT_SHORT | REJECT_TOO_SMALL | symbol_side_actionability | 3 | 1.02% | -1.1287% | -1.289% | 1.4892% | -3.5864% | 33.33% | 33.33% | 66.67% | 1.8321% | -3.2316% | 0.567 | ETH/USDT + SHORT + ACTIONABLE. |
| SYMBOL_SIDE_ACTIONABLE_BTCUSDT_LONG | REJECT_TOO_SMALL | symbol_side_actionability | 5 | 1.69% | -0.9782% | -1.3951% | 1.9392% | -3.5171% | 40.0% | 20.0% | 80.0% | 0.612% | -2.3969% | 0.255 | BTC/USDT + LONG + ACTIONABLE. |
| SYMBOL_SIDE_SCORE_GE_80_BTCUSDT_LONG | REJECT_TOO_SMALL | symbol_side_score | 5 | 1.69% | -1.0161% | -1.3951% | 1.75% | -3.5171% | 40.0% | 20.0% | 80.0% | 0.6001% | -2.3296% | 0.258 | BTC/USDT + LONG + score >= 80. |
| SYMBOL_ACTIONABLE_ETHUSDT | REJECT_TOO_SMALL | symbol_actionability | 7 | 2.37% | -1.1492% | -1.0502% | 2.0919% | -5.0698% | 28.57% | 28.57% | 71.43% | 1.4168% | -3.2597% | 0.435 | ETH/USDT + ACTIONABLE. |
| SYMBOL_SIDE_ACTIONABLE_ETHUSDT_LONG | REJECT_TOO_SMALL | symbol_side_actionability | 4 | 1.36% | -1.1646% | -0.8403% | 2.0919% | -5.0698% | 25.0% | 25.0% | 75.0% | 1.1054% | -3.2809% | 0.337 | ETH/USDT + LONG + ACTIONABLE. |
| SYMBOL_SIDE_ACTIONABLE_SOLUSDT_SHORT | REJECT_TOO_SMALL | symbol_side_actionability | 2 | 0.68% | -0.6006% | -0.6006% | -0.1671% | -1.0341% | 0.0% | 0.0% | 50.0% | 0.6274% | -1.7275% | 0.363 | SOL/USDT + SHORT + ACTIONABLE. |
| SYMBOL_SIDE_SCORE_GE_60_BTCUSDT_SHORT | REJECT_TOO_SMALL | symbol_side_score | 9 | 3.05% | -1.1671% | -1.1269% | 2.1183% | -5.1034% | 22.22% | 22.22% | 66.67% | 1.3389% | -2.7013% | 0.496 | BTC/USDT + SHORT + score >= 60. |
| SYMBOL_ACTIONABLE_BTCUSDT | REJECT_TOO_SMALL | symbol_actionability | 7 | 2.37% | -1.1805% | -1.3951% | 1.9392% | -3.5171% | 28.57% | 14.29% | 85.71% | 0.609% | -2.3515% | 0.259 | BTC/USDT + ACTIONABLE. |
| SYMBOL_SIDE_ACTIONABLE_BTCUSDT_SHORT | REJECT_TOO_SMALL | symbol_side_actionability | 2 | 0.68% | -1.6864% | -1.6864% | -1.1269% | -2.2458% | 0.0% | 0.0% | 100.0% | 0.6015% | -2.238% | 0.269 | BTC/USDT + SHORT + ACTIONABLE. |
| SYMBOL_SIDE_SCORE_GE_80_SOLUSDT_LONG | REJECT_TOO_SMALL | symbol_side_score | 1 | 0.34% | -3.7227% | -3.7227% | -3.7227% | -3.7227% | 0.0% | 0.0% | 100.0% | 0.1025% | -4.3716% | 0.023 | SOL/USDT + LONG + score >= 80. |

## Research Blockers
- Baseline Backtest هنوز میانگین مثبت ندارد.

## Recommendations
- بهترین gate تحقیقاتی با sample کافی: VOLUME_SCORE_GE_10 | avg=0.7131% | samples=34 | verdict=RESEARCH_CANDIDATE.
- این gate هنوز فقط research candidate است؛ قبل از Paper واقعی باید در Forward/Paper آینده هم تأیید شود.
- ACTIONABLE فعلی هنوز مثبت نیست: avg=-0.1425%، stop=56.52%. گیت actionability باید سخت‌تر شود.
- score>=80 را جدا نگه دار: samples=20, avg=0.3797%. اگر sample کم است، فقط research watchlist باشد.

## Safety Notes
- Gate Simulator فقط فیلترهای live-known را تست می‌کند؛ target/stop/return/MFE/MAE برای فیلتر استفاده نشده‌اند.
- BACKTEST جای FORWARD_TEST و Paper واقعی را نمی‌گیرد؛ candidateها فقط برای تحقیق هستند.
- subsetهای کم‌نمونه می‌توانند overfit باشند؛ sample حداقل و تأیید forward لازم است.