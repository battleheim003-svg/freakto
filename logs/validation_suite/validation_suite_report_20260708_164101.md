==============================================================================================================
📘 Freakto Metric Definitions v4.7.1
==============================================================================================================
هدف: حذف ابهام بین Directional Win Rate، Target Hit Rate و Paper Trade Win Rate.

--------------------------------------------------------------------------------------------------------------
Metric    : Directional Win Rate
Label     : Dir Win
Source    : decision_evaluations.csv
Formula   : count(return_after_24h_pct > 0) / count(valid evaluated returns)
Meaning   : درصد تصمیم‌هایی که بازده ارزیابی‌شده آن‌ها مثبت شده است. اگر 24h هنوز موجود نباشد، ماژول‌های ارزیابی ممکن است به 12h یا 4h fallback کنند.
Used In   : Edge Validation, Walk-Forward, Live Readiness notes
--------------------------------------------------------------------------------------------------------------
Metric    : Target 1 Hit Rate
Label     : T1 Hit
Source    : decision_evaluations.csv
Formula   : count(target_1_hit == True) / count(COMPLETE evaluations)
Meaning   : درصد تصمیم‌هایی که تارگت اول را زده‌اند. این با مثبت بودن بازده یکی نیست؛ ممکن است بازده مثبت باشد ولی T1 نخورده باشد.
Used In   : Strategy Lab, Regime Matrix, historical target validation
--------------------------------------------------------------------------------------------------------------
Metric    : Paper Trade Win Rate
Label     : Paper Win
Source    : paper_trade_evaluations.csv
Formula   : count(closed paper trades with positive R or WIN result) / count(closed paper trades)
Meaning   : درصد معاملات فرضی بسته‌شده که بر اساس R Multiple یا نتیجه ثبت‌شده سودده بوده‌اند.
Used In   : Paper Trading, Live Readiness
--------------------------------------------------------------------------------------------------------------
Metric    : Expectancy
Label     : Expectancy
Source    : decision_evaluations.csv / paper_trade_evaluations.csv
Formula   : average(return_after_24h_pct) for decisions OR average(r_multiple) for paper trades
Meaning   : میانگین سود/زیان مورد انتظار در نمونه‌های موجود. برای تصمیم‌ها درصدی و برای Paper Trade بر حسب R است.
Used In   : Edge Validation, Live Readiness, Strategy Lab
--------------------------------------------------------------------------------------------------------------
Metric    : Profit Factor
Label     : PF
Source    : evaluated returns
Formula   : gross positive returns / abs(gross negative returns)
Meaning   : نسبت مجموع سودها به مجموع زیان‌ها. در نمونه‌های خیلی کم یا بدون زیان می‌تواند بزرگ و ناپایدار باشد.
Used In   : Edge Validation, Regime Matrix, Live Readiness
==============================================================================================================

==============================================================================================================
📐 Freakto Edge Validation Engine v4.7.1
==============================================================================================================
Created UTC      : 2026-07-08T16:40:58.675073+00:00
Combined Quality : EARLY_EDGE_OBSERVED

--------------------------------------------------------------------------------------------------------------
Source       : decision_evaluations
Quality      : EARLY_POSITIVE_LOW_SAMPLE
Samples      : 17 | Positive/Negative/Flat: 17/0/0
Directional Win Rate: 100.00%
Expectancy   : 1.0470pct
ProfitFactor : 17.7989
Sharpe-like  : 8.6425 | Sortino-like: 0.0000
Max Drawdown : 0.0000pct
Best/Worst   : 1.8346pct / 0.4897pct
Avg Win/Loss : 1.0470pct / 0.0000pct
Stop Rate    : 0.00%
Target Hit   : T1 64.71% | T2 0.00% | T3 0.00%
Definition   : Directional Win = positive evaluated return; Target Hit = target_1_hit.
MFE/MAE Avg  : 1.5843% / -0.2997%
Note         : Expectancy و Directional Win Rate فعلاً مثبت هستند.
Warning      : نمونه کمتر از 30 است؛ نتیجه فقط سیگنال اولیه است.
--------------------------------------------------------------------------------------------------------------
Source       : paper_trade_evaluations
Quality      : NO_DATA
Samples      : 0 | Wins/Losses/Flat: 0/0/0
Paper Trade Win Rate: 0.00%
Expectancy   : 0.0000R
ProfitFactor : 0.0000
Sharpe-like  : 0.0000 | Sortino-like: 0.0000
Max Drawdown : 0.0000R
Best/Worst   : 0.0000R / 0.0000R
Avg Win/Loss : 0.0000R / 0.0000R
Stop Rate    : 0.00%
Definition   : Paper Trade Win = closed paper trades with positive R multiple.
Warning      : هنوز Paper Trade ارزیابی‌شده وجود ندارد.

Overall Notes:
✓ Decision Directional Win Rate و Expectancy فعلاً مثبت‌اند، اما تا رسیدن به نمونه کافی فقط تحقیقاتی محسوب می‌شوند.
✓ Paper edge هنوز شروع نشده یا معامله بسته‌شده ندارد.

Validation Blockers:
⛔ Decision COMPLETE کمتر از 100 است: 17
⛔ Paper trades بسته‌شده کمتر از 30 است: 0
==============================================================================================================

==============================================================================================================
🧬 Freakto Regime Performance Matrix v4.7.1
==============================================================================================================
Created UTC          : 2026-07-08T16:40:58.693740+00:00
Overall Verdict      : REGIME_DATA_MISSING
Known/Unknown Regime : 0 / 17
Best/Worst Regime    : UNKNOWN / UNKNOWN

Warnings:
⚠️ بیشتر نمونه‌ها regime_label ندارند؛ چند اجرای جدید monitor.py بعد از v4.7 لازم است.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : UNKNOWN / LONG / WATCHLIST
Samples            : 14
Target 1 Hit       : 64.29%
Directional Win    : 100.00%
Avg 24h            : 0.9748%
Profit Factor      : 13.6475
Stop Rate          : 0.00%
Avg Score          : 66.50
Verdict            : REGIME_POSITIVE
Note               : Regime در لاگ‌های قدیمی ثبت نشده؛ برای تصمیم‌گیری نیاز به داده v4.7 به بعد است.
Note               : در این رژیم نشانه اولیه Edge مثبت دیده می‌شود.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : UNKNOWN / LONG / NOT_ACTIONABLE
Samples            : 2
Target 1 Hit       : 100.00%
Directional Win    : 100.00%
Avg 24h            : 1.8308%
Profit Factor      : 3.6617
Stop Rate          : 0.00%
Avg Score          : 53.00
Verdict            : LOW_SAMPLE
Note               : نمونه کمتر از 5 است؛ فقط برای رصد.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : UNKNOWN / LONG / ACTIONABLE
Samples            : 1
Target 1 Hit       : 0.00%
Directional Win    : 100.00%
Avg 24h            : 0.4897%
Profit Factor      : 0.4897
Stop Rate          : 0.00%
Avg Score          : 70.00
Verdict            : LOW_SAMPLE
Note               : نمونه کمتر از 5 است؛ فقط برای رصد.
==============================================================================================================

==============================================================================================================
🧠 Freakto Portfolio Memory Engine v5.0
==============================================================================================================
Created UTC       : 2026-07-08T16:40:58.707350+00:00
Portfolio Status  : MEMORY_BUILDING
Symbols           : 1
Total scans       : 0
Complete evals    : 17
Closed paper      : 0
Best memory symbol: BTC/USDT
Best paper symbol : NONE

Warnings:
⚠️ Closed paper trades کل پورتفو کمتر از 30 است: 0
--------------------------------------------------------------------------------------------------------------
Symbol        : BTC/USDT
Status        : OBSERVATION_ONLY | Confidence LOW_MEDIUM
Scans/Dec/Eval: 0 / 32 / 17
Latest        : UNKNOWN | Rec UNKNOWN | MTF UNKNOWN
Avg Score/Conf/Opp: 0.00 / 0.00% / 0.00
Directional/T1/Avg24: 100.00% / 64.71% / 1.0470%
Paper        : closed 0 | win 0.00% | exp 0.0000R | PF 0.0000
Rec rates    : actionable 0.00% | monitor 0.00% | ignore 0.00%
Note         : حافظه نماد فعلاً فقط مشاهده‌ای است.
Blocker      : Complete evaluations کمتر از 30 است: 17
Blocker      : Closed paper trades کمتر از 30 است: 0
==============================================================================================================

==============================================================================================================
🎯 Freakto Confidence Calibration Engine v5.0
==============================================================================================================
Created UTC       : 2026-07-08T16:40:58.716355+00:00
Quality           : LOW_SAMPLE_CALIBRATION
Samples           : 17
Overall Dir Win   : 100.00%
Overall T1 Hit    : 64.71%
Mean Calib Error  : 38.56 pts

Warnings:
⚠️ Calibration sample کمتر از 30 است: 17

Blockers:
⛔ برای استفاده عملی، حداقل 100 ارزیابی لازم است: 17/100
--------------------------------------------------------------------------------------------------------------
Confidence Label Buckets
Low            | n=  2 | Pred  25.0% | Dir 100.00% | T1 100.00% | Gap +75.00 | LOW_SAMPLE
Medium         | n=  8 | Pred  55.0% | Dir 100.00% | T1  62.50% | Gap +45.00 | LOW_SAMPLE
Medium-High    | n=  7 | Pred  67.5% | Dir 100.00% | T1  57.14% | Gap +32.50 | LOW_SAMPLE
--------------------------------------------------------------------------------------------------------------
Score Buckets
score_50_59    | n=  4 | Pred  54.5% | Dir 100.00% | T1  75.00% | Gap +45.50 | LOW_SAMPLE
score_60_69    | n=  6 | Pred  64.5% | Dir 100.00% | T1  66.67% | Gap +35.50 | LOW_SAMPLE
score_70_79    | n=  7 | Pred  74.5% | Dir 100.00% | T1  57.14% | Gap +25.50 | LOW_SAMPLE
==============================================================================================================

==============================================================================================================
🎲 Freakto Monte Carlo Risk Lab v5.0
==============================================================================================================
Created UTC      : 2026-07-08T16:40:58.719317+00:00
Risk Quality     : LOW_SAMPLE_RISK_MODEL
Source           : decision_evaluations_fallback (pct)
Samples          : 17
Iterations       : 20
Trades / Run     : 10
Expected / Trade : 1.0470pct
Best / Worst Samp: 1.8346pct / 0.4897pct
--------------------------------------------------------------------------------------------------------------
Median Final     : 10.0212pct
Mean Final       : 10.0424pct
P05 / P95 Final  : 8.2033pct / 12.6776pct
Median Max DD    : 0.0000pct
P95 Max DD       : 0.0000pct
Prob Loss        : 0.00%
Prob Ruin        : 0.00% | Threshold -10.00pct

Warnings:
⚠️ نمونه Monte Carlo کمتر از 30 است: 17
⚠️ Paper Trade کافی نبود؛ شبیه‌سازی با decision returns درصدی انجام شد، نه R واقعی.
==============================================================================================================

==============================================================================================================
🧭 Freakto Forward Test Status v5.3.3
==============================================================================================================
Status          : FORWARD_TEST_COLLECTING
Progress Score  : 4/100
Readiness Level : RESEARCH_ONLY
Paper Ready     : False
Live Ready      : False

Data Progress:
- Complete evaluations : 17/100
- Closed paper trades  : 0/30
- Open paper trades    : 0
- Total paper trades   : 0
- Regime-labeled       : 0/30
- Unknown regime       : 17
- Symbols evaluated    : 1
- Symbols scanned      : 0
- Forward runs         : 1/3 successful
- Forward days         : 1/30
- First run UTC        : 2026-07-05T17:39:28.376869+00:00
- Last run UTC         : 2026-07-05T17:58:26.845133+00:00

Blockers:
⛔ Complete evaluations کمتر از 100 است: 17
⛔ Closed paper trades کمتر از 30 است: 0
⛔ Regime-labeled samples کمتر از 30 است: 0
⛔ روزهای Forward Test کمتر از 30 است: 1

Next Actions:
→ اجرای منظم decision_evaluator.py بعد از ثبت تصمیم‌های جدید.
→ اجرای portfolio_scanner.py --paper تا فقط فرصت‌های مجاز Paper ثبت شوند.
→ چند اجرای جدید monitor.py --once پس از v4.7 لازم است تا regime_label وارد لاگ‌ها شود.
→ این چرخه را روزانه یا هر کندل 4h اجرا کن تا حداقل 30 روز داده Forward جمع شود.

Safe cycle command:
python forward_test_dashboard.py --cycle --validate

Windows scheduled-task/batch friendly command:
python forward_test_dashboard.py --cycle --validate --continue-on-error
==============================================================================================================

==============================================================================================================
🧪 Freakto Historical Backfill & Backtest v5.3
==============================================================================================================
Status                 : BACKTEST_BUILDING
Run ID                 : ALL_BACKTESTS
Symbols                : 6
Rows                   : 654
Complete Rows          : 654
Actionable Rows        : 46
Monitor/Other Rows     : 608
Avg Score              : 46.52
Directional Samples    : 295
Directional Win Rate   : 46.10%
Target 1 Hit Rate      : 48.14%
Stop Hit Rate          : 47.12%
Avg 24h Return         : -0.2509%
Best / Worst 24h       : 9.0062% / -10.3172%

By Symbol:
- BTC/USDT: rows=119 | complete=119 | dir=55 | win=49.09% | avg24h=-0.2711%
- BNB/USDT: rows=107 | complete=107 | dir=50 | win=46.0% | avg24h=-0.161%
- DOGE/USDT: rows=107 | complete=107 | dir=48 | win=39.58% | avg24h=-0.1383%
- ETH/USDT: rows=107 | complete=107 | dir=48 | win=45.83% | avg24h=-0.3824%
- SOL/USDT: rows=107 | complete=107 | dir=53 | win=45.28% | avg24h=-0.3751%
- XRP/USDT: rows=107 | complete=107 | dir=41 | win=51.22% | avg24h=-0.151%

By Actionability:
- MONITOR_ONLY: rows=359 | complete=359 | win=0.0% | avg24h=0.0%
- WATCHLIST: rows=176 | complete=176 | win=46.59% | avg24h=-0.2406%
- NOT_ACTIONABLE: rows=73 | complete=73 | win=43.84% | avg24h=-0.3441%
- ACTIONABLE: rows=46 | complete=46 | win=47.83% | avg24h=-0.1425%

Research Blockers:
⛔ میانگین بازده 24h در Backtest مثبت نیست.

Warnings:
⚠️ BACKTEST با FORWARD_TEST یکی نیست؛ خروجی تاریخی فقط برای تحقیق و اعتبارسنجی اولیه است.
⚠️ برای جلوگیری از اعتماد کاذب، Live/Paper جدی فقط بعد از Forward/Paper کافی مجاز است.
==============================================================================================================

==============================================================================================================
🧪 Freakto Backtest Diagnostics & Edge Breakdown v5.3.1
==============================================================================================================
Status                 : DIAGNOSTICS_READY
Run ID                 : backtest_diag_20260708_164058
Rows / Complete        : 654 / 654
Directional Samples    : 295
Directional Win Rate   : 46.10%
Target 1 Hit Rate      : 48.14%
Stop Hit Rate          : 47.12%
Avg 24h Return         : -0.2509%
MFE / MAE Mean         : 1.9292% / -2.2058%
Best Holding Period    : 4h (-0.1851%)

By Holding Period:
- 4h: samples=295 | win=36.95% | avg24h=-0.1851% | T1=48.14% | Stop=47.12% | MFE/MAE=0.875
- 24h: samples=295 | win=46.1% | avg24h=-0.2509% | T1=48.14% | Stop=47.12% | MFE/MAE=0.875
- 12h: samples=295 | win=36.95% | avg24h=-0.3947% | T1=48.14% | Stop=47.12% | MFE/MAE=0.875

By Side:
- LONG: samples=150 | win=52.0% | avg24h=-0.2283% | T1=47.33% | Stop=49.33% | MFE/MAE=0.834
- SHORT: samples=145 | win=40.0% | avg24h=-0.2744% | T1=48.97% | Stop=44.83% | MFE/MAE=0.912

By Symbol:
- DOGE/USDT: samples=48 | win=39.58% | avg24h=-0.1383% | T1=50.0% | Stop=41.67% | MFE/MAE=1.053
- XRP/USDT: samples=41 | win=51.22% | avg24h=-0.151% | T1=51.22% | Stop=51.22% | MFE/MAE=0.836
- BNB/USDT: samples=50 | win=46.0% | avg24h=-0.161% | T1=50.0% | Stop=48.0% | MFE/MAE=0.938
- BTC/USDT: samples=55 | win=49.09% | avg24h=-0.2711% | T1=41.82% | Stop=45.45% | MFE/MAE=0.843
- SOL/USDT: samples=53 | win=45.28% | avg24h=-0.3751% | T1=47.17% | Stop=52.83% | MFE/MAE=0.804
- ETH/USDT: samples=48 | win=45.83% | avg24h=-0.3824% | T1=50.0% | Stop=43.75% | MFE/MAE=0.792

By Symbol + Side:
- DOGE/USDT | SHORT: samples=25 | win=40.0% | avg24h=0.2309% | T1=52.0% | Stop=32.0% | MFE/MAE=1.207
- XRP/USDT | SHORT: samples=24 | win=50.0% | avg24h=-0.032% | T1=62.5% | Stop=50.0% | MFE/MAE=0.983
- SOL/USDT | LONG: samples=24 | win=54.17% | avg24h=-0.0637% | T1=45.83% | Stop=54.17% | MFE/MAE=0.862
- BNB/USDT | LONG: samples=30 | win=53.33% | avg24h=-0.0784% | T1=56.67% | Stop=50.0% | MFE/MAE=0.972
- BTC/USDT | LONG: samples=36 | win=55.56% | avg24h=-0.1739% | T1=44.44% | Stop=41.67% | MFE/MAE=0.841
- BNB/USDT | SHORT: samples=20 | win=35.0% | avg24h=-0.285% | T1=40.0% | Stop=45.0% | MFE/MAE=0.89
- ETH/USDT | LONG: samples=20 | win=55.0% | avg24h=-0.3133% | T1=50.0% | Stop=50.0% | MFE/MAE=0.698
- XRP/USDT | LONG: samples=17 | win=52.94% | avg24h=-0.319% | T1=35.29% | Stop=52.94% | MFE/MAE=0.663
- ETH/USDT | SHORT: samples=28 | win=39.29% | avg24h=-0.4317% | T1=50.0% | Stop=39.29% | MFE/MAE=0.86
- BTC/USDT | SHORT: samples=19 | win=36.84% | avg24h=-0.4553% | T1=36.84% | Stop=52.63% | MFE/MAE=0.846

By Actionability:
- ACTIONABLE: samples=46 | win=47.83% | avg24h=-0.1425% | T1=45.65% | Stop=56.52% | MFE/MAE=0.786
- WATCHLIST: samples=176 | win=46.59% | avg24h=-0.2406% | T1=51.14% | Stop=48.3% | MFE/MAE=0.949
- NOT_ACTIONABLE: samples=73 | win=43.84% | avg24h=-0.3441% | T1=42.47% | Stop=38.36% | MFE/MAE=0.75

By Score Bucket:
- 90+: samples=1 | win=100.0% | avg24h=0.453% | T1=0.0% | Stop=100.0% | MFE/MAE=0.247
- 80-89: samples=19 | win=57.89% | avg24h=0.3758% | T1=63.16% | Stop=47.37% | MFE/MAE=1.046
- 60-69: samples=90 | win=47.78% | avg24h=-0.0554% | T1=47.78% | Stop=47.78% | MFE/MAE=0.944
- 50-59: samples=141 | win=43.97% | avg24h=-0.3696% | T1=47.52% | Stop=44.68% | MFE/MAE=0.882
- 70-79: samples=44 | win=43.18% | avg24h=-0.5572% | T1=45.45% | Stop=52.27% | MFE/MAE=0.684

By Target/Stop Path:
- TARGET_ONLY: samples=109 | win=84.4% | avg24h=1.8185% | T1=100.0% | Stop=0.0% | MFE/MAE=3.945
- TARGET_AND_STOP: samples=33 | win=63.64% | avg24h=0.2652% | T1=100.0% | Stop=100.0% | MFE/MAE=0.848
- NO_TARGET_NO_STOP: samples=47 | win=38.3% | avg24h=-0.3028% | T1=0.0% | Stop=0.0% | MFE/MAE=0.733
- STOP_ONLY: samples=106 | win=4.72% | avg24h=-2.5167% | T1=0.0% | Stop=100.0% | MFE/MAE=0.148

Research Blockers:
⛔ میانگین بازده 24h در کل Backtest مثبت نیست.

Diagnostic Recommendations:
→ قبل از Paper/Live، گیت‌های ورود باید سخت‌تر یا تفکیک‌شده‌تر شوند؛ ACTIONABLE فعلی هنوز Edge مثبت تاریخی نداده است.
→ بهترین سمت تاریخی فعلی: LONG با avg24h=-0.2283% و samples=150. Long/Short را جداگانه gate کن.
→ بهترین نماد تاریخی فعلی: DOGE/USDT با avg24h=-0.1383% و win=39.58%. نمادهای ضعیف را برای Paper محدود کن.
→ بهترین holding period فعلی: 4h با avg=-0.1851%. خروج 24h را قطعی فرض نکن.
→ بهترین score bucket فعلی: 60-69 با avg=-0.0554%. threshold باید بر اساس bucket واقعی تنظیم شود، نه حس عددی score.

Warnings:
⚠️ این گزارش فقط Backtest تاریخی است و جای Forward/Paper واقعی را نمی‌گیرد.
⚠️ گروه‌هایی با sample کم ممکن است تصادفی یا overfit باشند؛ برای تصمیم از sample کافی استفاده کن.
==============================================================================================================

==============================================================================================================
🧪 Freakto Backtest Gate Simulator v5.3.2
==============================================================================================================
Status                 : GATE_RESEARCH_CANDIDATES_FOUND
Run ID                 : gate_sim_20260708_164058
Horizon                : 24h
Min Samples            : 30
Rows / Complete        : 654 / 654
Directional Samples    : 295
Baseline Avg Return    : -0.2509%
Baseline Win Rate      : 46.10%
Baseline T1 / Stop     : 48.14% / 47.12%
Gates Tested           : 139
Positive Gates         : 4
Research Candidates    : 3
Small Positive Gates   : 11

Top Gates:
- VOLUME_SCORE_GE_10 [RESEARCH_CANDIDATE]: samples=34 | avg=0.7131% | win=64.71% | T1=76.47% | Stop=44.12% | MFE/MAE=1.314 | score=1.2887
- RISK_MEDIUM [RESEARCH_CANDIDATE]: samples=76 | avg=0.2106% | win=51.32% | T1=53.95% | Stop=42.11% | MFE/MAE=1.037 | score=0.3525
- HISTORICAL_EDGE_SCORE_GE_1 [RESEARCH_CANDIDATE]: samples=40 | avg=0.1026% | win=57.5% | T1=47.5% | Stop=35.0% | MFE/MAE=1.066 | score=0.3467
- STRUCTURE_SCORE_GE_10 [POSITIVE_BUT_NEEDS_REVIEW]: samples=86 | avg=0.266% | win=52.33% | T1=53.49% | Stop=44.19% | MFE/MAE=0.992 | score=0.3931 | warn=مثبت است اما همه معیارهای کیفیت کامل نیستند.
- SYMBOL_SIDE_SCORE_GE_60_BNBUSDT_LONG [SMALL_SAMPLE_POSITIVE]: samples=11 | avg=0.5033% | win=72.73% | T1=72.73% | Stop=54.55% | MFE/MAE=1.374 | score=0.8649 | warn=مثبت است ولی sample کمتر از حداقل 30 است.
- SCORE_BUCKET_80_89 [SMALL_SAMPLE_POSITIVE]: samples=19 | avg=0.3758% | win=57.89% | T1=63.16% | Stop=47.37% | MFE/MAE=1.046 | score=0.5799 | warn=مثبت است ولی sample کمتر از حداقل 30 است.
- SCORE_GE_80 [SMALL_SAMPLE_POSITIVE]: samples=20 | avg=0.3797% | win=60.0% | T1=60.0% | Stop=50.0% | MFE/MAE=1.001 | score=0.5601 | warn=مثبت است ولی sample کمتر از حداقل 30 است.
- QUALITY_CORE_SCORE80_WATCH_OR_ACTIONABLE [SMALL_SAMPLE_POSITIVE]: samples=20 | avg=0.3797% | win=60.0% | T1=60.0% | Stop=50.0% | MFE/MAE=1.001 | score=0.5601 | warn=مثبت است ولی sample کمتر از حداقل 30 است.

Research Candidates:
- VOLUME_SCORE_GE_10 [RESEARCH_CANDIDATE]: samples=34 | avg=0.7131% | win=64.71% | T1=76.47% | Stop=44.12% | MFE/MAE=1.314 | score=1.2887
- RISK_MEDIUM [RESEARCH_CANDIDATE]: samples=76 | avg=0.2106% | win=51.32% | T1=53.95% | Stop=42.11% | MFE/MAE=1.037 | score=0.3525
- HISTORICAL_EDGE_SCORE_GE_1 [RESEARCH_CANDIDATE]: samples=40 | avg=0.1026% | win=57.5% | T1=47.5% | Stop=35.0% | MFE/MAE=1.066 | score=0.3467

Small-Sample Positive Gates:
- SYMBOL_SIDE_SCORE_GE_60_BNBUSDT_LONG [SMALL_SAMPLE_POSITIVE]: samples=11 | avg=0.5033% | win=72.73% | T1=72.73% | Stop=54.55% | MFE/MAE=1.374 | score=0.8649 | warn=مثبت است ولی sample کمتر از حداقل 30 است.
- SCORE_BUCKET_80_89 [SMALL_SAMPLE_POSITIVE]: samples=19 | avg=0.3758% | win=57.89% | T1=63.16% | Stop=47.37% | MFE/MAE=1.046 | score=0.5799 | warn=مثبت است ولی sample کمتر از حداقل 30 است.
- SCORE_GE_80 [SMALL_SAMPLE_POSITIVE]: samples=20 | avg=0.3797% | win=60.0% | T1=60.0% | Stop=50.0% | MFE/MAE=1.001 | score=0.5601 | warn=مثبت است ولی sample کمتر از حداقل 30 است.
- QUALITY_CORE_SCORE80_WATCH_OR_ACTIONABLE [SMALL_SAMPLE_POSITIVE]: samples=20 | avg=0.3797% | win=60.0% | T1=60.0% | Stop=50.0% | MFE/MAE=1.001 | score=0.5601 | warn=مثبت است ولی sample کمتر از حداقل 30 است.
- SYMBOL_SIDE_DOGEUSDT_SHORT [SMALL_SAMPLE_POSITIVE]: samples=25 | avg=0.2309% | win=40.0% | T1=52.0% | Stop=32.0% | MFE/MAE=1.207 | score=0.2815 | warn=مثبت است ولی sample کمتر از حداقل 30 است.
- ACTIONABLE_SCORE_GE_80 [SMALL_SAMPLE_POSITIVE]: samples=18 | avg=0.2069% | win=55.56% | T1=55.56% | Stop=55.56% | MFE/MAE=0.891 | score=0.2328 | warn=مثبت است ولی sample کمتر از حداقل 30 است.
- SCORE_GE_80_LONG [SMALL_SAMPLE_POSITIVE]: samples=16 | avg=0.1384% | win=56.25% | T1=56.25% | Stop=56.25% | MFE/MAE=0.89 | score=0.1838 | warn=مثبت است ولی sample کمتر از حداقل 30 است.
- SYMBOL_SIDE_SCORE_GE_60_XRPUSDT_SHORT [SMALL_SAMPLE_POSITIVE]: samples=15 | avg=0.013% | win=46.67% | T1=66.67% | Stop=46.67% | MFE/MAE=1.088 | score=0.168 | warn=مثبت است ولی sample کمتر از حداقل 30 است.

Research Blockers:
⛔ Baseline Backtest هنوز میانگین مثبت ندارد.

Gate Recommendations:
→ بهترین gate تحقیقاتی با sample کافی: VOLUME_SCORE_GE_10 | avg=0.7131% | samples=34 | verdict=RESEARCH_CANDIDATE.
→ این gate هنوز فقط research candidate است؛ قبل از Paper واقعی باید در Forward/Paper آینده هم تأیید شود.
→ ACTIONABLE فعلی هنوز مثبت نیست: avg=-0.1425%، stop=56.52%. گیت actionability باید سخت‌تر شود.
→ score>=80 را جدا نگه دار: samples=20, avg=0.3797%. اگر sample کم است، فقط research watchlist باشد.

Warnings:
⚠️ Gate Simulator فقط فیلترهای live-known را تست می‌کند؛ target/stop/return/MFE/MAE برای فیلتر استفاده نشده‌اند.
⚠️ BACKTEST جای FORWARD_TEST و Paper واقعی را نمی‌گیرد؛ candidateها فقط برای تحقیق هستند.
⚠️ subsetهای کم‌نمونه می‌توانند overfit باشند؛ sample حداقل و تأیید forward لازم است.
==============================================================================================================

==============================================================================================================
🧪 Freakto Candidate Gate Shadow Validator v5.3.3
==============================================================================================================
Status                 : SHADOW_COLLECTING_FORWARD_DATA
Run ID                 : shadow_gate_20260708_164059
Horizon                : 24h
Min Samples            : 30
Decisions              : 32
Directional Decisions  : 23
Gates Tracked          : 7
Shadow Signals         : 14
Evaluated Shadow       : 14
Pending Shadow         : 0
Confirmed Candidates   : 0
Building Candidates    : 7
Rejected Candidates    : 0

Gate Shadow Metrics:
- STRUCTURE_SCORE_GE_10 [SHADOW_BUILDING]: signals=14 | eval=14 | pending=0 | avg=0.8834% | win=100.0% | T1=57.14% | Stop=0.0% | MFE/MAE=4.18 | warn=Forward evaluated samples کمتر از حداقل 30 است: 14
- VOLUME_SCORE_GE_10 [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- RISK_MEDIUM [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- HISTORICAL_EDGE_SCORE_GE_1 [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- SCORE_GE_80 [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- DOGE_SHORT_WATCH [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- BNB_LONG_SCORE_GE_60 [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.

Shadow Blockers:
⛔ کل نمونه‌های ارزیابی‌شده Shadow کمتر از 30 است: 14

Shadow Recommendations:
→ Shadow هنوز در حال ساخت داده است؛ فعال‌ترین gate: STRUCTURE_SCORE_GE_10 | signals=14, evaluated=14.
→ برای هر gate حداقل 30 نمونه Forward کامل لازم است.
→ سه gate اصلی که باید زیر نظر بمانند: VOLUME_SCORE_GE_10، RISK_MEDIUM، HISTORICAL_EDGE_SCORE_GE_1.

Warnings:
⚠️ Shadow Gate هیچ Paper Trade و هیچ سفارش واقعی ایجاد نمی‌کند؛ فقط برچسب تحقیقاتی می‌زند.
⚠️ Gateها از خروجی Backtest آمده‌اند و باید در Forward مستقل تأیید شوند.
⚠️ تا وقتی هر gate حداقل 30 نمونه Forward کامل ندارد، نتیجه آماری قابل اتکا نیست.
==============================================================================================================

==============================================================================================================
🧬 Freakto Regime-Split Gate Matrix v6.1.0
==============================================================================================================
Status: REGIME_GATE_CANDIDATES_FOUND
Run ID: regime_gate_matrix_20260708_164059
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

==============================================================================================================
🧠 Freakto Research Robustness & Intelligence Suite v6.1.0
==============================================================================================================
Status: RESEARCH_SUITE_WITH_BLOCKERS
Run ID: research_suite_20260708_164101

Sections:
- gate_robustness: ROBUST_GATES_FOUND
- cost_adjusted_backtest: COST_ADJUSTED_READY
- meta_labeling: META_LABEL_BUILDING
- ensemble_explainability: EXPLAINABILITY_READY
- data_enrichment: ENRICHMENT_CONNECTORS_PRESENT
- regime_research: REGIME_RESEARCH_READY
- regime_gate_matrix: REGIME_GATE_CANDIDATES_FOUND
- cross_exchange_validation: SINGLE_PROVIDER_ONLY
- research_db: RESEARCH_DB_READY
- pipeline_health: PIPELINE_ATTENTION_REQUIRED
- strict_readiness: STRICT_READINESS_RESEARCH_ONLY
- position_sizing_lab: POSITION_SIZING_RESEARCH_READY
- airdrop_shadow_research: AIRDROP_SHADOW_READY
- static_dashboard: STATIC_DASHBOARD_READY

Gate Robustness Highlights:
- VOLUME_SCORE_GE_10: ROBUST_RESEARCH_CANDIDATE | n=34 | net=0.5631% | stability=60.0%
- QUALITY_STRUCTURE_RISK_MEDIUM: ROBUST_RESEARCH_CANDIDATE | n=41 | net=0.3069% | stability=60.0%
- QUALITY_VOLUME_HEDGE: LOW_SAMPLE | n=2 | net=1.5292% | stability=100.0%
- BNB_LONG_SCORE_GE_60: LOW_SAMPLE | n=11 | net=0.3533% | stability=75.0%
- SCORE_GE_80: LOW_SAMPLE | n=20 | net=0.2297% | stability=60.0%

Regime-Gate Matrix Highlights:
- REGIME_GATE_CANDIDATES_FOUND | candidates=4 | horizon=24h
- TRENDING_BEAR × STRUCTURE_SCORE_GE_10: n=47 | net=0.6404% | verdict=REGIME_RESEARCH_CANDIDATE
- TRENDING_BEAR × RISK_MEDIUM: n=37 | net=0.5946% | verdict=REGIME_RESEARCH_CANDIDATE
- TRENDING_BEAR × STRUCTURE_SCORE_GE_10 × SHORT: n=47 | net=0.6404% | verdict=REGIME_RESEARCH_CANDIDATE
- TRENDING_BEAR × RISK_MEDIUM × SHORT: n=37 | net=0.5946% | verdict=REGIME_RESEARCH_CANDIDATE

Strict Readiness:
- STRICT_READINESS_RESEARCH_ONLY | blockers=2
  ⛔ Backtest net expectancy از نظر CI95 بالای صفر نیست.
  ⛔ Forward complete samples کمتر از 30 است.

Pipeline Health:
- PIPELINE_ATTENTION_REQUIRED | alerts=1

Suite Blockers:
⛔ meta_labeling: AUC یا sample هنوز برای استفاده عملی کافی نیست.
⛔ regime_gate_matrix: Baseline net return کلی هنوز مثبت نیست.
⛔ strict_readiness: Backtest net expectancy از نظر CI95 بالای صفر نیست.
⛔ strict_readiness: Forward complete samples کمتر از 30 است.

Safety: هیچ بخش v6/v6.1 سفارش واقعی ارسال نمی‌کند و Paper Trade جدید ایجاد نمی‌کند.
==============================================================================================================

==============================================================================================================
🚦 Freakto Advanced Live Readiness Score v4.7.1
==============================================================================================================
Created UTC       : 2026-07-08T16:41:01.377268+00:00
Readiness Level   : RESEARCH_ONLY
Readiness Score   : 49/100
Paper Ready       : False
Live Ready        : False
Allowed Risk      : 0.00%
Edge Quality      : EARLY_EDGE_OBSERVED
Regime Verdict    : REGIME_DATA_MISSING

Core Stats:
- Complete evaluations: 17
- Closed paper trades: 0
- Paper expectancy: 0.0000R
- Decision Profit Factor: 17.7989
--------------------------------------------------------------------------------------------------------------
Component : Data Sufficiency
Score     : 2/20
Status    : LOW
Note      : Complete evaluations: 17/100
Note      : Closed paper trades: 0/30
Blocker   : Complete evaluations هنوز کافی نیست: 17/100
Blocker   : Closed paper trades هنوز کافی نیست: 0/30
--------------------------------------------------------------------------------------------------------------
Component : Decision Edge
Score     : 23/23
Status    : PARTIAL
Note      : Decision quality: EARLY_POSITIVE_LOW_SAMPLE
Note      : Directional Win 100.00% | Expectancy 1.0470pct | PF 17.7989
Note      : Stop 0.00% | Sharpe-like 8.6425
Blocker   : Decision sample کمتر از 100 است: 17
--------------------------------------------------------------------------------------------------------------
Component : Paper Edge
Score     : 0/20
Status    : LOW
Note      : Paper quality: NO_DATA
Note      : Closed 0 | Paper Win 0.00% | Expectancy 0.0000R | PF 0.0000
Note      : Max drawdown 0.0000R
Blocker   : Paper sample کمتر از 30 معامله بسته‌شده است: 0
Blocker   : Paper expectancy هنوز مثبت نیست.
--------------------------------------------------------------------------------------------------------------
Component : Regime Stability
Score     : 5/18
Status    : LOW
Note      : Regime verdict: REGIME_DATA_MISSING
Note      : Known/Unknown: 0/17
Note      : Best/Worst: UNKNOWN/UNKNOWN
Blocker   : Regime-labeled samples کمتر از 30 است: 0
--------------------------------------------------------------------------------------------------------------
Component : Validation Stability
Score     : 12/12
Status    : PASS
Note      : Strategy Lab اجرا شده و نمونه دارد.
Note      : Walk-Forward Validation اجرا شده و test sample دارد.
--------------------------------------------------------------------------------------------------------------
Component : Operational Safety
Score     : 7/7
Status    : PASS
Note      : Auto-live trading در پروژه فعال نیست.
Note      : Readiness Gate قبل از هر تست عملی باید بررسی شود.
Note      : Stop Hit Rate کنترل‌شده است: 0.00%

Warnings:
⚠️ Decision edge هنوز بسیار کم‌نمونه است.
⚠️ Paper Trading هنوز نتیجه بسته‌شده ندارد.
⚠️ Regime Matrix برای لاگ‌های قدیمی هنوز UNKNOWN زیادی دارد؛ چند روز داده جدید لازم است.

Hard Blockers:
⛔ Complete evaluations هنوز کافی نیست: 17/100
⛔ Closed paper trades هنوز کافی نیست: 0/30
⛔ Decision sample کمتر از 100 است: 17
⛔ Paper sample کمتر از 30 معامله بسته‌شده است: 0
⛔ Paper expectancy هنوز مثبت نیست.
⛔ Regime-labeled samples کمتر از 30 است: 0

Conclusion: پروژه هنوز در Research/Observation است؛ داده و Paper Trade بیشتری لازم است.
==============================================================================================================