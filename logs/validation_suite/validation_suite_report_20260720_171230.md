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
Created UTC      : 2026-07-20T17:12:29.995356+00:00
Combined Quality : EARLY_EDGE_OBSERVED

--------------------------------------------------------------------------------------------------------------
Source       : decision_evaluations
Quality      : VALIDATING_POSITIVE
Samples      : 89 | Positive/Negative/Flat: 55/34/0
Directional Win Rate: 61.80%
Expectancy   : 0.4140pct
ProfitFactor : 1.9236
Sharpe-like  : 2.4392 | Sortino-like: 3.9309
Max Drawdown : -15.3391pct
Best/Worst   : 3.8877pct / -3.2625pct
Avg Win/Loss : 1.3953pct / -1.1734pct
Stop Rate    : 34.83%
Target Hit   : T1 39.33% | T2 38.20% | T3 28.09%
Definition   : Directional Win = positive evaluated return; Target Hit = target_1_hit.
MFE/MAE Avg  : 3.5661% / -2.3667%
Note         : Expectancy و Directional Win Rate فعلاً مثبت هستند.
Warning      : نمونه هنوز کمتر از 100 است؛ برای تصمیم عملی باید داده بیشتری جمع شود.
Warning      : افت تجمعی قابل توجه دیده شده است؛ کنترل ریسک باید بررسی شود.
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
⛔ Decision COMPLETE کمتر از 100 است: 89
⛔ Paper trades بسته‌شده کمتر از 30 است: 0
==============================================================================================================

==============================================================================================================
🧬 Freakto Regime Performance Matrix v4.7.1
==============================================================================================================
Created UTC          : 2026-07-20T17:12:30.030541+00:00
Overall Verdict      : REGIME_DATA_COLLECTING
Known/Unknown Regime : 61 / 28
Best/Worst Regime    : TRENDING_BEAR / UNKNOWN
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : TRENDING_BULL / LONG / WATCHLIST
Samples            : 27
Target 1 Hit       : 100.00%
Directional Win    : 66.67%
Avg 24h            : 0.1926%
Profit Factor      : 1.5241
Stop Rate          : 88.89%
Avg Score          : 66.11
Verdict            : MIXED_POSITIVE
Note               : بازده مثبت است اما کیفیت آماری کامل نیست.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : UNKNOWN / NEUTRAL / 0
Samples            : 22
Target 1 Hit       : 0.00%
Directional Win    : 54.55%
Avg 24h            : 0.3489%
Profit Factor      : 1.6213
Stop Rate          : 0.00%
Avg Score          : 33.91
Verdict            : MIXED_POSITIVE
Note               : Regime در لاگ‌های قدیمی ثبت نشده؛ برای تصمیم‌گیری نیاز به داده v4.7 به بعد است.
Note               : بازده مثبت است اما کیفیت آماری کامل نیست.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : TRENDING_BULL / NEUTRAL / MONITOR_ONLY
Samples            : 17
Target 1 Hit       : 0.00%
Directional Win    : 58.82%
Avg 24h            : 0.7824%
Profit Factor      : 2.8150
Stop Rate          : 0.00%
Avg Score          : 29.65
Verdict            : MIXED_POSITIVE
Note               : بازده مثبت است اما کیفیت آماری کامل نیست.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : TRENDING_BEAR / NEUTRAL / MONITOR_ONLY
Samples            : 7
Target 1 Hit       : 0.00%
Directional Win    : 100.00%
Avg 24h            : 1.9942%
Profit Factor      : 13.9593
Stop Rate          : 0.00%
Avg Score          : 31.00
Verdict            : MIXED_POSITIVE
Note               : بازده مثبت است اما کیفیت آماری کامل نیست.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : TRENDING_BULL / LONG / NOT_ACTIONABLE
Samples            : 7
Target 1 Hit       : 100.00%
Directional Win    : 57.14%
Avg 24h            : 0.1993%
Profit Factor      : 1.4366
Stop Rate          : 71.43%
Avg Score          : 49.57
Verdict            : MIXED_POSITIVE
Note               : بازده مثبت است اما کیفیت آماری کامل نیست.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : UNKNOWN / LONG / 0
Samples            : 5
Target 1 Hit       : 0.00%
Directional Win    : 40.00%
Avg 24h            : -0.4885%
Profit Factor      : 0.3351
Stop Rate          : 0.00%
Avg Score          : 60.00
Verdict            : OBSERVE
Note               : Regime در لاگ‌های قدیمی ثبت نشده؛ برای تصمیم‌گیری نیاز به داده v4.7 به بعد است.
Note               : نیاز به داده بیشتر دارد.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : UNKNOWN / SHORT / 0
Samples            : 1
Target 1 Hit       : 0.00%
Directional Win    : 100.00%
Avg 24h            : 0.6924%
Profit Factor      : 0.6924
Stop Rate          : 0.00%
Avg Score          : 57.00
Verdict            : LOW_SAMPLE
Note               : نمونه کمتر از 5 است؛ فقط برای رصد.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : TRENDING_BULL / LONG / ACTIONABLE
Samples            : 1
Target 1 Hit       : 100.00%
Directional Win    : 100.00%
Avg 24h            : 0.4897%
Profit Factor      : 0.4897
Stop Rate          : 100.00%
Avg Score          : 70.00
Verdict            : LOW_SAMPLE
Note               : نمونه کمتر از 5 است؛ فقط برای رصد.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : SIDEWAYS / NEUTRAL / MONITOR_ONLY
Samples            : 1
Target 1 Hit       : 0.00%
Directional Win    : 0.00%
Avg 24h            : -0.5747%
Profit Factor      : 0.0000
Stop Rate          : 0.00%
Avg Score          : 35.00
Verdict            : LOW_SAMPLE
Note               : نمونه کمتر از 5 است؛ فقط برای رصد.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : TRENDING_BEAR / SHORT / NOT_ACTIONABLE
Samples            : 1
Target 1 Hit       : 0.00%
Directional Win    : 0.00%
Avg 24h            : -2.8484%
Profit Factor      : 0.0000
Stop Rate          : 100.00%
Avg Score          : 46.00
Verdict            : LOW_SAMPLE
Note               : نمونه کمتر از 5 است؛ فقط برای رصد.
==============================================================================================================

==============================================================================================================
🧠 Freakto Portfolio Memory Engine v5.0
==============================================================================================================
Created UTC       : 2026-07-20T17:12:30.073406+00:00
Portfolio Status  : MEMORY_BUILDING
Symbols           : 6
Total scans       : 456
Complete evals    : 89
Closed paper      : 0
Best memory symbol: BTC/USDT
Best paper symbol : NONE

Warnings:
⚠️ Closed paper trades کل پورتفو کمتر از 30 است: 0
--------------------------------------------------------------------------------------------------------------
Symbol        : BNB/USDT
Status        : OBSERVATION_ACTIVE | Confidence LOW_MEDIUM
Scans/Dec/Eval: 76 / 0 / 0
Latest        : LONG | Rec IGNORE | MTF NEUTRAL
Avg Score/Conf/Opp: 38.59 / 33.54% / 12.25
Directional/T1/Avg24: 0.00% / 0.00% / 0.0000%
Paper        : closed 0 | win 0.00% | exp 0.0000R | PF 0.0000
Rec rates    : actionable 0.00% | monitor 5.26% | ignore 40.79%
Note         : نماد در حال رصد است اما هنوز Edge کافی ندارد.
Blocker      : Complete evaluations کمتر از 30 است: 0
Blocker      : Closed paper trades کمتر از 30 است: 0
--------------------------------------------------------------------------------------------------------------
Symbol        : BTC/USDT
Status        : SYMBOL_EDGE_EARLY | Confidence MEDIUM
Scans/Dec/Eval: 76 / 93 / 89
Latest        : NEUTRAL | Rec IGNORE | MTF NEUTRAL
Avg Score/Conf/Opp: 37.30 / 31.91% / 14.65
Directional/T1/Avg24: 61.80% / 39.33% / 0.4140%
Paper        : closed 0 | win 0.00% | exp 0.0000R | PF 0.0000
Rec rates    : actionable 0.00% | monitor 5.26% | ignore 40.79%
Note         : Decision edge اولیه برای این نماد مثبت است.
Blocker      : Closed paper trades کمتر از 30 است: 0
--------------------------------------------------------------------------------------------------------------
Symbol        : DOGE/USDT
Status        : OBSERVATION_ACTIVE | Confidence LOW_MEDIUM
Scans/Dec/Eval: 76 / 0 / 0
Latest        : LONG | Rec IGNORE | MTF NEUTRAL
Avg Score/Conf/Opp: 38.93 / 33.96% / 15.69
Directional/T1/Avg24: 0.00% / 0.00% / 0.0000%
Paper        : closed 0 | win 0.00% | exp 0.0000R | PF 0.0000
Rec rates    : actionable 0.00% | monitor 9.21% | ignore 36.84%
Note         : نماد در حال رصد است اما هنوز Edge کافی ندارد.
Blocker      : Complete evaluations کمتر از 30 است: 0
Blocker      : Closed paper trades کمتر از 30 است: 0
--------------------------------------------------------------------------------------------------------------
Symbol        : ETH/USDT
Status        : OBSERVATION_ACTIVE | Confidence LOW_MEDIUM
Scans/Dec/Eval: 76 / 0 / 0
Latest        : LONG | Rec MONITOR | MTF LONG
Avg Score/Conf/Opp: 37.47 / 31.66% / 15.93
Directional/T1/Avg24: 0.00% / 0.00% / 0.0000%
Paper        : closed 0 | win 0.00% | exp 0.0000R | PF 0.0000
Rec rates    : actionable 0.00% | monitor 6.58% | ignore 39.47%
Note         : نماد در حال رصد است اما هنوز Edge کافی ندارد.
Blocker      : Complete evaluations کمتر از 30 است: 0
Blocker      : Closed paper trades کمتر از 30 است: 0
--------------------------------------------------------------------------------------------------------------
Symbol        : SOL/USDT
Status        : OBSERVATION_ACTIVE | Confidence LOW_MEDIUM
Scans/Dec/Eval: 76 / 0 / 0
Latest        : LONG | Rec MONITOR | MTF NEUTRAL
Avg Score/Conf/Opp: 35.53 / 30.32% / 19.71
Directional/T1/Avg24: 0.00% / 0.00% / 0.0000%
Paper        : closed 0 | win 0.00% | exp 0.0000R | PF 0.0000
Rec rates    : actionable 0.00% | monitor 9.21% | ignore 36.84%
Note         : نماد در حال رصد است اما هنوز Edge کافی ندارد.
Blocker      : Complete evaluations کمتر از 30 است: 0
Blocker      : Closed paper trades کمتر از 30 است: 0
--------------------------------------------------------------------------------------------------------------
Symbol        : XRP/USDT
Status        : OBSERVATION_ACTIVE | Confidence LOW_MEDIUM
Scans/Dec/Eval: 76 / 0 / 0
Latest        : LONG | Rec IGNORE | MTF NEUTRAL
Avg Score/Conf/Opp: 34.08 / 28.09% / 15.27
Directional/T1/Avg24: 0.00% / 0.00% / 0.0000%
Paper        : closed 0 | win 0.00% | exp 0.0000R | PF 0.0000
Rec rates    : actionable 0.00% | monitor 6.58% | ignore 39.47%
Note         : نماد در حال رصد است اما هنوز Edge کافی ندارد.
Blocker      : Complete evaluations کمتر از 30 است: 0
Blocker      : Closed paper trades کمتر از 30 است: 0
==============================================================================================================

==============================================================================================================
🎯 Freakto Confidence Calibration Engine v5.0
==============================================================================================================
Created UTC       : 2026-07-20T17:12:30.089120+00:00
Quality           : CALIBRATION_MIXED
Samples           : 89
Overall Dir Win   : 61.80%
Overall T1 Hit    : 39.33%
Mean Calib Error  : 19.56 pts

Warnings:
⚠️ Calibration متوسط است؛ برخی confidence bucketها نیاز به داده بیشتر دارند.

Blockers:
⛔ برای استفاده عملی، حداقل 100 ارزیابی لازم است: 89/100
--------------------------------------------------------------------------------------------------------------
Confidence Label Buckets
Low            | n= 33 | Pred  25.0% | Dir  63.64% | T1  21.21% | Gap +38.64 | UNDER_CONFIDENT
nan            | n= 28 | Pred  50.0% | Dir  53.57% | T1   0.00% | Gap  +3.57 | WELL_CALIBRATED_DIRECTIONAL
Medium         | n= 17 | Pred  55.0% | Dir  64.71% | T1 100.00% | Gap  +9.71 | WELL_CALIBRATED_DIRECTIONAL
Medium-High    | n= 11 | Pred  67.5% | Dir  72.73% | T1 100.00% | Gap  +5.23 | WELL_CALIBRATED_DIRECTIONAL
--------------------------------------------------------------------------------------------------------------
Score Buckets
score_10_19    | n=  5 | Pred  14.5% | Dir  60.00% | T1   0.00% | Gap +45.50 | LOW_SAMPLE
score_20_29    | n= 11 | Pred  24.5% | Dir  63.64% | T1   0.00% | Gap +39.14 | UNDER_CONFIDENT
score_30_39    | n= 24 | Pred  34.5% | Dir  62.50% | T1   0.00% | Gap +28.00 | UNDER_CONFIDENT
score_40_49    | n= 13 | Pred  44.5% | Dir  46.15% | T1  38.46% | Gap  +1.65 | WELL_CALIBRATED_DIRECTIONAL
score_50_59    | n= 11 | Pred  54.5% | Dir  81.82% | T1  63.64% | Gap +27.32 | UNDER_CONFIDENT
score_60_69    | n= 13 | Pred  64.5% | Dir  53.85% | T1  92.31% | Gap -10.65 | OVER_CONFIDENT
score_70_79    | n= 12 | Pred  74.5% | Dir  66.67% | T1  91.67% | Gap  -7.83 | WELL_CALIBRATED_DIRECTIONAL
==============================================================================================================

==============================================================================================================
🎲 Freakto Monte Carlo Risk Lab v5.0
==============================================================================================================
Created UTC      : 2026-07-20T17:12:30.131381+00:00
Risk Quality     : HIGH_RISK
Source           : decision_evaluations_fallback (pct)
Samples          : 89
Iterations       : 2000
Trades / Run     : 100
Expected / Trade : 0.4140pct
Best / Worst Samp: 3.8877pct / -3.2625pct
--------------------------------------------------------------------------------------------------------------
Median Final     : 40.7822pct
Mean Final       : 40.8968pct
P05 / P95 Final  : 15.6995pct / 67.1736pct
Median Max DD    : -7.8973pct
P95 Max DD       : -14.8667pct
Prob Loss        : 0.50%
Prob Ruin        : 26.45% | Threshold -10.00pct

Warnings:
⚠️ Paper Trade کافی نبود؛ شبیه‌سازی با decision returns درصدی انجام شد، نه R واقعی.

Blockers:
⛔ Probability of ruin بالاست: 26.45%
==============================================================================================================

==============================================================================================================
🧭 Freakto Forward Test Status v9.0.0
==============================================================================================================
Status          : FORWARD_TEST_COLLECTING
Progress Score  : 65/100
Readiness Level : RESEARCH_ONLY
Paper Ready     : False
Live Ready      : False

Data Progress:
- Complete evaluations : 89/100
- Closed paper trades  : 0/30
- Open paper trades    : 0
- Total paper trades   : 0
- Regime-labeled       : 61/30
- Unknown regime       : 28
- Symbols evaluated    : 1
- Symbols scanned      : 6
- Forward runs         : 61/63 successful
- Forward days         : 16/30
- First run UTC        : 2026-07-05T17:39:28.376869+00:00
- Last run UTC         : 2026-07-20T11:23:54.581530+00:00

Notes:
✓ Regime-labeled samples برای تحلیل اولیه کافی است.

Blockers:
⛔ Complete evaluations کمتر از 100 است: 89
⛔ Closed paper trades کمتر از 30 است: 0
⛔ روزهای Forward Test کمتر از 30 است: 16

Next Actions:
→ اجرای منظم decision_evaluator.py بعد از ثبت تصمیم‌های جدید.
→ اجرای portfolio_scanner.py --paper تا فقط فرصت‌های مجاز Paper ثبت شوند.
→ این چرخه را روزانه یا هر کندل 4h اجرا کن تا حداقل 30 روز داده Forward جمع شود.

Safe cycle command:
python forward_test_dashboard.py --cycle --validate

Windows scheduled-task/batch friendly command:
python forward_test_dashboard.py --cycle --validate --continue-on-error
==============================================================================================================

==============================================================================================================
🧪 Freakto Historical Backfill & Backtest v5.3
==============================================================================================================
Status                 : NO_BACKTEST_DATA
Run ID                 : ALL_BACKTESTS
Symbols                : 0
Rows                   : 0
Complete Rows          : 0
Actionable Rows        : 0
Monitor/Other Rows     : 0
Avg Score              : 0.0
Directional Samples    : 0
Directional Win Rate   : 0.00%
Target 1 Hit Rate      : 0.00%
Stop Hit Rate          : 0.00%
Avg 24h Return         : 0.0000%
Best / Worst 24h       : 0.0000% / 0.0000%

Research Blockers:
⛔ هیچ داده Backtest تاریخی وجود ندارد.
==============================================================================================================

==============================================================================================================
🧪 Freakto Backtest Diagnostics & Edge Breakdown v5.3.1
==============================================================================================================
Status                 : NO_BACKTEST_DATA
Run ID                 : backtest_diag_20260720_171230
Rows / Complete        : 0 / 0
Directional Samples    : 0
Directional Win Rate   : 0.00%
Target 1 Hit Rate      : 0.00%
Stop Hit Rate          : 0.00%
Avg 24h Return         : 0.0000%
MFE / MAE Mean         : 0.0000% / 0.0000%

Research Blockers:
⛔ هیچ داده historical_backtest_evaluations.csv وجود ندارد.

Diagnostic Recommendations:
→ یک Backtest سبک اجرا کن و دوباره diagnostics بگیر.

Warnings:
⚠️ ابتدا historical_backtest_dashboard.py را اجرا کن.
==============================================================================================================

==============================================================================================================
🧪 Freakto Backtest Gate Simulator v5.3.2
==============================================================================================================
Status                 : NO_BACKTEST_DATA
Run ID                 : gate_sim_20260720_171230
Horizon                : 24h
Min Samples            : 30
Rows / Complete        : 0 / 0
Directional Samples    : 0
Baseline Avg Return    : 0.0000%
Baseline Win Rate      : 0.00%
Baseline T1 / Stop     : 0.00% / 0.00%
Gates Tested           : 0
Positive Gates         : 0
Research Candidates    : 0
Small Positive Gates   : 0

Research Blockers:
⛔ هیچ فایل historical_backtest_evaluations.csv پیدا نشد.

Gate Recommendations:
→ اول historical_backtest_dashboard.py را اجرا کن، سپس gate simulator را اجرا کن.

Warnings:
⚠️ این ابزار فقط research است و هیچ معامله‌ای ثبت نمی‌کند.
==============================================================================================================

==============================================================================================================
🧬 Freakto Forward Regime Label Injection Patch v6.2.1
==============================================================================================================
Status                 : FORWARD_REGIME_LABELING_READY
Run ID                 : forward_regime_label_20260720_171230
Apply Changes          : False
Decision Rows          : 93
Known Before / After   : 61 / 61
Unknown Before / After : 32 / 32
Injected Decision Rows : 0
Preserved Direct Rows  : 61
Direct/Text/Proxy      : 28 / 33 / 0
Evaluation Rows        : 92
Patched Evaluations    : 0
Eval Known After       : 61

Decision Regime Counts:
- TRENDING_BULL: 52
- UNKNOWN: 32
- TRENDING_BEAR: 8
- SIDEWAYS: 1

Recommendations:
→ هنوز 32 تصمیم Forward بدون regime قابل‌اعتماد مانده؛ اجرای‌های جدید بعد از v6.2.1 باید این عدد را کاهش دهد.
→ بعد از اجرای cycle جدید، regime_shadow_gate_dashboard.py --compact را دوباره بررسی کن.

Warnings:
⚠️ Regime injection فقط از داده‌های لحظه تصمیم استفاده می‌کند؛ outcome/return/target/stop استفاده نمی‌شود.
⚠️ برچسب‌های LOW_CONF_PROXY برای Research هستند و باید در Forward واقعی بیشتر validate شوند.
==============================================================================================================

==============================================================================================================
🧪 Freakto Regime Shadow Gate Activator v6.2.0
==============================================================================================================
Status                 : SHADOW_COLLECTING_FORWARD_DATA
Run ID                 : shadow_gate_20260720_171230
Horizon                : 24h
Min Samples            : 30
Decisions              : 93
Directional Decisions  : 42
Gates Tracked          : 11
Shadow Signals         : 28
Evaluated Shadow       : 28
Pending Shadow         : 0
Confirmed Candidates   : 0
Building Candidates    : 11
Rejected Candidates    : 0

Gate Shadow Metrics:
- STRUCTURE_SCORE_GE_10 [SHADOW_BUILDING]: signals=19 | eval=19 | pending=0 | avg=0.5264% | win=84.21% | T1=73.68% | Stop=63.16% | MFE/MAE=1.93 | warn=Forward evaluated samples کمتر از حداقل 30 است: 19
- HISTORICAL_EDGE_SCORE_GE_1 [SHADOW_BUILDING]: signals=8 | eval=8 | pending=0 | avg=-1.2246% | win=12.5% | T1=100.0% | Stop=100.0% | MFE/MAE=0.688 | warn=Forward evaluated samples کمتر از حداقل 30 است: 8
- RISK_MEDIUM [SHADOW_BUILDING]: signals=1 | eval=1 | pending=0 | avg=0.5361% | win=100.0% | T1=100.0% | Stop=100.0% | MFE/MAE=0.828 | warn=Forward evaluated samples کمتر از حداقل 30 است: 1
- REGIME_TRENDING_BEAR__RISK_MEDIUM [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10 [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- VOLUME_SCORE_GE_10 [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.

Shadow Blockers:
⛔ کل نمونه‌های ارزیابی‌شده Shadow کمتر از 30 است: 28

Shadow Recommendations:
→ Shadow هنوز در حال ساخت داده است؛ فعال‌ترین gate: STRUCTURE_SCORE_GE_10 | signals=19, evaluated=19.
→ برای هر gate حداقل 30 نمونه Forward کامل لازم است.
→ Regime Shadow gateهای v6.1 فعال شده‌اند، اما هنوز هیچ تصمیم Forward آن‌ها را پاس نکرده است.
→ سه gate پایه که باید زیر نظر بمانند: VOLUME_SCORE_GE_10، RISK_MEDIUM، HISTORICAL_EDGE_SCORE_GE_1.

Warnings:
⚠️ Shadow Gate هیچ Paper Trade و هیچ سفارش واقعی ایجاد نمی‌کند؛ فقط برچسب تحقیقاتی می‌زند.
⚠️ Gateهای پایه از Backtest و Gateهای Regime از v6.1 Regime-Gate Matrix آمده‌اند و باید در Forward مستقل تأیید شوند.
⚠️ تا وقتی هر gate، مخصوصاً gateهای Regime، حداقل 30 نمونه Forward کامل ندارد، نتیجه آماری قابل اتکا نیست.
==============================================================================================================

==============================================================================================================
🧬 Freakto Regime-Split Gate Matrix v6.1.0
==============================================================================================================
Status: NO_BACKTEST_DATA
Run ID: regime_gate_matrix_20260720_171230
Horizon: 24h
Min Samples: 10 | Candidate Min Samples: 30
Baseline Net: samples=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0%
Regimes Seen: 
Gates Tested: 0 | Candidates: 0

Regime Candidates:
- هیچ داده‌ای موجود نیست.

Top Regime × Gate:
- هیچ داده‌ای موجود نیست.

Top Regime × Gate × Side:
- هیچ داده‌ای موجود نیست.

Top Regime × Side:
- هیچ داده‌ای موجود نیست.

Top Regime × Symbol:
- هیچ داده‌ای موجود نیست.

Avoid Regimes:

Shadow Proposals:
- فعلاً proposal قابل اتکا برای Shadow اضافه نشد.

Blockers:
⛔ هیچ historical_backtest_evaluations کامل برای ساخت Regime-Gate Matrix پیدا نشد.
==============================================================================================================

==============================================================================================================
🔎 Freakto Forward Shadow Coverage & Bull Regime Probe v6.3.1
==============================================================================================================
Status                 : FORWARD_PROMISING_BACKTEST_CONFLICTS_FOUND
Run ID                 : forward_shadow_coverage_20260720_171230
Horizon                : 24h
Decision Rows          : 93
Directional Decisions  : 42
Evaluation Rows        : 92
Complete Evaluations   : 28
Shadow Signals         : 28
Evaluated Shadow       : 28

Forward Regime Coverage:
- TRENDING_BULL: rows=52 | directional=35 | share=55.91% | direct=0 | proxy/text=0
- UNKNOWN: rows=32 | directional=6 | share=34.41% | direct=0 | proxy/text=0
- TRENDING_BEAR: rows=8 | directional=1 | share=8.6% | direct=0 | proxy/text=0
- SIDEWAYS: rows=1 | directional=0 | share=1.08% | direct=0 | proxy/text=0

Shadow Gate Coverage:
- STRUCTURE_SCORE_GE_10: signals=19 | eval=19 | avg=0.5264% | win=84.21% | dominant_regime=TRENDING_BULL
- HISTORICAL_EDGE_SCORE_GE_1: signals=8 | eval=8 | avg=-1.2246% | win=12.5% | dominant_regime=TRENDING_BULL
- RISK_MEDIUM: signals=1 | eval=1 | avg=0.5361% | win=100.0% | dominant_regime=TRENDING_BULL

Bull Regime Probes:
- BULL_STRUCTURE_SCORE_GE_10: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=14 | fwd_avg=0.8834% | fwd_win=100.0% | src=shadow_ledger_sync | bt_n=0 | bt_net=0.0%
- BULL_STRUCTURE_SCORE_GE_10_LONG: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=14 | fwd_avg=0.8834% | fwd_win=100.0% | src=shadow_ledger_sync | bt_n=0 | bt_net=0.0%
- BULL_RISK_MEDIUM: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=1 | fwd_avg=0.5361% | fwd_win=100.0% | src=shadow_ledger_sync | bt_n=0 | bt_net=0.0%
- BULL_VOLUME_SCORE_GE_10: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | src=decision_evaluations | bt_n=0 | bt_net=0.0%
- BULL_SCORE_GE_80: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | src=decision_evaluations | bt_n=0 | bt_net=0.0%
- BULL_BNB_LONG_SCORE_GE_60: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | src=decision_evaluations | bt_n=0 | bt_net=0.0%

Backtest/Forward Contradictions:
⚠️ BULL_STRUCTURE_SCORE_GE_10: Forward avg=0.8834% با n=14 اما Backtest net=0.0% است.
⚠️ BULL_STRUCTURE_SCORE_GE_10_LONG: Forward avg=0.8834% با n=14 اما Backtest net=0.0% است.
⚠️ BULL_RISK_MEDIUM: Forward avg=0.5361% با n=1 اما Backtest net=0.0% است.

Blockers:
⛔ Shadow evaluated samples کمتر از 30 است: 28

Recommendations:
→ فعال‌ترین Bull probe فعلی: BULL_STRUCTURE_SCORE_GE_10 | forward n=14 | avg=0.8834% | verdict=FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT.
→ Bull probe فقط مشاهده‌ای است؛ تا وقتی Backtest/Forward هر دو robust نشوند، به Shadow Candidate ارتقا نده.
→ برای تصمیم‌گیری بعدی، STRUCTURE_SCORE_GE_10 را جداگانه به تفکیک regime در Forward دنبال کن.

Warnings:
⚠️ این ماژول فقط coverage و probe تحقیقاتی می‌سازد؛ هیچ Paper/Live فعال نمی‌کند.
⚠️ Bull probeها کاندید قطعی نیستند؛ v6.3.1 اگر لازم باشد از Shadow Ledger برای همگام‌سازی ارزیابی‌ها استفاده می‌کند.
⚠️ برچسب‌های legacy/proxy regime برای تحقیق‌اند؛ Forward جدید DIRECT_ENGINE ارزش بیشتری دارد.
==============================================================================================================

==============================================================================================================
🧬 Freakto Root Cause Discovery Engine v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_PRIMARY_PROBABLE
Run ID                 : root_cause_20260720_171230
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Decision Side/Score    : NEUTRAL | 48
Narrative              : MACRO_POLICY_DOMINANT | MIXED_OR_NEUTRAL | MACRO_POLICY
Causal Context         : MULTI_SOURCE_EVENT_CONSENSUS | catalyst=59/100

Root Cause:
- Primary              : MACRO_POLICY_PRESSURE
- Direction            : BEARISH
- Confidence           : HIGH
- Probability Share    : 62.98%
- Evidence Quality     : HIGH
- Verdict              : PRIMARY_PROBABLE_ROOT_CAUSE
- Summary              : Probable root cause=MACRO_POLICY_PRESSURE; direction=BEARISH; confidence=HIGH; share=62.98%. قوی‌ترین evidence از federal_reserve_speeches است: Market narrative theme: MACRO_POLICY
- Evidence Total       : 11 | official=8 | event_rows=8

Top Cause Hypotheses:
- MACRO_POLICY_PRESSURE: p=62.98% | score=60.1338 | dir=BEARISH | evidence=8 | verdict=PRIMARY_PROBABLE_CAUSE
- TECHNICAL_STRUCTURE_MOMENTUM: p=18.85% | score=18.0 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- EXCHANGE_MARKET_ACCESS: p=9.46% | score=9.035 | dir=BULLISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- MIXED_EVENT_CONFLICT: p=8.7% | score=8.31 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE

Recommendations:
→ automatic_event_collector، causal_intelligence، market_narrative و narrative_decision را قبل از root_cause اجرا کن.
→ اگر primary_root_cause چند هفته متوالی با outcome مثبت/منفی همبستگی داشت، بعداً می‌تواند وارد Root-Cause Gate Simulator شود.
→ برای افزایش دقت، داده‌های derivatives/on-chain/ETF flow را به evidence registry اضافه کن.

Warnings:
⚠️ Root Cause Discovery احتمالات علّی پژوهشی می‌سازد؛ علت قطعی یا سیگنال خرید/فروش نیست.
⚠️ این ماژول از outcome/return آینده برای تشخیص علت استفاده نمی‌کند تا leakage ایجاد نشود.
⚠️ تا وقتی علت‌ها با forward outcomes اعتبارسنجی نشوند، Paper/Live نباید از آن‌ها استفاده کند.
==============================================================================================================

==============================================================================================================
🧪 Freakto Root Cause Forward Validation v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_FORWARD_MIXED_OR_WEAK
Run ID                 : root_cause_forward_20260720_171230
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 92 / 89
Root Cause Rows        : 41
Evaluated Cells        : 118
Eligible Causes        : 1
Research Candidates    : 0
Promising Low Sample   : 0
Min Samples / Deadzone : 10 / 0.0%

Top Root-Cause Forward Results:
- MACRO_POLICY_PRESSURE | BEARISH | n24=38 hit24=60.53% avg24=0.0391% | n12=39 hit12=56.41% | score=12.8179 | MIXED_BUT_POSITIVE_FORWARD_EDGE

Recommendations:
→ ابتدا decision_evaluator.py را اجرا کن تا market_return_after_* برای تصمیم‌ها ساخته شود.
→ Root Causeهایی که hit-rate پایدار و sample کافی دارند بعداً می‌توانند وارد Root-Cause Gate Simulator شوند.
→ تا قبل از sample کافی، نتیجه فقط Research/Shadow بماند و Paper/Live فعال نشود.

Warnings:
⚠️ Root Cause Forward Validation فقط رابطه علت‌های پژوهشی با outcome بعدی را می‌سنجد؛ سیگنال خرید/فروش نیست.
⚠️ این validation باید چند هفته/ماه sample جمع کند تا قابل اتکا شود.
==============================================================================================================

==============================================================================================================
🧫 Freakto Root Cause Sample Accumulator v8.2.0
==============================================================================================================
Status                 : ROOT_CAUSE_SAMPLE_TARGET_REACHED_MIXED
Run ID                 : root_cause_samples_20260720_171230
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 92 / 89
Root Cause Rows        : 41
Evaluated Cells        : 118
Unique Root Causes     : 1
Validation Status      : ROOT_CAUSE_FORWARD_MIXED_OR_WEAK
Candidates / Promising : 0 / 0
Min/Research/Candidate : 10 / 30 / 90 cells
More decisions needed  : min=0 | research=0 | candidate=0

Root Cause Buckets:
- MACRO_POLICY_PRESSURE | BEARISH | rows=41 cells=118 | n24=38 hit24=60.53% avg24=0.0391% | maturity=CANDIDATE_SAMPLE_READY | PROMISING_RESEARCH_WATCHLIST

Recommendations:
→ چرخه Forward را هر 4 ساعت یا با GitHub Actions اجرا کن تا Root Cause rows بیشتر شود.
→ پس از هر root_cause_dashboard.py، decision_evaluator.py و سپس root_cause_forward_validation_dashboard.py را اجرا کن.
→ تا وقتی حداقل 30-50 تصمیم دارای Root Cause جمع نشده، نتیجه فقط Research/Shadow بماند.

Warnings:
⚠️ Root Cause Sample Tracker فقط بلوغ نمونه‌ها را می‌سنجد؛ Paper/Live فعال نمی‌کند.
⚠️ Promotion واقعی فقط بعد از Forward validation پایدار و sample کافی مجاز است.
==============================================================================================================

==============================================================================================================
🕸️ Freakto Evidence Graph Engine v9.0.0
==============================================================================================================
Status                 : EVIDENCE_GRAPH_CANDIDATE_SAMPLE_READY
Run ID                 : evidence_graph_20260720_171230
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 92 / 89
Graph Rows             : 38
Nodes / Edges / Paths  : 22 / 45 / 34
Graph Maturity         : CANDIDATE_SAMPLE_READY
Min/Research/Candidate : 10 / 30 / 90 evaluated cells

Top Evidence Paths:
- EVIDENCE_SOURCE:FEDERAL_RESERVE_PRESS -> ROOT_CAUSE:MACRO_POLICY_PRESSURE_BEARISH -> OUTCOME:ROOT_CAUSE_HIT_24H | n=3 hit24=100.0% avg24=2.5841% | LOW_SAMPLE_EDGE
- EVIDENCE_SOURCE:FEDERAL_RESERVE_SPEECHES -> ROOT_CAUSE:MACRO_POLICY_PRESSURE_BEARISH -> OUTCOME:ROOT_CAUSE_HIT_24H | n=1 hit24=100.0% avg24=2.1886% | LOW_SAMPLE_EDGE
- EVIDENCE_SOURCE:FEDERAL_RESERVE_SPEECHES -> ROOT_CAUSE:MACRO_POLICY_PRESSURE_BEARISH -> OUTCOME:ROOT_CAUSE_HIT_24H | n=1 hit24=100.0% avg24=1.9251% | LOW_SAMPLE_EDGE
- EVIDENCE_SOURCE:FEDERAL_RESERVE_SPEECHES -> ROOT_CAUSE:MACRO_POLICY_PRESSURE_BEARISH -> OUTCOME:ROOT_CAUSE_HIT_24H | n=1 hit24=100.0% avg24=1.6197% | LOW_SAMPLE_EDGE
- EVIDENCE_SOURCE:FEDERAL_RESERVE_PRESS -> ROOT_CAUSE:MACRO_POLICY_PRESSURE_BEARISH -> OUTCOME:ROOT_CAUSE_HIT_24H | n=1 hit24=100.0% avg24=1.403% | LOW_SAMPLE_EDGE

Root Cause Learning Signals:
- MACRO_POLICY_PRESSURE | BEARISH | n24=38 hit24=60.53% avg24=0.0391% | EVIDENCE_WEIGHT_CAN_BE_REVIEWED_UP

Recommendations:
→ چرخه Forward را منظم اجرا کن تا مسیرهای evidence به outcomeهای بیشتری وصل شوند.
→ مسیرهایی که چند هفته متوالی hit-rate و signed-return مثبت دارند بعداً می‌توانند وارد Evidence Weight Review شوند.
→ اگر یک منبع یا روایت در Forward چندبار fail شد، وزن آن باید فقط بعد از sample کافی بازبینی شود.

Warnings:
⚠️ Evidence Graph فقط رابطه‌های پژوهشی بین شواهد، روایت، علت و outcome را می‌سازد؛ سیگنال خرید/فروش نیست.
⚠️ تا وقتی sample کافی وجود نداشته باشد، هیچ وزن evidence نباید برای Paper/Live تغییر کند.
==============================================================================================================

================================================================================================================
Freakto Market Replay Engine v10.3.0
================================================================================================================
Status                 : NO_REPLAY_ROWS
Run ID                 : market_replay_status
Mode                   : REPLAY_SAFE_TECHNICAL_CORE
Symbols Completed      : 0/0
Candles / Rows         : 0 / 0
Complete / Directional : 0 / 0
Actionable / Neutral   : 0 / 0
Evaluation Horizon     : 1d (6 candles)
Win Rate Horizon       : 0.00%
Avg Gross / Net        : 0.0000% / 0.0000%
Profit Factor          : 0.0
Leakage Audit          : FAILED_NO_REPLAY_ROWS
Historical Context     : UNKNOWN

Blockers:
[BLOCKER] هیچ ردیف Market Replay ساخته نشد.
================================================================================================================

==========================================================================================================================
🧬 Freakto Score Calibration & Feature Attribution Lab v10.3.0
==========================================================================================================================
Status                 : SCORE_CALIBRATION_BLOCKED
Run ID                 : replay_score_calibration_20260720_171230_369030
Rows Total / Analyzed  : 0 / 0
Score Verdict          : UNKNOWN
Test Monotonicity      : 0.0
Test Band Violations   : 0
High-Low Test Net      : 0.0%
Shadow Candidates      : 0

Blockers:
⛔ Replay evaluations file does not exist: logs/market_replay/market_replay_evaluations.csv

Warnings:
⚠️ Score Calibration is research-only and never changes strategy settings.
==========================================================================================================================

==============================================================================================================
🧠 Freakto Research Robustness & Intelligence Suite v10.2.0
==============================================================================================================
Status: RESEARCH_SUITE_WITH_BLOCKERS
Run ID: research_suite_20260720_171230

Sections:
- gate_robustness: NO_BACKTEST_DATA
- cost_adjusted_backtest: NO_BACKTEST_DATA
- meta_labeling: LOW_SAMPLE_META_LABELING
- ensemble_explainability: EXPLAINABILITY_READY
- data_enrichment: ENRICHMENT_CONNECTORS_PRESENT
- regime_research: NO_BACKTEST_DATA
- forward_regime_labeling: FORWARD_REGIME_LABELING_READY
- regime_gate_matrix: NO_BACKTEST_DATA
- regime_shadow_gates: REGIME_SHADOW_GATES_ACTIVE
- forward_shadow_coverage: FORWARD_PROMISING_BACKTEST_CONFLICTS_FOUND
- automatic_event_collector: AUTO_EVENT_COLLECTOR_LEDGER_ONLY
- causal_intelligence: CAUSAL_CONTEXT_LEDGER_ONLY
- market_narrative: MARKET_NARRATIVE_WEAK_EVIDENCE
- narrative_decision_conflict: NARRATIVE_CONTEXT_ONLY
- root_cause_discovery: ROOT_CAUSE_PRIMARY_PROBABLE
- root_cause_forward_validation: ROOT_CAUSE_FORWARD_MIXED_OR_WEAK
- root_cause_sample_tracker: ROOT_CAUSE_SAMPLE_TARGET_REACHED_MIXED
- evidence_graph: EVIDENCE_GRAPH_CANDIDATE_SAMPLE_READY
- market_replay: NO_REPLAY_ROWS
- replay_score_calibration: SCORE_CALIBRATION_BLOCKED
- cross_exchange_validation: NO_BACKTEST_DATA
- research_db: RESEARCH_DB_READY
- pipeline_health: PIPELINE_HEALTHY
- strict_readiness: STRICT_READINESS_RESEARCH_ONLY
- position_sizing_lab: NO_BACKTEST_DATA
- airdrop_shadow_research: AIRDROP_SHADOW_READY
- static_dashboard: STATIC_DASHBOARD_READY

Gate Robustness Highlights:

Regime-Gate Matrix Highlights:
- NO_BACKTEST_DATA | candidates=0 | horizon=24h

Forward Regime Labeling:
- FORWARD_REGIME_LABELING_READY | known=61 | unknown=32 | injected=0

Regime Shadow Gate Highlights:
- REGIME_SHADOW_GATES_ACTIVE | regime_gates=4 | signals=0 | eval=28
- REGIME_TRENDING_BEAR__RISK_MEDIUM: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%
- REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%

Forward Shadow Coverage / Bull Probe:
- FORWARD_PROMISING_BACKTEST_CONFLICTS_FOUND | decisions=93 | shadow_signals=28 | eval_shadow=28
- BULL_STRUCTURE_SCORE_GE_10: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=14 | fwd_avg=0.8834% | bt_net=0.0%
- BULL_STRUCTURE_SCORE_GE_10_LONG: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=14 | fwd_avg=0.8834% | bt_net=0.0%
- BULL_RISK_MEDIUM: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=1 | fwd_avg=0.5361% | bt_net=0.0%
- BULL_VOLUME_SCORE_GE_10: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | bt_net=0.0%

Causal/Event Intelligence:
- CAUSAL_CONTEXT_LEDGER_ONLY | sources_ok=8 | trusted_ok=8 | catalyst=50/100 | conflict=LOW
- primary=MULTI_SOURCE_EVENT_CONSENSUS | verdict=CAUSAL_CONTEXT_NEUTRAL

Market Narrative Engine:
- MARKET_NARRATIVE_WEAK_EVIDENCE | label=MACRO_POLICY_DOMINANT | dir=MIXED_OR_NEUTRAL | theme=MACRO_POLICY | score=-2.3109
- accepted=3 | noise_filtered=0 | risk=HIGH | conflict=LOW

Narrative/Decision Conflict:
- NARRATIVE_CONTEXT_ONLY | side=NEUTRAL | narrative=MIXED_OR_NEUTRAL | alignment=CONTEXT_ONLY
- conflict=10/100 | adj=-5 | verdict=NEUTRAL_DECISION_CONTEXT_ONLY

Market Replay v10:
- NO_REPLAY_ROWS | rows=0 | complete=0 | directional=0
- test/research audit=FAILED_NO_REPLAY_ROWS | avg_net24=0.0% | PF=0.0

Replay Score Calibration v10.2:
- SCORE_CALIBRATION_BLOCKED | rows=0 | score=None | candidates=0
- test_monotonicity=None | high-low=None% | violations=None

Root Cause Discovery:
- ROOT_CAUSE_PRIMARY_PROBABLE | primary=MACRO_POLICY_PRESSURE | dir=BEARISH | conf=HIGH | p=62.98%
- quality=HIGH | evidence=11 | verdict=PRIMARY_PROBABLE_ROOT_CAUSE

Root Cause Forward Validation:
- ROOT_CAUSE_FORWARD_MIXED_OR_WEAK | rows=41 | cells=118 | candidates=0 | low_sample=0
- MACRO_POLICY_PRESSURE BEARISH: n24=38 hit24=60.53% avg24=0.0391% | MIXED_BUT_POSITIVE_FORWARD_EDGE

Strict Readiness:
- STRICT_READINESS_RESEARCH_ONLY | blockers=4
  ⛔ Backtest sample کمتر از 100 است.
  ⛔ Backtest net expectancy از نظر CI95 بالای صفر نیست.
  ⛔ Forward net expectancy مثبت نیست.
  ⛔ پوشش regime کافی نیست؛ حداقل دو رژیم معتبر لازم است.

Pipeline Health:
- PIPELINE_HEALTHY | alerts=0

Suite Blockers:
⛔ gate_robustness: هیچ دیتای backtest کامل برای robust validation وجود ندارد.
⛔ cost_adjusted_backtest: Backtest data موجود نیست.
⛔ meta_labeling: برای meta-labeling حداقل 120 نمونه لازم است.
⛔ regime_research: Backtest data موجود نیست.
⛔ regime_gate_matrix: هیچ historical_backtest_evaluations کامل برای ساخت Regime-Gate Matrix پیدا نشد.
⛔ regime_shadow_gates: کل نمونه‌های ارزیابی‌شده Shadow کمتر از 30 است: 28
⛔ forward_shadow_coverage: Shadow evaluated samples کمتر از 30 است: 28
⛔ market_replay: هیچ ردیف Market Replay ساخته نشد.
⛔ replay_score_calibration: Replay evaluations file does not exist: logs/market_replay/market_replay_evaluations.csv
⛔ cross_exchange_validation: Backtest data موجود نیست.
⛔ strict_readiness: Backtest sample کمتر از 100 است.
⛔ strict_readiness: Backtest net expectancy از نظر CI95 بالای صفر نیست.

Safety: هیچ بخش v6 تا v10 سفارش واقعی ارسال نمی‌کند؛ Market Replay نیز فقط Research/Backtest است.
==============================================================================================================

==============================================================================================================
🚦 Freakto Advanced Live Readiness Score v4.7.1
==============================================================================================================
Created UTC       : 2026-07-20T17:12:30.795248+00:00
Readiness Level   : PAPER_TRADING_PHASE
Readiness Score   : 66/100
Paper Ready       : True
Live Ready        : False
Allowed Risk      : 0.00%
Edge Quality      : EARLY_EDGE_OBSERVED
Regime Verdict    : REGIME_DATA_COLLECTING

Core Stats:
- Complete evaluations: 89
- Closed paper trades: 0
- Paper expectancy: 0.0000R
- Decision Profit Factor: 1.9236
--------------------------------------------------------------------------------------------------------------
Component : Data Sufficiency
Score     : 11/20
Status    : PARTIAL
Note      : Complete evaluations: 89/100
Note      : Closed paper trades: 0/30
Blocker   : Complete evaluations هنوز کافی نیست: 89/100
Blocker   : Closed paper trades هنوز کافی نیست: 0/30
--------------------------------------------------------------------------------------------------------------
Component : Decision Edge
Score     : 23/23
Status    : PARTIAL
Note      : Decision quality: VALIDATING_POSITIVE
Note      : Directional Win 61.80% | Expectancy 0.4140pct | PF 1.9236
Note      : Stop 34.83% | Sharpe-like 2.4392
Blocker   : Decision sample کمتر از 100 است: 89
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
Score     : 13/18
Status    : PARTIAL
Note      : Regime verdict: REGIME_DATA_COLLECTING
Note      : Known/Unknown: 61/28
Note      : Best/Worst: TRENDING_BEAR/UNKNOWN
Blocker   : هنوز هیچ رژیم با Edge مثبت قابل اتکا مشخص نشده است.
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
Note      : Stop Hit Rate کنترل‌شده است: 34.83%

Warnings:
⚠️ Paper Trading هنوز نتیجه بسته‌شده ندارد.
⚠️ Market Replay v10 باید روی Test split و بعد در Forward تأیید شود؛ این مانع Paper آزمایشی نیست اما Live را مسدود می‌کند.

Hard Blockers:
⛔ Complete evaluations هنوز کافی نیست: 89/100
⛔ Closed paper trades هنوز کافی نیست: 0/30
⛔ Decision sample کمتر از 100 است: 89
⛔ Paper sample کمتر از 30 معامله بسته‌شده است: 0
⛔ Paper expectancy هنوز مثبت نیست.
⛔ هنوز هیچ رژیم با Edge مثبت قابل اتکا مشخص نشده است.
⛔ Market Replay هنوز برای Live معتبر نیست: NO_REPLAY_ROWS (rows=0, audit=FAILED_NO_REPLAY_ROWS)

Conclusion: پروژه در فاز Paper/Forward Test است؛ پول واقعی هنوز مجاز نیست.
==============================================================================================================