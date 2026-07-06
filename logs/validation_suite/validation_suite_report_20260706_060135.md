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
Created UTC      : 2026-07-06T06:01:35.736322+00:00
Combined Quality : EARLY_EDGE_OBSERVED

--------------------------------------------------------------------------------------------------------------
Source       : decision_evaluations
Quality      : EARLY_POSITIVE_LOW_SAMPLE
Samples      : 21 | Positive/Negative/Flat: 21/0/0
Directional Win Rate: 100.00%
Expectancy   : 0.9396pct
ProfitFactor : 19.7323
Sharpe-like  : 8.1386 | Sortino-like: 0.0000
Max Drawdown : 0.0000pct
Best/Worst   : 1.8657pct / 0.1956pct
Avg Win/Loss : 0.9396pct / 0.0000pct
Stop Rate    : 0.00%
Target Hit   : T1 100.00% | T2 33.33% | T3 0.00%
Definition   : Directional Win = positive evaluated return; Target Hit = target_1_hit.
MFE/MAE Avg  : 2.2430% / -0.4316%
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
⛔ Decision COMPLETE کمتر از 100 است: 21
⛔ Paper trades بسته‌شده کمتر از 30 است: 0
==============================================================================================================

==============================================================================================================
🧬 Freakto Regime Performance Matrix v4.7.1
==============================================================================================================
Created UTC          : 2026-07-06T06:01:35.762273+00:00
Overall Verdict      : REGIME_DATA_MISSING
Known/Unknown Regime : 0 / 21
Best/Worst Regime    : UNKNOWN / UNKNOWN

Warnings:
⚠️ بیشتر نمونه‌ها regime_label ندارند؛ چند اجرای جدید monitor.py بعد از v4.7 لازم است.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : UNKNOWN / LONG / WATCHLIST
Samples            : 18
Target 1 Hit       : 100.00%
Directional Win    : 100.00%
Avg 24h            : 0.8616%
Profit Factor      : 15.5083
Stop Rate          : 0.00%
Avg Score          : 65.83
Verdict            : REGIME_POSITIVE
Note               : Regime در لاگ‌های قدیمی ثبت نشده؛ برای تصمیم‌گیری نیاز به داده v4.7 به بعد است.
Note               : در این رژیم نشانه اولیه Edge مثبت دیده می‌شود.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : UNKNOWN / LONG / NOT_ACTIONABLE
Samples            : 2
Target 1 Hit       : 100.00%
Directional Win    : 100.00%
Avg 24h            : 1.8619%
Profit Factor      : 3.7238
Stop Rate          : 0.00%
Avg Score          : 53.00
Verdict            : LOW_SAMPLE
Note               : نمونه کمتر از 5 است؛ فقط برای رصد.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : UNKNOWN / LONG / ACTIONABLE
Samples            : 1
Target 1 Hit       : 100.00%
Directional Win    : 100.00%
Avg 24h            : 0.5002%
Profit Factor      : 0.5002
Stop Rate          : 0.00%
Avg Score          : 70.00
Verdict            : LOW_SAMPLE
Note               : نمونه کمتر از 5 است؛ فقط برای رصد.
==============================================================================================================

==============================================================================================================
🧠 Freakto Portfolio Memory Engine v5.0
==============================================================================================================
Created UTC       : 2026-07-06T06:01:35.771524+00:00
Portfolio Status  : MEMORY_BUILDING
Symbols           : 1
Total scans       : 0
Complete evals    : 21
Closed paper      : 0
Best memory symbol: BTC/USDT
Best paper symbol : NONE

Warnings:
⚠️ Closed paper trades کل پورتفو کمتر از 30 است: 0
--------------------------------------------------------------------------------------------------------------
Symbol        : BTC/USDT
Status        : OBSERVATION_ONLY | Confidence LOW_MEDIUM
Scans/Dec/Eval: 0 / 33 / 21
Latest        : UNKNOWN | Rec UNKNOWN | MTF UNKNOWN
Avg Score/Conf/Opp: 0.00 / 0.00% / 0.00
Directional/T1/Avg24: 100.00% / 100.00% / 0.9396%
Paper        : closed 0 | win 0.00% | exp 0.0000R | PF 0.0000
Rec rates    : actionable 0.00% | monitor 0.00% | ignore 0.00%
Note         : حافظه نماد فعلاً فقط مشاهده‌ای است.
Blocker      : Complete evaluations کمتر از 30 است: 21
Blocker      : Closed paper trades کمتر از 30 است: 0
==============================================================================================================

==============================================================================================================
🎯 Freakto Confidence Calibration Engine v5.0
==============================================================================================================
Created UTC       : 2026-07-06T06:01:35.780495+00:00
Quality           : LOW_SAMPLE_CALIBRATION
Samples           : 21
Overall Dir Win   : 100.00%
Overall T1 Hit    : 100.00%
Mean Calib Error  : 38.82 pts

Warnings:
⚠️ Calibration sample کمتر از 30 است: 21

Blockers:
⛔ برای استفاده عملی، حداقل 100 ارزیابی لازم است: 21/100
--------------------------------------------------------------------------------------------------------------
Confidence Label Buckets
Low            | n=  2 | Pred  25.0% | Dir 100.00% | T1 100.00% | Gap +75.00 | LOW_SAMPLE
Medium         | n= 11 | Pred  55.0% | Dir 100.00% | T1 100.00% | Gap +45.00 | UNDER_CONFIDENT
Medium-High    | n=  8 | Pred  67.5% | Dir 100.00% | T1 100.00% | Gap +32.50 | LOW_SAMPLE
--------------------------------------------------------------------------------------------------------------
Score Buckets
score_50_59    | n=  6 | Pred  54.5% | Dir 100.00% | T1 100.00% | Gap +45.50 | LOW_SAMPLE
score_60_69    | n=  7 | Pred  64.5% | Dir 100.00% | T1 100.00% | Gap +35.50 | LOW_SAMPLE
score_70_79    | n=  8 | Pred  74.5% | Dir 100.00% | T1 100.00% | Gap +25.50 | LOW_SAMPLE
==============================================================================================================

==============================================================================================================
🎲 Freakto Monte Carlo Risk Lab v5.0
==============================================================================================================
Created UTC      : 2026-07-06T06:01:35.820343+00:00
Risk Quality     : LOW_SAMPLE_RISK_MODEL
Source           : decision_evaluations_fallback (pct)
Samples          : 21
Iterations       : 2000
Trades / Run     : 100
Expected / Trade : 0.9396pct
Best / Worst Samp: 1.8657pct / 0.1956pct
--------------------------------------------------------------------------------------------------------------
Median Final     : 93.7160pct
Mean Final       : 93.8310pct
P05 / P95 Final  : 85.7006pct / 102.3231pct
Median Max DD    : 0.0000pct
P95 Max DD       : 0.0000pct
Prob Loss        : 0.00%
Prob Ruin        : 0.00% | Threshold -10.00pct

Warnings:
⚠️ نمونه Monte Carlo کمتر از 30 است: 21
⚠️ Paper Trade کافی نبود؛ شبیه‌سازی با decision returns درصدی انجام شد، نه R واقعی.
==============================================================================================================

==============================================================================================================
🧭 Freakto Forward Test Status v5.1.2
==============================================================================================================
Status          : FORWARD_TEST_COLLECTING
Progress Score  : 7/100
Readiness Level : RESEARCH_ONLY
Paper Ready     : False
Live Ready      : False

Data Progress:
- Complete evaluations : 21/100
- Closed paper trades  : 0/30
- Open paper trades    : 0
- Total paper trades   : 0
- Regime-labeled       : 0/30
- Unknown regime       : 21
- Symbols evaluated    : 1
- Symbols scanned      : 0
- Forward runs         : 2/4 successful
- Forward days         : 2/30
- First run UTC        : 2026-07-05T17:39:28.376869+00:00
- Last run UTC         : 2026-07-06T06:00:44.850869+00:00

Blockers:
⛔ Complete evaluations کمتر از 100 است: 21
⛔ Closed paper trades کمتر از 30 است: 0
⛔ Regime-labeled samples کمتر از 30 است: 0
⛔ روزهای Forward Test کمتر از 30 است: 2

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
🚦 Freakto Advanced Live Readiness Score v4.7.1
==============================================================================================================
Created UTC       : 2026-07-06T06:01:35.856795+00:00
Readiness Level   : RESEARCH_ONLY
Readiness Score   : 50/100
Paper Ready       : False
Live Ready        : False
Allowed Risk      : 0.00%
Edge Quality      : EARLY_EDGE_OBSERVED
Regime Verdict    : REGIME_DATA_MISSING

Core Stats:
- Complete evaluations: 21
- Closed paper trades: 0
- Paper expectancy: 0.0000R
- Decision Profit Factor: 19.7323
--------------------------------------------------------------------------------------------------------------
Component : Data Sufficiency
Score     : 3/20
Status    : LOW
Note      : Complete evaluations: 21/100
Note      : Closed paper trades: 0/30
Blocker   : Complete evaluations هنوز کافی نیست: 21/100
Blocker   : Closed paper trades هنوز کافی نیست: 0/30
--------------------------------------------------------------------------------------------------------------
Component : Decision Edge
Score     : 23/23
Status    : PARTIAL
Note      : Decision quality: EARLY_POSITIVE_LOW_SAMPLE
Note      : Directional Win 100.00% | Expectancy 0.9396pct | PF 19.7323
Note      : Stop 0.00% | Sharpe-like 8.1386
Blocker   : Decision sample کمتر از 100 است: 21
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
Note      : Known/Unknown: 0/21
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
⛔ Complete evaluations هنوز کافی نیست: 21/100
⛔ Closed paper trades هنوز کافی نیست: 0/30
⛔ Decision sample کمتر از 100 است: 21
⛔ Paper sample کمتر از 30 معامله بسته‌شده است: 0
⛔ Paper expectancy هنوز مثبت نیست.
⛔ Regime-labeled samples کمتر از 30 است: 0

Conclusion: پروژه هنوز در Research/Observation است؛ داده و Paper Trade بیشتری لازم است.
==============================================================================================================