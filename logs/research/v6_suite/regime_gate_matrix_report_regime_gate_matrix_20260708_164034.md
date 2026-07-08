==============================================================================================================
🧬 Freakto Regime-Split Gate Matrix v6.1.0
==============================================================================================================
Status: REGIME_GATE_CANDIDATES_FOUND
Run ID: regime_gate_matrix_20260708_164034
Horizon: 24h
Min Samples: 10 | Candidate Min Samples: 30
Baseline Net: samples=295 | avg=-0.4009% | win=43.73% | T1=48.14% | Stop=47.12%
Regimes Seen: QUIET, SIDEWAYS, TRENDING_BEAR, TRENDING_BULL, UNKNOWN
Gates Tested: 17 | Candidates: 4

Regime Candidates:
- TRENDING_BEAR × STRUCTURE_SCORE_GE_10: verdict=REGIME_RESEARCH_CANDIDATE | samples=47 | net_avg_pct=0.6404 | win_rate=57.45 | target_1_hit_rate=65.96 | stop_hit_rate=38.3 | mfe_mae_ratio=1.296 | score=0.9828
- TRENDING_BEAR × RISK_MEDIUM: verdict=REGIME_RESEARCH_CANDIDATE | samples=37 | net_avg_pct=0.5946 | win_rate=56.76 | target_1_hit_rate=62.16 | stop_hit_rate=27.03 | mfe_mae_ratio=1.475 | score=0.923
- TRENDING_BEAR × STRUCTURE_SCORE_GE_10 × SHORT: verdict=REGIME_RESEARCH_CANDIDATE | samples=47 | net_avg_pct=0.6404 | win_rate=57.45 | target_1_hit_rate=65.96 | stop_hit_rate=38.3 | mfe_mae_ratio=1.296 | score=0.9828
- TRENDING_BEAR × RISK_MEDIUM × SHORT: verdict=REGIME_RESEARCH_CANDIDATE | samples=37 | net_avg_pct=0.5946 | win_rate=56.76 | target_1_hit_rate=62.16 | stop_hit_rate=27.03 | mfe_mae_ratio=1.475 | score=0.923

Top Regime × Gate:
- TRENDING_BEAR × STRUCTURE_SCORE_GE_10: verdict=REGIME_RESEARCH_CANDIDATE | samples=47 | net_avg_pct=0.6404 | win_rate=57.45 | target_1_hit_rate=65.96 | stop_hit_rate=38.3 | mfe_mae_ratio=1.296 | score=0.9828
- TRENDING_BEAR × RISK_MEDIUM: verdict=REGIME_RESEARCH_CANDIDATE | samples=37 | net_avg_pct=0.5946 | win_rate=56.76 | target_1_hit_rate=62.16 | stop_hit_rate=27.03 | mfe_mae_ratio=1.475 | score=0.923
- TRENDING_BEAR × VOLUME_SCORE_GE_10: verdict=POSITIVE_LOW_SAMPLE | samples=12 | net_avg_pct=0.949 | win_rate=58.33 | target_1_hit_rate=75.0 | stop_hit_rate=33.33 | mfe_mae_ratio=1.512 | score=1.3464
- TRENDING_BEAR × QUALITY_STRUCTURE_RISK_MEDIUM: verdict=POSITIVE_LOW_SAMPLE | samples=24 | net_avg_pct=0.7975 | win_rate=58.33 | target_1_hit_rate=66.67 | stop_hit_rate=33.33 | mfe_mae_ratio=1.487 | score=1.1862
- TRENDING_BULL × BNB_LONG_SCORE_GE_60: verdict=POSITIVE_LOW_SAMPLE | samples=11 | net_avg_pct=0.3533 | win_rate=72.73 | target_1_hit_rate=72.73 | stop_hit_rate=54.55 | mfe_mae_ratio=1.374 | score=0.7183
- TRENDING_BULL × VOLUME_SCORE_GE_10: verdict=POSITIVE_LOW_SAMPLE | samples=17 | net_avg_pct=0.4073 | win_rate=70.59 | target_1_hit_rate=76.47 | stop_hit_rate=52.94 | mfe_mae_ratio=1.012 | score=0.7139
- TRENDING_BEAR × DOGE_SHORT_WATCH: verdict=POSITIVE_LOW_SAMPLE | samples=25 | net_avg_pct=0.0809 | win_rate=40.0 | target_1_hit_rate=52.0 | stop_hit_rate=32.0 | mfe_mae_ratio=1.207 | score=0.032
- TRENDING_BULL × HISTORICAL_EDGE_SCORE_GE_1: verdict=NET_NEGATIVE_AFTER_COST | samples=31 | net_avg_pct=-0.126 | win_rate=58.06 | target_1_hit_rate=48.39 | stop_hit_rate=35.48 | mfe_mae_ratio=0.971 | score=0.0104
- TRENDING_BULL × SCORE_GE_80: verdict=NET_NEGATIVE_AFTER_COST | samples=16 | net_avg_pct=-0.0115 | win_rate=56.25 | target_1_hit_rate=56.25 | stop_hit_rate=56.25 | mfe_mae_ratio=0.89 | score=-0.0564
- TRENDING_BULL × SCORE_60_69: verdict=NET_NEGATIVE_AFTER_COST | samples=39 | net_avg_pct=-0.099 | win_rate=53.85 | target_1_hit_rate=43.59 | stop_hit_rate=43.59 | mfe_mae_ratio=0.888 | score=-0.0783
- TRENDING_BEAR × XRP_SHORT_SCORE_GE_60: verdict=NET_NEGATIVE_AFTER_COST | samples=15 | net_avg_pct=-0.137 | win_rate=40.0 | target_1_hit_rate=66.67 | stop_hit_rate=46.67 | mfe_mae_ratio=1.088 | score=-0.1864
- TRENDING_BULL × ACTIONABLE_SCORE_GE_80: verdict=NET_NEGATIVE_AFTER_COST | samples=15 | net_avg_pct=-0.119 | win_rate=53.33 | target_1_hit_rate=53.33 | stop_hit_rate=60.0 | mfe_mae_ratio=0.828 | score=-0.2594
- TRENDING_BULL × ACTIONABLE: verdict=NET_NEGATIVE_AFTER_COST | samples=30 | net_avg_pct=-0.2182 | win_rate=50.0 | target_1_hit_rate=50.0 | stop_hit_rate=60.0 | mfe_mae_ratio=0.743 | score=-0.3735
- TRENDING_BEAR × SCORE_GE_70: verdict=NET_NEGATIVE_AFTER_COST | samples=21 | net_avg_pct=-0.3912 | win_rate=33.33 | target_1_hit_rate=47.62 | stop_hit_rate=47.62 | mfe_mae_ratio=0.895 | score=-0.6815
- TRENDING_BULL × QUALITY_STRUCTURE_RISK_MEDIUM: verdict=NET_NEGATIVE_AFTER_COST | samples=17 | net_avg_pct=-0.3857 | win_rate=41.18 | target_1_hit_rate=41.18 | stop_hit_rate=52.94 | mfe_mae_ratio=0.685 | score=-0.7217
- TRENDING_BEAR × ACTIONABLE: verdict=NET_NEGATIVE_AFTER_COST | samples=16 | net_avg_pct=-0.4318 | win_rate=31.25 | target_1_hit_rate=37.5 | stop_hit_rate=50.0 | mfe_mae_ratio=0.873 | score=-0.8236
- TRENDING_BEAR × SCORE_60_69: verdict=AVOID_CANDIDATE | samples=49 | net_avg_pct=-0.2188 | win_rate=40.82 | target_1_hit_rate=51.02 | stop_hit_rate=51.02 | mfe_mae_ratio=0.988 | score=-0.3496
- TRENDING_BEAR × WATCHLIST: verdict=AVOID_CANDIDATE | samples=86 | net_avg_pct=-0.2627 | win_rate=40.7 | target_1_hit_rate=54.65 | stop_hit_rate=50.0 | mfe_mae_ratio=1.012 | score=-0.365
- TRENDING_BULL × LONG_ONLY: verdict=AVOID_CANDIDATE | samples=136 | net_avg_pct=-0.3485 | win_rate=50.0 | target_1_hit_rate=48.53 | stop_hit_rate=50.0 | mfe_mae_ratio=0.804 | score=-0.3868
- TRENDING_BEAR × SHORT_ONLY: verdict=AVOID_CANDIDATE | samples=138 | net_avg_pct=-0.3394 | win_rate=39.86 | target_1_hit_rate=50.0 | stop_hit_rate=44.2 | mfe_mae_ratio=0.951 | score=-0.4349

Top Regime × Gate × Side:
- TRENDING_BEAR × STRUCTURE_SCORE_GE_10 × SHORT: verdict=REGIME_RESEARCH_CANDIDATE | samples=47 | net_avg_pct=0.6404 | win_rate=57.45 | target_1_hit_rate=65.96 | stop_hit_rate=38.3 | mfe_mae_ratio=1.296 | score=0.9828
- TRENDING_BEAR × RISK_MEDIUM × SHORT: verdict=REGIME_RESEARCH_CANDIDATE | samples=37 | net_avg_pct=0.5946 | win_rate=56.76 | target_1_hit_rate=62.16 | stop_hit_rate=27.03 | mfe_mae_ratio=1.475 | score=0.923
- TRENDING_BEAR × VOLUME_SCORE_GE_10 × SHORT: verdict=POSITIVE_LOW_SAMPLE | samples=12 | net_avg_pct=0.949 | win_rate=58.33 | target_1_hit_rate=75.0 | stop_hit_rate=33.33 | mfe_mae_ratio=1.512 | score=1.3464
- TRENDING_BEAR × QUALITY_STRUCTURE_RISK_MEDIUM × SHORT: verdict=POSITIVE_LOW_SAMPLE | samples=24 | net_avg_pct=0.7975 | win_rate=58.33 | target_1_hit_rate=66.67 | stop_hit_rate=33.33 | mfe_mae_ratio=1.487 | score=1.1862
- TRENDING_BULL × BNB_LONG_SCORE_GE_60 × LONG: verdict=POSITIVE_LOW_SAMPLE | samples=11 | net_avg_pct=0.3533 | win_rate=72.73 | target_1_hit_rate=72.73 | stop_hit_rate=54.55 | mfe_mae_ratio=1.374 | score=0.7183
- TRENDING_BULL × VOLUME_SCORE_GE_10 × LONG: verdict=POSITIVE_LOW_SAMPLE | samples=17 | net_avg_pct=0.4073 | win_rate=70.59 | target_1_hit_rate=76.47 | stop_hit_rate=52.94 | mfe_mae_ratio=1.012 | score=0.7139
- TRENDING_BEAR × DOGE_SHORT_WATCH × SHORT: verdict=POSITIVE_LOW_SAMPLE | samples=25 | net_avg_pct=0.0809 | win_rate=40.0 | target_1_hit_rate=52.0 | stop_hit_rate=32.0 | mfe_mae_ratio=1.207 | score=0.032
- TRENDING_BULL × HISTORICAL_EDGE_SCORE_GE_1 × LONG: verdict=NET_NEGATIVE_AFTER_COST | samples=31 | net_avg_pct=-0.126 | win_rate=58.06 | target_1_hit_rate=48.39 | stop_hit_rate=35.48 | mfe_mae_ratio=0.971 | score=0.0104
- TRENDING_BULL × SCORE_GE_80 × LONG: verdict=NET_NEGATIVE_AFTER_COST | samples=16 | net_avg_pct=-0.0115 | win_rate=56.25 | target_1_hit_rate=56.25 | stop_hit_rate=56.25 | mfe_mae_ratio=0.89 | score=-0.0564
- TRENDING_BULL × SCORE_60_69 × LONG: verdict=NET_NEGATIVE_AFTER_COST | samples=39 | net_avg_pct=-0.099 | win_rate=53.85 | target_1_hit_rate=43.59 | stop_hit_rate=43.59 | mfe_mae_ratio=0.888 | score=-0.0783
- TRENDING_BEAR × XRP_SHORT_SCORE_GE_60 × SHORT: verdict=NET_NEGATIVE_AFTER_COST | samples=15 | net_avg_pct=-0.137 | win_rate=40.0 | target_1_hit_rate=66.67 | stop_hit_rate=46.67 | mfe_mae_ratio=1.088 | score=-0.1864
- TRENDING_BULL × ACTIONABLE_SCORE_GE_80 × LONG: verdict=NET_NEGATIVE_AFTER_COST | samples=15 | net_avg_pct=-0.119 | win_rate=53.33 | target_1_hit_rate=53.33 | stop_hit_rate=60.0 | mfe_mae_ratio=0.828 | score=-0.2594
- TRENDING_BULL × ACTIONABLE × LONG: verdict=NET_NEGATIVE_AFTER_COST | samples=30 | net_avg_pct=-0.2182 | win_rate=50.0 | target_1_hit_rate=50.0 | stop_hit_rate=60.0 | mfe_mae_ratio=0.743 | score=-0.3735
- TRENDING_BEAR × SCORE_GE_70 × SHORT: verdict=NET_NEGATIVE_AFTER_COST | samples=21 | net_avg_pct=-0.3912 | win_rate=33.33 | target_1_hit_rate=47.62 | stop_hit_rate=47.62 | mfe_mae_ratio=0.895 | score=-0.6815
- TRENDING_BULL × QUALITY_STRUCTURE_RISK_MEDIUM × LONG: verdict=NET_NEGATIVE_AFTER_COST | samples=17 | net_avg_pct=-0.3857 | win_rate=41.18 | target_1_hit_rate=41.18 | stop_hit_rate=52.94 | mfe_mae_ratio=0.685 | score=-0.7217
- TRENDING_BEAR × ACTIONABLE × SHORT: verdict=NET_NEGATIVE_AFTER_COST | samples=16 | net_avg_pct=-0.4318 | win_rate=31.25 | target_1_hit_rate=37.5 | stop_hit_rate=50.0 | mfe_mae_ratio=0.873 | score=-0.8236
- TRENDING_BEAR × SCORE_60_69 × SHORT: verdict=AVOID_CANDIDATE | samples=49 | net_avg_pct=-0.2188 | win_rate=40.82 | target_1_hit_rate=51.02 | stop_hit_rate=51.02 | mfe_mae_ratio=0.988 | score=-0.3496
- TRENDING_BEAR × WATCHLIST × SHORT: verdict=AVOID_CANDIDATE | samples=86 | net_avg_pct=-0.2627 | win_rate=40.7 | target_1_hit_rate=54.65 | stop_hit_rate=50.0 | mfe_mae_ratio=1.012 | score=-0.365
- TRENDING_BULL × LONG_ONLY × LONG: verdict=AVOID_CANDIDATE | samples=136 | net_avg_pct=-0.3485 | win_rate=50.0 | target_1_hit_rate=48.53 | stop_hit_rate=50.0 | mfe_mae_ratio=0.804 | score=-0.3868
- TRENDING_BEAR × SHORT_ONLY × SHORT: verdict=AVOID_CANDIDATE | samples=138 | net_avg_pct=-0.3394 | win_rate=39.86 | target_1_hit_rate=50.0 | stop_hit_rate=44.2 | mfe_mae_ratio=0.951 | score=-0.4349

Top Regime × Side:
- TRENDING_BULL × LONG: verdict=AVOID_CANDIDATE | samples=136 | net_avg_pct=-0.3485 | win_rate=50.0 | target_1_hit_rate=48.53 | stop_hit_rate=50.0 | mfe_mae_ratio=0.804 | score=-0.3868
- TRENDING_BEAR × SHORT: verdict=AVOID_CANDIDATE | samples=138 | net_avg_pct=-0.3394 | win_rate=39.86 | target_1_hit_rate=50.0 | stop_hit_rate=44.2 | mfe_mae_ratio=0.951 | score=-0.4349
- SIDEWAYS × LONG: verdict=LOW_SAMPLE | samples=5 | net_avg_pct=0.0839 | win_rate=60.0 | target_1_hit_rate=60.0 | stop_hit_rate=60.0 | mfe_mae_ratio=1.828 | score=0.1779
- QUIET × LONG: verdict=LOW_SAMPLE | samples=1 | net_avg_pct=-0.332 | win_rate=0.0 | target_1_hit_rate=0.0 | stop_hit_rate=0.0 | mfe_mae_ratio=1.071 | score=-0.7747
- UNKNOWN × LONG: verdict=LOW_SAMPLE | samples=8 | net_avg_pct=-1.1793 | win_rate=25.0 | target_1_hit_rate=25.0 | stop_hit_rate=37.5 | mfe_mae_ratio=0.892 | score=-1.7219
- SIDEWAYS × SHORT: verdict=LOW_SAMPLE | samples=5 | net_avg_pct=-1.581 | win_rate=20.0 | target_1_hit_rate=40.0 | stop_hit_rate=60.0 | mfe_mae_ratio=0.4 | score=-2.4358
- UNKNOWN × SHORT: verdict=LOW_SAMPLE | samples=2 | net_avg_pct=-3.3984 | win_rate=0.0 | target_1_hit_rate=0.0 | stop_hit_rate=50.0 | mfe_mae_ratio=0.303 | score=-5.2314

Top Regime × Symbol:
- TRENDING_BEAR × DOGE/USDT: verdict=POSITIVE_LOW_SAMPLE | samples=25 | net_avg_pct=0.0809 | win_rate=40.0 | target_1_hit_rate=52.0 | stop_hit_rate=32.0 | mfe_mae_ratio=1.207 | score=0.032
- TRENDING_BEAR × XRP/USDT: verdict=NET_NEGATIVE_AFTER_COST | samples=24 | net_avg_pct=-0.182 | win_rate=45.83 | target_1_hit_rate=62.5 | stop_hit_rate=50.0 | mfe_mae_ratio=0.983 | score=-0.207
- TRENDING_BULL × SOL/USDT: verdict=NET_NEGATIVE_AFTER_COST | samples=21 | net_avg_pct=-0.118 | win_rate=52.38 | target_1_hit_rate=47.62 | stop_hit_rate=52.38 | mfe_mae_ratio=0.809 | score=-0.2431
- TRENDING_BULL × BNB/USDT: verdict=NET_NEGATIVE_AFTER_COST | samples=25 | net_avg_pct=-0.2483 | win_rate=52.0 | target_1_hit_rate=56.0 | stop_hit_rate=56.0 | mfe_mae_ratio=0.861 | score=-0.2829
- TRENDING_BEAR × BNB/USDT: verdict=NET_NEGATIVE_AFTER_COST | samples=19 | net_avg_pct=-0.3024 | win_rate=36.84 | target_1_hit_rate=42.11 | stop_hit_rate=42.11 | mfe_mae_ratio=1.009 | score=-0.5
- TRENDING_BULL × ETH/USDT: verdict=NET_NEGATIVE_AFTER_COST | samples=19 | net_avg_pct=-0.3873 | win_rate=52.63 | target_1_hit_rate=52.63 | stop_hit_rate=52.63 | mfe_mae_ratio=0.714 | score=-0.5228
- TRENDING_BEAR × SOL/USDT: verdict=NET_NEGATIVE_AFTER_COST | samples=25 | net_avg_pct=-0.4357 | win_rate=44.0 | target_1_hit_rate=56.0 | stop_hit_rate=48.0 | mfe_mae_ratio=0.887 | score=-0.6588
- TRENDING_BULL × XRP/USDT: verdict=NET_NEGATIVE_AFTER_COST | samples=17 | net_avg_pct=-0.469 | win_rate=47.06 | target_1_hit_rate=35.29 | stop_hit_rate=52.94 | mfe_mae_ratio=0.663 | score=-0.7936
- TRENDING_BEAR × ETH/USDT: verdict=NET_NEGATIVE_AFTER_COST | samples=26 | net_avg_pct=-0.6288 | win_rate=38.46 | target_1_hit_rate=46.15 | stop_hit_rate=42.31 | mfe_mae_ratio=0.815 | score=-0.871
- TRENDING_BEAR × BTC/USDT: verdict=NET_NEGATIVE_AFTER_COST | samples=19 | net_avg_pct=-0.6053 | win_rate=31.58 | target_1_hit_rate=36.84 | stop_hit_rate=52.63 | mfe_mae_ratio=0.846 | score=-1.047
- TRENDING_BULL × DOGE/USDT: verdict=NET_NEGATIVE_AFTER_COST | samples=20 | net_avg_pct=-0.7293 | win_rate=35.0 | target_1_hit_rate=50.0 | stop_hit_rate=55.0 | mfe_mae_ratio=0.863 | score=-1.1077
- TRENDING_BULL × BTC/USDT: verdict=AVOID_CANDIDATE | samples=34 | net_avg_pct=-0.2585 | win_rate=55.88 | target_1_hit_rate=47.06 | stop_hit_rate=38.24 | mfe_mae_ratio=0.881 | score=-0.1921
- UNKNOWN × BNB/USDT: verdict=LOW_SAMPLE | samples=2 | net_avg_pct=0.5455 | win_rate=100.0 | target_1_hit_rate=50.0 | stop_hit_rate=0.0 | mfe_mae_ratio=2.768 | score=1.5723
- SIDEWAYS × DOGE/USDT: verdict=LOW_SAMPLE | samples=1 | net_avg_pct=1.1504 | win_rate=100.0 | target_1_hit_rate=0.0 | stop_hit_rate=100.0 | mfe_mae_ratio=0.753 | score=1.2257
- SIDEWAYS × ETH/USDT: verdict=LOW_SAMPLE | samples=2 | net_avg_pct=0.0302 | win_rate=50.0 | target_1_hit_rate=100.0 | stop_hit_rate=0.0 | mfe_mae_ratio=1.648 | score=0.2487
- QUIET × BNB/USDT: verdict=LOW_SAMPLE | samples=1 | net_avg_pct=-0.332 | win_rate=0.0 | target_1_hit_rate=0.0 | stop_hit_rate=0.0 | mfe_mae_ratio=1.071 | score=-0.7747
- UNKNOWN × DOGE/USDT: verdict=LOW_SAMPLE | samples=2 | net_avg_pct=-1.2119 | win_rate=0.0 | target_1_hit_rate=50.0 | stop_hit_rate=0.0 | mfe_mae_ratio=1.839 | score=-1.6899
- SIDEWAYS × SOL/USDT: verdict=LOW_SAMPLE | samples=4 | net_avg_pct=-1.085 | win_rate=25.0 | target_1_hit_rate=25.0 | stop_hit_rate=75.0 | mfe_mae_ratio=0.716 | score=-1.9962
- SIDEWAYS × BNB/USDT: verdict=LOW_SAMPLE | samples=3 | net_avg_pct=-1.4521 | win_rate=33.33 | target_1_hit_rate=66.67 | stop_hit_rate=66.67 | mfe_mae_ratio=0.767 | score=-2.0537
- UNKNOWN × ETH/USDT: verdict=LOW_SAMPLE | samples=1 | net_avg_pct=-1.9089 | win_rate=0.0 | target_1_hit_rate=0.0 | stop_hit_rate=0.0 | mfe_mae_ratio=0.396 | score=-2.6556

Avoid Regimes:
- UNKNOWN: AVOID | n=10 | net=-1.6231% | win=20.0% | T1=20.0% | Stop=40.0%
- SIDEWAYS: AVOID | n=10 | net=-0.7485% | win=40.0% | T1=50.0% | Stop=60.0%
- TRENDING_BULL: WEAK_NEGATIVE | n=136 | net=-0.3485% | win=50.0% | T1=48.53% | Stop=50.0%
- TRENDING_BEAR: WEAK_NEGATIVE | n=138 | net=-0.3394% | win=39.86% | T1=50.0% | Stop=44.2%
- QUIET: LOW_SAMPLE | n=1 | net=-0.332% | win=0.0% | T1=0.0% | Stop=0.0%

Shadow Proposals:
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10: mode=SHADOW_ONLY | n=47 | net=0.6404% | filters=structure_score__ge=10, regime_label=TRENDING_BEAR
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT: mode=SHADOW_ONLY | n=47 | net=0.6404% | filters=structure_score__ge=10, regime_label=TRENDING_BEAR, side=SHORT
- REGIME_TRENDING_BEAR__RISK_MEDIUM: mode=SHADOW_ONLY | n=37 | net=0.5946% | filters=risk_label=Medium, regime_label=TRENDING_BEAR
- REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT: mode=SHADOW_ONLY | n=37 | net=0.5946% | filters=risk_label=Medium, regime_label=TRENDING_BEAR, side=SHORT

Blockers:
⛔ Baseline net return کلی هنوز مثبت نیست.

Recommendations:
→ بهترین ترکیب Regime/Gate فعلی: TRENDING_BEAR × STRUCTURE_SCORE_GE_10 با net=0.6404% و n=47.
→ این ترکیب فقط باید در Shadow Forward رصد شود؛ هنوز Paper/Live مجاز نیست.
→ Regimeهای خام مشکوک برای Avoid/Watch بدون Gate: UNKNOWN, SIDEWAYS.
→ horizon اصلی فعلاً 24h بماند؛ 4h و 12h قبلاً بعد از cost/stability candidate ندادند.

Warnings:
⚠️ Regime label باید در Forward هم ثبت و validate شود؛ Backtest به تنهایی کافی نیست.
⚠️ گروه‌های کم‌نمونه می‌توانند overfit باشند؛ sample و window stability باید رشد کند.
⚠️ این ماژول فقط از داده‌های live-known برای فیلتر استفاده می‌کند؛ outcomeها فقط برای ارزیابی‌اند.
==============================================================================================================