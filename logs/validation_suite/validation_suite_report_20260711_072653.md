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
Created UTC      : 2026-07-11T07:26:52.821349+00:00
Combined Quality : EARLY_EDGE_OBSERVED

--------------------------------------------------------------------------------------------------------------
Source       : decision_evaluations
Quality      : MIXED_VALIDATION
Samples      : 51 | Positive/Negative/Flat: 39/12/0
Directional Win Rate: 76.47%
Expectancy   : 0.7245pct
ProfitFactor : 3.1353
Sharpe-like  : 3.3404 | Sortino-like: 4.5688
Max Drawdown : -12.6696pct
Best/Worst   : 3.8877pct / -3.2625pct
Avg Win/Loss : 1.3911pct / -1.4420pct
Stop Rate    : 45.10%
Target Hit   : T1 50.98% | T2 45.10% | T3 21.57%
Definition   : Directional Win = positive evaluated return; Target Hit = target_1_hit.
MFE/MAE Avg  : 2.8769% / -2.2024%
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
⛔ Decision COMPLETE کمتر از 100 است: 51
⛔ Paper trades بسته‌شده کمتر از 30 است: 0
==============================================================================================================

==============================================================================================================
🧬 Freakto Regime Performance Matrix v4.7.1
==============================================================================================================
Created UTC          : 2026-07-11T07:26:52.851411+00:00
Overall Verdict      : REGIME_DATA_COLLECTING
Known/Unknown Regime : 51 / 0
Best/Worst Regime    : TRENDING_BEAR / TRENDING_BULL
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : TRENDING_BULL / LONG / WATCHLIST
Samples            : 22
Target 1 Hit       : 95.45%
Directional Win    : 81.82%
Avg 24h            : 0.4287%
Profit Factor      : 2.6573
Stop Rate          : 86.36%
Avg Score          : 65.27
Verdict            : MIXED_POSITIVE
Note               : بازده مثبت است اما کیفیت آماری کامل نیست.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : TRENDING_BULL / NEUTRAL / MONITOR_ONLY
Samples            : 16
Target 1 Hit       : 0.00%
Directional Win    : 62.50%
Avg 24h            : 0.9190%
Profit Factor      : 3.4814
Stop Rate          : 0.00%
Avg Score          : 30.38
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
Samples            : 4
Target 1 Hit       : 100.00%
Directional Win    : 75.00%
Avg 24h            : 0.3038%
Profit Factor      : 1.4278
Stop Rate          : 50.00%
Avg Score          : 51.00
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
Created UTC       : 2026-07-11T07:26:52.864155+00:00
Portfolio Status  : MEMORY_BUILDING
Symbols           : 1
Total scans       : 0
Complete evals    : 51
Closed paper      : 0
Best memory symbol: BTC/USDT
Best paper symbol : NONE

Warnings:
⚠️ Closed paper trades کل پورتفو کمتر از 30 است: 0
--------------------------------------------------------------------------------------------------------------
Symbol        : BTC/USDT
Status        : SYMBOL_EDGE_EARLY | Confidence MEDIUM
Scans/Dec/Eval: 0 / 55 / 51
Latest        : UNKNOWN | Rec UNKNOWN | MTF UNKNOWN
Avg Score/Conf/Opp: 0.00 / 0.00% / 0.00
Directional/T1/Avg24: 76.47% / 50.98% / 0.7245%
Paper        : closed 0 | win 0.00% | exp 0.0000R | PF 0.0000
Rec rates    : actionable 0.00% | monitor 0.00% | ignore 0.00%
Note         : Decision edge اولیه برای این نماد مثبت است.
Blocker      : Closed paper trades کمتر از 30 است: 0
==============================================================================================================

==============================================================================================================
🎯 Freakto Confidence Calibration Engine v5.0
==============================================================================================================
Created UTC       : 2026-07-11T07:26:52.878573+00:00
Quality           : CALIBRATION_WEAK
Samples           : 51
Overall Dir Win   : 76.47%
Overall T1 Hit    : 50.98%
Mean Calib Error  : 32.21 pts

Blockers:
⛔ Confidence داخلی با outcome واقعی فاصله زیادی دارد.
⛔ برای استفاده عملی، حداقل 100 ارزیابی لازم است: 51/100
--------------------------------------------------------------------------------------------------------------
Confidence Label Buckets
Low            | n= 28 | Pred  25.0% | Dir  71.43% | T1  14.29% | Gap +46.43 | UNDER_CONFIDENT
Medium         | n= 15 | Pred  55.0% | Dir  73.33% | T1  93.33% | Gap +18.33 | UNDER_CONFIDENT
Medium-High    | n=  8 | Pred  67.5% | Dir 100.00% | T1 100.00% | Gap +32.50 | LOW_SAMPLE
--------------------------------------------------------------------------------------------------------------
Score Buckets
score_10_19    | n=  3 | Pred  14.5% | Dir  66.67% | T1   0.00% | Gap +52.17 | LOW_SAMPLE
score_20_29    | n=  5 | Pred  24.5% | Dir  80.00% | T1   0.00% | Gap +55.50 | LOW_SAMPLE
score_30_39    | n= 14 | Pred  34.5% | Dir  71.43% | T1   0.00% | Gap +36.93 | UNDER_CONFIDENT
score_40_49    | n=  4 | Pred  44.5% | Dir  50.00% | T1  50.00% | Gap  +5.50 | LOW_SAMPLE
score_50_59    | n=  7 | Pred  54.5% | Dir  85.71% | T1 100.00% | Gap +31.21 | LOW_SAMPLE
score_60_69    | n= 10 | Pred  64.5% | Dir  70.00% | T1  90.00% | Gap  +5.50 | WELL_CALIBRATED_DIRECTIONAL
score_70_79    | n=  8 | Pred  74.5% | Dir 100.00% | T1 100.00% | Gap +25.50 | LOW_SAMPLE
==============================================================================================================

==============================================================================================================
🎲 Freakto Monte Carlo Risk Lab v5.0
==============================================================================================================
Created UTC      : 2026-07-11T07:26:52.929520+00:00
Risk Quality     : RISK_PROFILE_ACCEPTABLE
Source           : decision_evaluations_fallback (pct)
Samples          : 51
Iterations       : 2000
Trades / Run     : 100
Expected / Trade : 0.7245pct
Best / Worst Samp: 3.8877pct / -3.2625pct
--------------------------------------------------------------------------------------------------------------
Median Final     : 72.6286pct
Mean Final       : 72.8797pct
P05 / P95 Final  : 46.5436pct / 98.5719pct
Median Max DD    : -5.9287pct
P95 Max DD       : -10.5366pct
Prob Loss        : 0.00%
Prob Ruin        : 6.75% | Threshold -10.00pct

Notes:
✓ Median path مثبت و Probability of ruin پایین است.

Warnings:
⚠️ Paper Trade کافی نبود؛ شبیه‌سازی با decision returns درصدی انجام شد، نه R واقعی.
==============================================================================================================

==============================================================================================================
🧭 Freakto Forward Test Status v9.0.0
==============================================================================================================
Status          : FORWARD_TEST_COLLECTING
Progress Score  : 50/100
Readiness Level : RESEARCH_ONLY
Paper Ready     : False
Live Ready      : False

Data Progress:
- Complete evaluations : 51/100
- Closed paper trades  : 0/30
- Open paper trades    : 0
- Total paper trades   : 0
- Regime-labeled       : 51/30
- Unknown regime       : 0
- Symbols evaluated    : 1
- Symbols scanned      : 0
- Forward runs         : 24/26 successful
- Forward days         : 7/30
- First run UTC        : 2026-07-05T17:39:28.376869+00:00
- Last run UTC         : 2026-07-11T07:25:47.173544+00:00

Notes:
✓ Regime-labeled samples برای تحلیل اولیه کافی است.

Blockers:
⛔ Complete evaluations کمتر از 100 است: 51
⛔ Closed paper trades کمتر از 30 است: 0
⛔ روزهای Forward Test کمتر از 30 است: 7

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
Run ID                 : backtest_diag_20260711_072652
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
Run ID                 : gate_sim_20260711_072652
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
Run ID                 : forward_regime_label_20260711_072652
Apply Changes          : False
Decision Rows          : 55
Known Before / After   : 55 / 55
Unknown Before / After : 0 / 0
Injected Decision Rows : 0
Preserved Direct Rows  : 55
Direct/Text/Proxy      : 22 / 33 / 0
Evaluation Rows        : 54
Patched Evaluations    : 0
Eval Known After       : 54

Decision Regime Counts:
- TRENDING_BULL: 46
- TRENDING_BEAR: 8
- SIDEWAYS: 1

Recommendations:
→ بعد از اجرای cycle جدید، regime_shadow_gate_dashboard.py --compact را دوباره بررسی کن.

Warnings:
⚠️ Regime injection فقط از داده‌های لحظه تصمیم استفاده می‌کند؛ outcome/return/target/stop استفاده نمی‌شود.
⚠️ برچسب‌های LOW_CONF_PROXY برای Research هستند و باید در Forward واقعی بیشتر validate شوند.
==============================================================================================================

==============================================================================================================
🧪 Freakto Regime Shadow Gate Activator v6.2.0
==============================================================================================================
Status                 : SHADOW_COLLECTING_FORWARD_DATA
Run ID                 : shadow_gate_20260711_072652
Horizon                : 24h
Min Samples            : 30
Decisions              : 55
Directional Decisions  : 31
Gates Tracked          : 11
Shadow Signals         : 20
Evaluated Shadow       : 16
Pending Shadow         : 1
Confirmed Candidates   : 0
Building Candidates    : 11
Rejected Candidates    : 0

Gate Shadow Metrics:
- STRUCTURE_SCORE_GE_10 [SHADOW_BUILDING]: signals=14 | eval=14 | pending=0 | avg=0.8834% | win=100.0% | T1=100.0% | Stop=85.71% | MFE/MAE=1.785 | warn=Forward evaluated samples کمتر از حداقل 30 است: 14
- HISTORICAL_EDGE_SCORE_GE_1 [SHADOW_BUILDING]: signals=5 | eval=2 | pending=1 | avg=-3.0511% | win=0.0% | T1=100.0% | Stop=100.0% | MFE/MAE=0.317 | warn=Forward evaluated samples کمتر از حداقل 30 است: 2
- REGIME_TRENDING_BEAR__RISK_MEDIUM [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10 [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- VOLUME_SCORE_GE_10 [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- RISK_MEDIUM [SHADOW_BUILDING]: signals=1 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=Forward evaluated samples کمتر از حداقل 30 است: 0

Shadow Blockers:
⛔ کل نمونه‌های ارزیابی‌شده Shadow کمتر از 30 است: 16

Shadow Recommendations:
→ Shadow هنوز در حال ساخت داده است؛ فعال‌ترین gate: STRUCTURE_SCORE_GE_10 | signals=14, evaluated=14.
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
Run ID: regime_gate_matrix_20260711_072653
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
Run ID                 : forward_shadow_coverage_20260711_072653
Horizon                : 24h
Decision Rows          : 55
Directional Decisions  : 31
Evaluation Rows        : 54
Complete Evaluations   : 16
Shadow Signals         : 20
Evaluated Shadow       : 16

Forward Regime Coverage:
- TRENDING_BULL: rows=46 | directional=30 | share=83.64% | direct=0 | proxy/text=0
- TRENDING_BEAR: rows=8 | directional=1 | share=14.55% | direct=0 | proxy/text=0
- SIDEWAYS: rows=1 | directional=0 | share=1.82% | direct=0 | proxy/text=0

Shadow Gate Coverage:
- STRUCTURE_SCORE_GE_10: signals=14 | eval=14 | avg=0.8834% | win=100.0% | dominant_regime=TRENDING_BULL
- HISTORICAL_EDGE_SCORE_GE_1: signals=5 | eval=2 | avg=-3.0511% | win=0.0% | dominant_regime=TRENDING_BULL
- RISK_MEDIUM: signals=1 | eval=0 | avg=0.0% | win=0.0% | dominant_regime=TRENDING_BULL

Bull Regime Probes:
- BULL_STRUCTURE_SCORE_GE_10: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=14 | fwd_avg=0.8834% | fwd_win=100.0% | src=shadow_ledger_sync | bt_n=0 | bt_net=0.0%
- BULL_STRUCTURE_SCORE_GE_10_LONG: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=14 | fwd_avg=0.8834% | fwd_win=100.0% | src=shadow_ledger_sync | bt_n=0 | bt_net=0.0%
- BULL_VOLUME_SCORE_GE_10: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | src=decision_evaluations | bt_n=0 | bt_net=0.0%
- BULL_RISK_MEDIUM: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | src=decision_evaluations | bt_n=0 | bt_net=0.0%
- BULL_SCORE_GE_80: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | src=decision_evaluations | bt_n=0 | bt_net=0.0%
- BULL_BNB_LONG_SCORE_GE_60: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | src=decision_evaluations | bt_n=0 | bt_net=0.0%

Backtest/Forward Contradictions:
⚠️ BULL_STRUCTURE_SCORE_GE_10: Forward avg=0.8834% با n=14 اما Backtest net=0.0% است.
⚠️ BULL_STRUCTURE_SCORE_GE_10_LONG: Forward avg=0.8834% با n=14 اما Backtest net=0.0% است.

Blockers:
⛔ Shadow evaluated samples کمتر از 30 است: 16

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
Status                 : ROOT_CAUSE_MIXED_WITH_CONTRADICTIONS
Run ID                 : root_cause_20260711_072653
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Decision Side/Score    : LONG | 62
Narrative              : MIXED_NARRATIVE_CONFLICT | BEARISH | MACRO_POLICY
Causal Context         : MULTI_SOURCE_EVENT_CONSENSUS | catalyst=44/100

Root Cause:
- Primary              : MACRO_POLICY_PRESSURE
- Direction            : BEARISH
- Confidence           : MEDIUM
- Probability Share    : 41.81%
- Evidence Quality     : HIGH
- Verdict              : PROBABLE_CAUSE_BUT_CONFLICTED
- Summary              : Probable root cause=MACRO_POLICY_PRESSURE; direction=BEARISH; confidence=MEDIUM; share=41.81%. قوی‌ترین evidence از federal_reserve_press است: Market narrative theme: MACRO_POLICY | هشدار: شواهد متضاد همزمان وجود دارد.
- Evidence Total       : 16 | official=12 | event_rows=12

Top Cause Hypotheses:
- MACRO_POLICY_PRESSURE: p=41.81% | score=68.033 | dir=BEARISH | evidence=7 | verdict=SUPPORTING_CAUSE
- REGULATORY_ACCESS_OR_MODERNIZATION: p=13.27% | score=21.59 | dir=BULLISH | evidence=2 | verdict=WEAK_SUPPORTING_CAUSE
- MIXED_EVENT_CONFLICT: p=13.21% | score=21.4923 | dir=MIXED_OR_NEUTRAL | evidence=2 | verdict=WEAK_SUPPORTING_CAUSE
- EXCHANGE_MARKET_ACCESS: p=11.66% | score=18.975 | dir=MIXED_OR_NEUTRAL | evidence=2 | verdict=WEAK_SUPPORTING_CAUSE
- TECHNICAL_STRUCTURE_MOMENTUM: p=11.06% | score=18.0 | dir=BULLISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- REGULATORY_RISK: p=8.98% | score=14.615 | dir=BEARISH | evidence=2 | verdict=WEAK_SUPPORTING_CAUSE

Contradictions:
⚠️ شواهد bullish و bearish همزمان قوی‌اند: bull=39.59, bear=82.65

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
Status                 : ROOT_CAUSE_FORWARD_PROMISING_LOW_SAMPLE
Run ID                 : root_cause_forward_20260711_072653
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 54 / 51
Root Cause Rows        : 3
Evaluated Cells        : 5
Eligible Causes        : 1
Research Candidates    : 0
Promising Low Sample   : 1
Min Samples / Deadzone : 10 / 0.0%

Top Root-Cause Forward Results:
- MACRO_POLICY_PRESSURE | BEARISH | n24=0 hit24=0.0% avg24=0.0% | n12=2 hit12=50.0% | score=5.7613 | FORWARD_PROMISING_LOW_SAMPLE

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
Status                 : ROOT_CAUSE_SAMPLE_COLLECTION_ACTIVE_LOW_SAMPLE
Run ID                 : root_cause_samples_20260711_072653
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 54 / 51
Root Cause Rows        : 3
Evaluated Cells        : 5
Unique Root Causes     : 1
Validation Status      : ROOT_CAUSE_FORWARD_PROMISING_LOW_SAMPLE
Candidates / Promising : 0 / 1
Min/Research/Candidate : 10 / 30 / 90 cells
More decisions needed  : min=2 | research=9 | candidate=29

Root Cause Buckets:
- MACRO_POLICY_PRESSURE | BEARISH | rows=3 cells=5 | n24=0 hit24=0.0% avg24=0.0% | maturity=LOW_SAMPLE_ACCUMULATING | LOW_SAMPLE_KEEP_COLLECTING

Blockers:
⛔ Root Cause evaluated cells کمتر از حداقل است: 5/10

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
Status                 : NO_EVIDENCE_GRAPH_ROWS
Run ID                 : evidence_graph_20260711_072653
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 54 / 51
Graph Rows             : 0
Nodes / Edges / Paths  : 0 / 0 / 0
Graph Maturity         : NO_GRAPH_DATA
Min/Research/Candidate : 10 / 30 / 90 evaluated cells

Blockers:
⛔ هیچ decision_evaluations row با root_cause قابل ساخت گراف پیدا نشد؛ root_cause_dashboard و decision_evaluator را اجرا کن.

Recommendations:
→ چرخه Forward را منظم اجرا کن تا مسیرهای evidence به outcomeهای بیشتری وصل شوند.
→ مسیرهایی که چند هفته متوالی hit-rate و signed-return مثبت دارند بعداً می‌توانند وارد Evidence Weight Review شوند.
→ اگر یک منبع یا روایت در Forward چندبار fail شد، وزن آن باید فقط بعد از sample کافی بازبینی شود.

Warnings:
⚠️ Evidence Graph فقط رابطه‌های پژوهشی بین شواهد، روایت، علت و outcome را می‌سازد؛ سیگنال خرید/فروش نیست.
⚠️ تا وقتی sample کافی وجود نداشته باشد، هیچ وزن evidence نباید برای Paper/Live تغییر کند.
==============================================================================================================

================================================================================================================
⏪ Freakto Market Replay Engine v10.0.0
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
⛔ هیچ ردیف Market Replay ساخته نشد.
================================================================================================================

==============================================================================================================
🧠 Freakto Research Robustness & Intelligence Suite v10.0.0
==============================================================================================================
Status: RESEARCH_SUITE_WITH_BLOCKERS
Run ID: research_suite_20260711_072653

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
- causal_intelligence: CAUSAL_CONTEXT_WITH_BLOCKERS
- market_narrative: MARKET_NARRATIVE_WITH_CONFLICTS
- narrative_decision_conflict: NARRATIVE_DECISION_HIGH_CONFLICT
- root_cause_discovery: ROOT_CAUSE_MIXED_WITH_CONTRADICTIONS
- root_cause_forward_validation: ROOT_CAUSE_FORWARD_PROMISING_LOW_SAMPLE
- root_cause_sample_tracker: ROOT_CAUSE_SAMPLE_COLLECTION_ACTIVE_LOW_SAMPLE
- evidence_graph: NO_EVIDENCE_GRAPH_ROWS
- market_replay: NO_REPLAY_ROWS
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
- FORWARD_REGIME_LABELING_READY | known=55 | unknown=0 | injected=0

Regime Shadow Gate Highlights:
- REGIME_SHADOW_GATES_ACTIVE | regime_gates=4 | signals=0 | eval=16
- REGIME_TRENDING_BEAR__RISK_MEDIUM: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%
- REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%

Forward Shadow Coverage / Bull Probe:
- FORWARD_PROMISING_BACKTEST_CONFLICTS_FOUND | decisions=55 | shadow_signals=20 | eval_shadow=16
- BULL_STRUCTURE_SCORE_GE_10: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=14 | fwd_avg=0.8834% | bt_net=0.0%
- BULL_STRUCTURE_SCORE_GE_10_LONG: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=14 | fwd_avg=0.8834% | bt_net=0.0%
- BULL_VOLUME_SCORE_GE_10: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | bt_net=0.0%
- BULL_RISK_MEDIUM: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | bt_net=0.0%

Causal/Event Intelligence:
- CAUSAL_CONTEXT_WITH_BLOCKERS | sources_ok=13 | trusted_ok=13 | catalyst=44/100 | conflict=HIGH
- primary=MULTI_SOURCE_EVENT_CONSENSUS | verdict=CAUSAL_CONFLICT_RESEARCH_ONLY

Market Narrative Engine:
- MARKET_NARRATIVE_WITH_CONFLICTS | label=MIXED_NARRATIVE_CONFLICT | dir=BEARISH | theme=MACRO_POLICY | score=-20.8077
- accepted=7 | noise_filtered=0 | risk=HIGH | conflict=HIGH

Narrative/Decision Conflict:
- NARRATIVE_DECISION_HIGH_CONFLICT | side=LONG | narrative=BEARISH | alignment=CONFLICTING
- conflict=86/100 | adj=-35 | verdict=HIGH_CONFLICT_WATCHLIST_ONLY

Market Replay v10:
- NO_REPLAY_ROWS | rows=0 | complete=0 | directional=0
- test/research audit=FAILED_NO_REPLAY_ROWS | avg_net24=0.0% | PF=0.0

Root Cause Discovery:
- ROOT_CAUSE_MIXED_WITH_CONTRADICTIONS | primary=MACRO_POLICY_PRESSURE | dir=BEARISH | conf=MEDIUM | p=41.81%
- quality=HIGH | evidence=16 | verdict=PROBABLE_CAUSE_BUT_CONFLICTED

Root Cause Forward Validation:
- ROOT_CAUSE_FORWARD_PROMISING_LOW_SAMPLE | rows=3 | cells=5 | candidates=0 | low_sample=1
- MACRO_POLICY_PRESSURE BEARISH: n24=0 hit24=0.0% avg24=0.0% | FORWARD_PROMISING_LOW_SAMPLE

Strict Readiness:
- STRICT_READINESS_RESEARCH_ONLY | blockers=4
  ⛔ Backtest sample کمتر از 100 است.
  ⛔ Backtest net expectancy از نظر CI95 بالای صفر نیست.
  ⛔ Forward complete samples کمتر از 30 است.
  ⛔ پوشش regime کافی نیست؛ حداقل دو رژیم معتبر لازم است.

Pipeline Health:
- PIPELINE_HEALTHY | alerts=0

Suite Blockers:
⛔ gate_robustness: هیچ دیتای backtest کامل برای robust validation وجود ندارد.
⛔ cost_adjusted_backtest: Backtest data موجود نیست.
⛔ meta_labeling: برای meta-labeling حداقل 120 نمونه لازم است.
⛔ regime_research: Backtest data موجود نیست.
⛔ regime_gate_matrix: هیچ historical_backtest_evaluations کامل برای ساخت Regime-Gate Matrix پیدا نشد.
⛔ regime_shadow_gates: کل نمونه‌های ارزیابی‌شده Shadow کمتر از 30 است: 16
⛔ forward_shadow_coverage: Shadow evaluated samples کمتر از 30 است: 16
⛔ causal_intelligence: Causal conflict بالا است؛ هر استفاده عملی باید downgrade شود و فقط Research بماند.
⛔ root_cause_sample_tracker: Root Cause evaluated cells کمتر از حداقل است: 5/10
⛔ evidence_graph: هیچ decision_evaluations row با root_cause قابل ساخت گراف پیدا نشد؛ root_cause_dashboard و decision_evaluator را اجرا کن.
⛔ market_replay: هیچ ردیف Market Replay ساخته نشد.
⛔ cross_exchange_validation: Backtest data موجود نیست.

Safety: هیچ بخش v6 تا v10 سفارش واقعی ارسال نمی‌کند؛ Market Replay نیز فقط Research/Backtest است.
==============================================================================================================

==============================================================================================================
🚦 Freakto Advanced Live Readiness Score v4.7.1
==============================================================================================================
Created UTC       : 2026-07-11T07:26:53.570458+00:00
Readiness Level   : PAPER_TRADING_PHASE
Readiness Score   : 56/100
Paper Ready       : True
Live Ready        : False
Allowed Risk      : 0.00%
Edge Quality      : EARLY_EDGE_OBSERVED
Regime Verdict    : REGIME_DATA_COLLECTING

Core Stats:
- Complete evaluations: 51
- Closed paper trades: 0
- Paper expectancy: 0.0000R
- Decision Profit Factor: 3.1353
--------------------------------------------------------------------------------------------------------------
Component : Data Sufficiency
Score     : 6/20
Status    : LOW
Note      : Complete evaluations: 51/100
Note      : Closed paper trades: 0/30
Blocker   : Complete evaluations هنوز کافی نیست: 51/100
Blocker   : Closed paper trades هنوز کافی نیست: 0/30
--------------------------------------------------------------------------------------------------------------
Component : Decision Edge
Score     : 20/23
Status    : PARTIAL
Note      : Decision quality: MIXED_VALIDATION
Note      : Directional Win 76.47% | Expectancy 0.7245pct | PF 3.1353
Note      : Stop 45.10% | Sharpe-like 3.3404
Blocker   : Decision sample کمتر از 100 است: 51
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
Note      : Known/Unknown: 51/0
Note      : Best/Worst: TRENDING_BEAR/TRENDING_BULL
Blocker   : هنوز هیچ رژیم با Edge مثبت قابل اتکا مشخص نشده است.
--------------------------------------------------------------------------------------------------------------
Component : Validation Stability
Score     : 12/12
Status    : PASS
Note      : Strategy Lab اجرا شده و نمونه دارد.
Note      : Walk-Forward Validation اجرا شده و test sample دارد.
--------------------------------------------------------------------------------------------------------------
Component : Operational Safety
Score     : 5/7
Status    : PARTIAL
Note      : Auto-live trading در پروژه فعال نیست.
Note      : Readiness Gate قبل از هر تست عملی باید بررسی شود.
Blocker   : Stop Hit Rate بالاست: 45.10%

Warnings:
⚠️ Paper Trading هنوز نتیجه بسته‌شده ندارد.
⚠️ Market Replay v10 باید روی Test split و بعد در Forward تأیید شود؛ این مانع Paper آزمایشی نیست اما Live را مسدود می‌کند.

Hard Blockers:
⛔ Complete evaluations هنوز کافی نیست: 51/100
⛔ Closed paper trades هنوز کافی نیست: 0/30
⛔ Decision sample کمتر از 100 است: 51
⛔ Paper sample کمتر از 30 معامله بسته‌شده است: 0
⛔ Paper expectancy هنوز مثبت نیست.
⛔ هنوز هیچ رژیم با Edge مثبت قابل اتکا مشخص نشده است.
⛔ Stop Hit Rate بالاست: 45.10%
⛔ Market Replay هنوز برای Live معتبر نیست: NO_REPLAY_ROWS (rows=0, audit=FAILED_NO_REPLAY_ROWS)

Conclusion: پروژه در فاز Paper/Forward Test است؛ پول واقعی هنوز مجاز نیست.
==============================================================================================================