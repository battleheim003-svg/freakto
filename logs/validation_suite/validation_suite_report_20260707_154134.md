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
Created UTC      : 2026-07-07T15:41:34.320085+00:00
Combined Quality : EARLY_EDGE_OBSERVED

--------------------------------------------------------------------------------------------------------------
Source       : decision_evaluations
Quality      : MIXED_VALIDATION
Samples      : 36 | Positive/Negative/Flat: 31/5/0
Directional Win Rate: 86.11%
Expectancy   : 1.0317pct
ProfitFactor : 21.7938
Sharpe-like  : 6.3770 | Sortino-like: 22.1860
Max Drawdown : -1.7127pct
Best/Worst   : 3.5622pct / -0.6451pct
Avg Win/Loss : 1.2557pct / -0.3572pct
Stop Rate    : 50.00%
Target Hit   : T1 63.89% | T2 63.89% | T3 30.56%
Definition   : Directional Win = positive evaluated return; Target Hit = target_1_hit.
MFE/MAE Avg  : 3.1721% / -2.0499%
Note         : Expectancy و Directional Win Rate فعلاً مثبت هستند.
Warning      : نمونه هنوز کمتر از 100 است؛ برای تصمیم عملی باید داده بیشتری جمع شود.
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
⛔ Decision COMPLETE کمتر از 100 است: 36
⛔ Paper trades بسته‌شده کمتر از 30 است: 0
==============================================================================================================

==============================================================================================================
🧬 Freakto Regime Performance Matrix v4.7.1
==============================================================================================================
Created UTC          : 2026-07-07T15:41:34.340093+00:00
Overall Verdict      : REGIME_DATA_COLLECTING
Known/Unknown Regime : 5 / 31
Best/Worst Regime    : TRENDING_BULL / UNKNOWN

Warnings:
⚠️ بیشتر نمونه‌ها regime_label ندارند؛ چند اجرای جدید monitor.py بعد از v4.7 لازم است.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : UNKNOWN / LONG / WATCHLIST
Samples            : 20
Target 1 Hit       : 100.00%
Directional Win    : 90.00%
Avg 24h            : 0.6932%
Profit Factor      : 12.0253
Stop Rate          : 85.00%
Avg Score          : 65.35
Verdict            : MIXED_POSITIVE
Note               : Regime در لاگ‌های قدیمی ثبت نشده؛ برای تصمیم‌گیری نیاز به داده v4.7 به بعد است.
Note               : بازده مثبت است اما کیفیت آماری کامل نیست.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : UNKNOWN / NEUTRAL / MONITOR_ONLY
Samples            : 8
Target 1 Hit       : 0.00%
Directional Win    : 75.00%
Avg 24h            : 0.9388%
Profit Factor      : 17.4959
Stop Rate          : 0.00%
Avg Score          : 29.00
Verdict            : MIXED_POSITIVE
Note               : Regime در لاگ‌های قدیمی ثبت نشده؛ برای تصمیم‌گیری نیاز به داده v4.7 به بعد است.
Note               : بازده مثبت است اما کیفیت آماری کامل نیست.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : TRENDING_BULL / NEUTRAL / MONITOR_ONLY
Samples            : 5
Target 1 Hit       : 0.00%
Directional Win    : 80.00%
Avg 24h            : 2.3233%
Profit Factor      : 159.0503
Stop Rate          : 0.00%
Avg Score          : 33.40
Verdict            : MIXED_POSITIVE
Note               : بازده مثبت است اما کیفیت آماری کامل نیست.
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
Created UTC       : 2026-07-07T15:41:34.347258+00:00
Portfolio Status  : MEMORY_BUILDING
Symbols           : 1
Total scans       : 0
Complete evals    : 36
Closed paper      : 0
Best memory symbol: BTC/USDT
Best paper symbol : NONE

Warnings:
⚠️ Closed paper trades کل پورتفو کمتر از 30 است: 0
--------------------------------------------------------------------------------------------------------------
Symbol        : BTC/USDT
Status        : SYMBOL_EDGE_EARLY | Confidence MEDIUM
Scans/Dec/Eval: 0 / 41 / 36
Latest        : UNKNOWN | Rec UNKNOWN | MTF UNKNOWN
Avg Score/Conf/Opp: 0.00 / 0.00% / 0.00
Directional/T1/Avg24: 86.11% / 63.89% / 1.0317%
Paper        : closed 0 | win 0.00% | exp 0.0000R | PF 0.0000
Rec rates    : actionable 0.00% | monitor 0.00% | ignore 0.00%
Note         : Decision edge اولیه برای این نماد مثبت است.
Blocker      : Closed paper trades کمتر از 30 است: 0
==============================================================================================================

==============================================================================================================
🎯 Freakto Confidence Calibration Engine v5.0
==============================================================================================================
Created UTC       : 2026-07-07T15:41:34.356158+00:00
Quality           : CALIBRATION_WEAK
Samples           : 36
Overall Dir Win   : 86.11%
Overall T1 Hit    : 63.89%
Mean Calib Error  : 37.33 pts

Blockers:
⛔ Confidence داخلی با outcome واقعی فاصله زیادی دارد.
⛔ برای استفاده عملی، حداقل 100 ارزیابی لازم است: 36/100
--------------------------------------------------------------------------------------------------------------
Confidence Label Buckets
Low            | n= 15 | Pred  25.0% | Dir  80.00% | T1  13.33% | Gap +55.00 | UNDER_CONFIDENT
Medium         | n= 13 | Pred  55.0% | Dir  84.62% | T1 100.00% | Gap +29.62 | UNDER_CONFIDENT
Medium-High    | n=  8 | Pred  67.5% | Dir 100.00% | T1 100.00% | Gap +32.50 | LOW_SAMPLE
--------------------------------------------------------------------------------------------------------------
Score Buckets
score_10_19    | n=  3 | Pred  14.5% | Dir  66.67% | T1   0.00% | Gap +52.17 | LOW_SAMPLE
score_30_39    | n= 10 | Pred  34.5% | Dir  80.00% | T1   0.00% | Gap +45.50 | UNDER_CONFIDENT
score_50_59    | n=  7 | Pred  54.5% | Dir  85.71% | T1 100.00% | Gap +31.21 | LOW_SAMPLE
score_60_69    | n=  8 | Pred  64.5% | Dir  87.50% | T1 100.00% | Gap +23.00 | LOW_SAMPLE
score_70_79    | n=  8 | Pred  74.5% | Dir 100.00% | T1 100.00% | Gap +25.50 | LOW_SAMPLE
==============================================================================================================

==============================================================================================================
🎲 Freakto Monte Carlo Risk Lab v5.0
==============================================================================================================
Created UTC      : 2026-07-07T15:41:34.395865+00:00
Risk Quality     : RISK_PROFILE_ACCEPTABLE
Source           : decision_evaluations_fallback (pct)
Samples          : 36
Iterations       : 2000
Trades / Run     : 100
Expected / Trade : 1.0317pct
Best / Worst Samp: 3.5622pct / -0.6451pct
--------------------------------------------------------------------------------------------------------------
Median Final     : 103.2716pct
Mean Final       : 103.3233pct
P05 / P95 Final  : 87.7627pct / 118.3829pct
Median Max DD    : -0.7696pct
P95 Max DD       : -1.4048pct
Prob Loss        : 0.00%
Prob Ruin        : 0.00% | Threshold -10.00pct

Notes:
✓ Median path مثبت و Probability of ruin پایین است.

Warnings:
⚠️ Paper Trade کافی نبود؛ شبیه‌سازی با decision returns درصدی انجام شد، نه R واقعی.
==============================================================================================================

==============================================================================================================
🧭 Freakto Forward Test Status v5.3.3
==============================================================================================================
Status          : FORWARD_TEST_COLLECTING
Progress Score  : 17/100
Readiness Level : RESEARCH_ONLY
Paper Ready     : False
Live Ready      : False

Data Progress:
- Complete evaluations : 36/100
- Closed paper trades  : 0/30
- Open paper trades    : 0
- Total paper trades   : 0
- Regime-labeled       : 0/30
- Unknown regime       : 36
- Symbols evaluated    : 1
- Symbols scanned      : 0
- Forward runs         : 10/12 successful
- Forward days         : 3/30
- First run UTC        : 2026-07-05T17:39:28.376869+00:00
- Last run UTC         : 2026-07-07T15:40:42.092544+00:00

Blockers:
⛔ Complete evaluations کمتر از 100 است: 36
⛔ Closed paper trades کمتر از 30 است: 0
⛔ Regime-labeled samples کمتر از 30 است: 0
⛔ روزهای Forward Test کمتر از 30 است: 3

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
Run ID                 : backtest_diag_20260707_154134
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
Run ID                 : gate_sim_20260707_154134
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
🧪 Freakto Candidate Gate Shadow Validator v5.3.3
==============================================================================================================
Status                 : SHADOW_COLLECTING_FORWARD_DATA
Run ID                 : shadow_gate_20260707_154134
Horizon                : 24h
Min Samples            : 30
Decisions              : 41
Directional Decisions  : 27
Gates Tracked          : 7
Shadow Signals         : 16
Evaluated Shadow       : 14
Pending Shadow         : 2
Confirmed Candidates   : 0
Building Candidates    : 7
Rejected Candidates    : 0

Gate Shadow Metrics:
- STRUCTURE_SCORE_GE_10 [SHADOW_BUILDING]: signals=14 | eval=14 | pending=0 | avg=0.8834% | win=100.0% | T1=100.0% | Stop=85.71% | MFE/MAE=1.785 | warn=Forward evaluated samples کمتر از حداقل 30 است: 14
- VOLUME_SCORE_GE_10 [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- RISK_MEDIUM [SHADOW_BUILDING]: signals=0 | eval=0 | pending=0 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=هنوز هیچ تصمیم Forward این gate را پاس نکرده است.
- HISTORICAL_EDGE_SCORE_GE_1 [SHADOW_BUILDING]: signals=2 | eval=0 | pending=2 | avg=0.0% | win=0.0% | T1=0.0% | Stop=0.0% | MFE/MAE=0.0 | warn=Forward evaluated samples کمتر از حداقل 30 است: 0
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
🧠 Freakto Research Robustness & Intelligence Suite v6.0.0
==============================================================================================================
Status: RESEARCH_SUITE_WITH_BLOCKERS
Run ID: research_suite_20260707_154134

Sections:
- gate_robustness: NO_BACKTEST_DATA
- cost_adjusted_backtest: NO_BACKTEST_DATA
- meta_labeling: LOW_SAMPLE_META_LABELING
- ensemble_explainability: EXPLAINABILITY_READY
- data_enrichment: ENRICHMENT_CONNECTORS_PRESENT
- regime_research: NO_BACKTEST_DATA
- cross_exchange_validation: NO_BACKTEST_DATA
- research_db: RESEARCH_DB_READY
- pipeline_health: PIPELINE_HEALTHY
- strict_readiness: STRICT_READINESS_RESEARCH_ONLY
- position_sizing_lab: NO_BACKTEST_DATA
- airdrop_shadow_research: AIRDROP_SHADOW_READY
- static_dashboard: STATIC_DASHBOARD_READY

Gate Robustness Highlights:

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
⛔ cross_exchange_validation: Backtest data موجود نیست.
⛔ strict_readiness: Backtest sample کمتر از 100 است.
⛔ strict_readiness: Backtest net expectancy از نظر CI95 بالای صفر نیست.
⛔ strict_readiness: Forward complete samples کمتر از 30 است.
⛔ strict_readiness: پوشش regime کافی نیست؛ حداقل دو رژیم معتبر لازم است.

Safety: هیچ بخش v6 سفارش واقعی ارسال نمی‌کند و Paper Trade جدید ایجاد نمی‌کند.
==============================================================================================================

==============================================================================================================
🚦 Freakto Advanced Live Readiness Score v4.7.1
==============================================================================================================
Created UTC       : 2026-07-07T15:41:34.547271+00:00
Readiness Level   : RESEARCH_ONLY
Readiness Score   : 47/100
Paper Ready       : False
Live Ready        : False
Allowed Risk      : 0.00%
Edge Quality      : EARLY_EDGE_OBSERVED
Regime Verdict    : REGIME_DATA_COLLECTING

Core Stats:
- Complete evaluations: 36
- Closed paper trades: 0
- Paper expectancy: 0.0000R
- Decision Profit Factor: 21.7938
--------------------------------------------------------------------------------------------------------------
Component : Data Sufficiency
Score     : 4/20
Status    : LOW
Note      : Complete evaluations: 36/100
Note      : Closed paper trades: 0/30
Blocker   : Complete evaluations هنوز کافی نیست: 36/100
Blocker   : Closed paper trades هنوز کافی نیست: 0/30
--------------------------------------------------------------------------------------------------------------
Component : Decision Edge
Score     : 20/23
Status    : PARTIAL
Note      : Decision quality: MIXED_VALIDATION
Note      : Directional Win 86.11% | Expectancy 1.0317pct | PF 21.7938
Note      : Stop 50.00% | Sharpe-like 6.3770
Blocker   : Decision sample کمتر از 100 است: 36
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
Score     : 6/18
Status    : PARTIAL
Note      : Regime verdict: REGIME_DATA_COLLECTING
Note      : Known/Unknown: 5/31
Note      : Best/Worst: TRENDING_BULL/UNKNOWN
Blocker   : Regime-labeled samples کمتر از 30 است: 5
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
Blocker   : Stop Hit Rate بالاست: 50.00%

Warnings:
⚠️ Paper Trading هنوز نتیجه بسته‌شده ندارد.
⚠️ Regime Matrix برای لاگ‌های قدیمی هنوز UNKNOWN زیادی دارد؛ چند روز داده جدید لازم است.

Hard Blockers:
⛔ Complete evaluations هنوز کافی نیست: 36/100
⛔ Closed paper trades هنوز کافی نیست: 0/30
⛔ Decision sample کمتر از 100 است: 36
⛔ Paper sample کمتر از 30 معامله بسته‌شده است: 0
⛔ Paper expectancy هنوز مثبت نیست.
⛔ Regime-labeled samples کمتر از 30 است: 5
⛔ هنوز هیچ رژیم با Edge مثبت قابل اتکا مشخص نشده است.
⛔ Stop Hit Rate بالاست: 50.00%

Conclusion: پروژه هنوز در Research/Observation است؛ داده و Paper Trade بیشتری لازم است.
==============================================================================================================