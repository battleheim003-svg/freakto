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
Created UTC      : 2026-07-09T21:09:23.573214+00:00
Combined Quality : EARLY_EDGE_OBSERVED

--------------------------------------------------------------------------------------------------------------
Source       : decision_evaluations
Quality      : MIXED_VALIDATION
Samples      : 45 | Positive/Negative/Flat: 34/11/0
Directional Win Rate: 75.56%
Expectancy   : 0.6413pct
ProfitFactor : 2.9964
Sharpe-like  : 2.9344 | Sortino-like: 3.9355
Max Drawdown : -12.6696pct
Best/Worst   : 3.8877pct / -3.2625pct
Avg Win/Loss : 1.2740pct / -1.3142pct
Stop Rate    : 48.89%
Target Hit   : T1 53.33% | T2 51.11% | T3 24.44%
Definition   : Directional Win = positive evaluated return; Target Hit = target_1_hit.
MFE/MAE Avg  : 2.7336% / -2.3426%
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
⛔ Decision COMPLETE کمتر از 100 است: 45
⛔ Paper trades بسته‌شده کمتر از 30 است: 0
==============================================================================================================

==============================================================================================================
🧬 Freakto Regime Performance Matrix v4.7.1
==============================================================================================================
Created UTC          : 2026-07-09T21:09:23.600097+00:00
Overall Verdict      : REGIME_DATA_COLLECTING
Known/Unknown Regime : 45 / 0
Best/Worst Regime    : TRENDING_BULL / TRENDING_BULL
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : TRENDING_BULL / LONG / WATCHLIST
Samples            : 22
Target 1 Hit       : 90.91%
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
Regime/Side/Action : TRENDING_BULL / LONG / NOT_ACTIONABLE
Samples            : 4
Target 1 Hit       : 75.00%
Directional Win    : 75.00%
Avg 24h            : 0.3038%
Profit Factor      : 1.4278
Stop Rate          : 50.00%
Avg Score          : 51.00
Verdict            : LOW_SAMPLE
Note               : نمونه کمتر از 5 است؛ فقط برای رصد.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : TRENDING_BEAR / NEUTRAL / MONITOR_ONLY
Samples            : 2
Target 1 Hit       : 0.00%
Directional Win    : 100.00%
Avg 24h            : 1.5098%
Profit Factor      : 3.0197
Stop Rate          : 0.00%
Avg Score          : 38.00
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
==============================================================================================================

==============================================================================================================
🧠 Freakto Portfolio Memory Engine v5.0
==============================================================================================================
Created UTC       : 2026-07-09T21:09:23.611498+00:00
Portfolio Status  : MEMORY_BUILDING
Symbols           : 1
Total scans       : 0
Complete evals    : 45
Closed paper      : 0
Best memory symbol: BTC/USDT
Best paper symbol : NONE

Warnings:
⚠️ Closed paper trades کل پورتفو کمتر از 30 است: 0
--------------------------------------------------------------------------------------------------------------
Symbol        : BTC/USDT
Status        : SYMBOL_EDGE_EARLY | Confidence MEDIUM
Scans/Dec/Eval: 0 / 51 / 45
Latest        : UNKNOWN | Rec UNKNOWN | MTF UNKNOWN
Avg Score/Conf/Opp: 0.00 / 0.00% / 0.00
Directional/T1/Avg24: 75.56% / 53.33% / 0.6413%
Paper        : closed 0 | win 0.00% | exp 0.0000R | PF 0.0000
Rec rates    : actionable 0.00% | monitor 0.00% | ignore 0.00%
Note         : Decision edge اولیه برای این نماد مثبت است.
Blocker      : Closed paper trades کمتر از 30 است: 0
==============================================================================================================

==============================================================================================================
🎯 Freakto Confidence Calibration Engine v5.0
==============================================================================================================
Created UTC       : 2026-07-09T21:09:23.624778+00:00
Quality           : CALIBRATION_WEAK
Samples           : 45
Overall Dir Win   : 75.56%
Overall T1 Hit    : 53.33%
Mean Calib Error  : 29.57 pts

Blockers:
⛔ Confidence داخلی با outcome واقعی فاصله زیادی دارد.
⛔ برای استفاده عملی، حداقل 100 ارزیابی لازم است: 45/100
--------------------------------------------------------------------------------------------------------------
Confidence Label Buckets
Low            | n= 22 | Pred  25.0% | Dir  68.18% | T1  13.64% | Gap +43.18 | UNDER_CONFIDENT
Medium         | n= 15 | Pred  55.0% | Dir  73.33% | T1  86.67% | Gap +18.33 | UNDER_CONFIDENT
Medium-High    | n=  8 | Pred  67.5% | Dir 100.00% | T1 100.00% | Gap +32.50 | LOW_SAMPLE
--------------------------------------------------------------------------------------------------------------
Score Buckets
score_10_19    | n=  3 | Pred  14.5% | Dir  66.67% | T1   0.00% | Gap +52.17 | LOW_SAMPLE
score_20_29    | n=  1 | Pred  24.5% | Dir   0.00% | T1   0.00% | Gap -24.50 | LOW_SAMPLE
score_30_39    | n= 13 | Pred  34.5% | Dir  69.23% | T1   0.00% | Gap +34.73 | UNDER_CONFIDENT
score_40_49    | n=  3 | Pred  44.5% | Dir  66.67% | T1  33.33% | Gap +22.17 | LOW_SAMPLE
score_50_59    | n=  7 | Pred  54.5% | Dir  85.71% | T1 100.00% | Gap +31.21 | LOW_SAMPLE
score_60_69    | n= 10 | Pred  64.5% | Dir  70.00% | T1  80.00% | Gap  +5.50 | WELL_CALIBRATED_DIRECTIONAL
score_70_79    | n=  8 | Pred  74.5% | Dir 100.00% | T1 100.00% | Gap +25.50 | LOW_SAMPLE
==============================================================================================================

==============================================================================================================
🎲 Freakto Monte Carlo Risk Lab v5.0
==============================================================================================================
Created UTC      : 2026-07-09T21:09:23.672598+00:00
Risk Quality     : RISK_PROFILE_ACCEPTABLE
Source           : decision_evaluations_fallback (pct)
Samples          : 45
Iterations       : 2000
Trades / Run     : 100
Expected / Trade : 0.6413pct
Best / Worst Samp: 3.8877pct / -3.2625pct
--------------------------------------------------------------------------------------------------------------
Median Final     : 64.5272pct
Mean Final       : 64.5812pct
P05 / P95 Final  : 39.7216pct / 88.7231pct
Median Max DD    : -5.6796pct
P95 Max DD       : -9.9910pct
Prob Loss        : 0.00%
Prob Ruin        : 5.00% | Threshold -10.00pct

Notes:
✓ Median path مثبت و Probability of ruin پایین است.

Warnings:
⚠️ Paper Trade کافی نبود؛ شبیه‌سازی با decision returns درصدی انجام شد، نه R واقعی.
==============================================================================================================

==============================================================================================================
🧭 Freakto Forward Test Status v7.1.0
==============================================================================================================
Status          : FORWARD_TEST_COLLECTING
Progress Score  : 48/100
Readiness Level : RESEARCH_ONLY
Paper Ready     : False
Live Ready      : False

Data Progress:
- Complete evaluations : 45/100
- Closed paper trades  : 0/30
- Open paper trades    : 0
- Total paper trades   : 0
- Regime-labeled       : 45/30
- Unknown regime       : 0
- Symbols evaluated    : 1
- Symbols scanned      : 0
- Forward runs         : 20/22 successful
- Forward days         : 5/30
- First run UTC        : 2026-07-05T17:39:28.376869+00:00
- Last run UTC         : 2026-07-09T21:08:22.686632+00:00

Notes:
✓ Regime-labeled samples برای تحلیل اولیه کافی است.

Blockers:
⛔ Complete evaluations کمتر از 100 است: 45
⛔ Closed paper trades کمتر از 30 است: 0
⛔ روزهای Forward Test کمتر از 30 است: 5

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
Run ID                 : backtest_diag_20260709_210923
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
Run ID                 : gate_sim_20260709_210923
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
Run ID                 : forward_regime_label_20260709_210923
Apply Changes          : False
Decision Rows          : 51
Known Before / After   : 51 / 51
Unknown Before / After : 0 / 0
Injected Decision Rows : 0
Preserved Direct Rows  : 51
Direct/Text/Proxy      : 18 / 33 / 0
Evaluation Rows        : 50
Patched Evaluations    : 0
Eval Known After       : 50

Decision Regime Counts:
- TRENDING_BULL: 43
- TRENDING_BEAR: 8

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
Run ID                 : shadow_gate_20260709_210923
Horizon                : 24h
Min Samples            : 30
Decisions              : 51
Directional Decisions  : 28
Gates Tracked          : 11
Shadow Signals         : 16
Evaluated Shadow       : 16
Pending Shadow         : 0
Confirmed Candidates   : 0
Building Candidates    : 11
Rejected Candidates    : 0

Gate Shadow Metrics:
- STRUCTURE_SCORE_GE_10 [SHADOW_BUILDING]: signals=14 | eval=14 | pending=0 | avg=0.8834% | win=100.0% | T1=100.0% | Stop=85.71% | MFE/MAE=1.785 | warn=Forward evaluated samples کمتر از حداقل 30 است: 14
- HISTORICAL_EDGE_SCORE_GE_1 [SHADOW_BUILDING]: signals=2 | eval=2 | pending=0 | avg=-3.0511% | win=0.0% | T1=0.0% | Stop=100.0% | MFE/MAE=0.127 | warn=Forward evaluated samples کمتر از حداقل 30 است: 2
- REGIME_TRENDING_BEAR__RISK_MEDIUM [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10 [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- VOLUME_SCORE_GE_10 [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- RISK_MEDIUM [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.

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
Run ID: regime_gate_matrix_20260709_210923
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
Run ID                 : forward_shadow_coverage_20260709_210923
Horizon                : 24h
Decision Rows          : 51
Directional Decisions  : 28
Evaluation Rows        : 50
Complete Evaluations   : 16
Shadow Signals         : 16
Evaluated Shadow       : 16

Forward Regime Coverage:
- TRENDING_BULL: rows=43 | directional=27 | share=84.31% | direct=0 | proxy/text=0
- TRENDING_BEAR: rows=8 | directional=1 | share=15.69% | direct=0 | proxy/text=0

Shadow Gate Coverage:
- STRUCTURE_SCORE_GE_10: signals=14 | eval=14 | avg=0.8834% | win=100.0% | dominant_regime=TRENDING_BULL
- HISTORICAL_EDGE_SCORE_GE_1: signals=2 | eval=2 | avg=-3.0511% | win=0.0% | dominant_regime=TRENDING_BULL

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
🧠 Freakto Research Robustness & Intelligence Suite v7.1.0
==============================================================================================================
Status: RESEARCH_SUITE_WITH_BLOCKERS
Run ID: research_suite_20260709_210924

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
- causal_intelligence: CAUSAL_CONTEXT_INTERNAL_ONLY
- market_narrative: MARKET_NARRATIVE_WITH_CONFLICTS
- narrative_decision_conflict: NARRATIVE_CONTEXT_ONLY
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
- FORWARD_REGIME_LABELING_READY | known=51 | unknown=0 | injected=0

Regime Shadow Gate Highlights:
- REGIME_SHADOW_GATES_ACTIVE | regime_gates=4 | signals=0 | eval=16
- REGIME_TRENDING_BEAR__RISK_MEDIUM: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%
- REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%

Forward Shadow Coverage / Bull Probe:
- FORWARD_PROMISING_BACKTEST_CONFLICTS_FOUND | decisions=51 | shadow_signals=16 | eval_shadow=16
- BULL_STRUCTURE_SCORE_GE_10: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=14 | fwd_avg=0.8834% | bt_net=0.0%
- BULL_STRUCTURE_SCORE_GE_10_LONG: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=14 | fwd_avg=0.8834% | bt_net=0.0%
- BULL_VOLUME_SCORE_GE_10: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | bt_net=0.0%
- BULL_RISK_MEDIUM: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | bt_net=0.0%

Causal/Event Intelligence:
- CAUSAL_CONTEXT_INTERNAL_ONLY | sources_ok=12 | trusted_ok=12 | catalyst=14/100 | conflict=LOW
- primary=MULTI_SOURCE_EVENT_CONSENSUS | verdict=CAUSAL_CONTEXT_WEAK_OR_RISKY

Market Narrative Engine:
- MARKET_NARRATIVE_WITH_CONFLICTS | label=MIXED_NARRATIVE_CONFLICT | dir=BEARISH | theme=MACRO_POLICY | score=-25.5197
- accepted=7 | noise_filtered=0 | risk=HIGH | conflict=LOW

Narrative/Decision Conflict:
- NARRATIVE_CONTEXT_ONLY | side=NEUTRAL | narrative=BEARISH | alignment=CONTEXT_ONLY
- conflict=62/100 | adj=-12 | verdict=NEUTRAL_DECISION_CONTEXT_ONLY

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
⛔ cross_exchange_validation: Backtest data موجود نیست.
⛔ strict_readiness: Backtest sample کمتر از 100 است.
⛔ strict_readiness: Backtest net expectancy از نظر CI95 بالای صفر نیست.
⛔ strict_readiness: Forward complete samples کمتر از 30 است.
⛔ strict_readiness: پوشش regime کافی نیست؛ حداقل دو رژیم معتبر لازم است.

Safety: هیچ بخش v6/v7 سفارش واقعی ارسال نمی‌کند و Paper Trade جدید ایجاد نمی‌کند.
==============================================================================================================

==============================================================================================================
🚦 Freakto Advanced Live Readiness Score v4.7.1
==============================================================================================================
Created UTC       : 2026-07-09T21:09:24.199635+00:00
Readiness Level   : PAPER_TRADING_PHASE
Readiness Score   : 55/100
Paper Ready       : True
Live Ready        : False
Allowed Risk      : 0.00%
Edge Quality      : EARLY_EDGE_OBSERVED
Regime Verdict    : REGIME_DATA_COLLECTING

Core Stats:
- Complete evaluations: 45
- Closed paper trades: 0
- Paper expectancy: 0.0000R
- Decision Profit Factor: 2.9964
--------------------------------------------------------------------------------------------------------------
Component : Data Sufficiency
Score     : 5/20
Status    : LOW
Note      : Complete evaluations: 45/100
Note      : Closed paper trades: 0/30
Blocker   : Complete evaluations هنوز کافی نیست: 45/100
Blocker   : Closed paper trades هنوز کافی نیست: 0/30
--------------------------------------------------------------------------------------------------------------
Component : Decision Edge
Score     : 20/23
Status    : PARTIAL
Note      : Decision quality: MIXED_VALIDATION
Note      : Directional Win 75.56% | Expectancy 0.6413pct | PF 2.9964
Note      : Stop 48.89% | Sharpe-like 2.9344
Blocker   : Decision sample کمتر از 100 است: 45
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
Note      : Known/Unknown: 45/0
Note      : Best/Worst: TRENDING_BULL/TRENDING_BULL
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
Blocker   : Stop Hit Rate بالاست: 48.89%

Warnings:
⚠️ Paper Trading هنوز نتیجه بسته‌شده ندارد.

Hard Blockers:
⛔ Complete evaluations هنوز کافی نیست: 45/100
⛔ Closed paper trades هنوز کافی نیست: 0/30
⛔ Decision sample کمتر از 100 است: 45
⛔ Paper sample کمتر از 30 معامله بسته‌شده است: 0
⛔ Paper expectancy هنوز مثبت نیست.
⛔ هنوز هیچ رژیم با Edge مثبت قابل اتکا مشخص نشده است.
⛔ Stop Hit Rate بالاست: 48.89%

Conclusion: پروژه در فاز Paper/Forward Test است؛ پول واقعی هنوز مجاز نیست.
==============================================================================================================