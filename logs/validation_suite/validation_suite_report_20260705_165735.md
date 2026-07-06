==============================================================================================================
📐 Freakto Edge Validation Engine v4.7
==============================================================================================================
Created UTC      : 2026-07-05T16:57:35.572097+00:00
Combined Quality : EARLY_EDGE_OBSERVED

--------------------------------------------------------------------------------------------------------------
Source       : decision_evaluations
Quality      : EARLY_POSITIVE_LOW_SAMPLE
Samples      : 17 | Wins 17 | Losses 0 | Flat 0
Win Rate     : 100.00%
Expectancy   : 1.0470pct
ProfitFactor : 17.7989
Sharpe-like  : 8.6425 | Sortino-like: 0.0000
Max Drawdown : 0.0000pct
Best/Worst   : 1.8346pct / 0.4897pct
Avg Win/Loss : 1.0470pct / 0.0000pct
Stop Rate    : 0.00%
T1/T2/T3 Hit : 64.71% / 0.00% / 0.00%
MFE/MAE Avg  : 1.5843% / -0.2997%
Note         : Expectancy و Win Rate فعلاً مثبت هستند.
Warning      : نمونه کمتر از 30 است؛ نتیجه فقط سیگنال اولیه است.
--------------------------------------------------------------------------------------------------------------
Source       : paper_trade_evaluations
Quality      : NO_DATA
Samples      : 0 | Wins 0 | Losses 0 | Flat 0
Win Rate     : 0.00%
Expectancy   : 0.0000R
ProfitFactor : 0.0000
Sharpe-like  : 0.0000 | Sortino-like: 0.0000
Max Drawdown : 0.0000R
Best/Worst   : 0.0000R / 0.0000R
Avg Win/Loss : 0.0000R / 0.0000R
Stop Rate    : 0.00%
Warning      : هنوز Paper Trade ارزیابی‌شده وجود ندارد.

Overall Notes:
✓ Decision edge فعلاً مثبت است، اما تا رسیدن به نمونه کافی فقط تحقیقاتی محسوب می‌شود.
✓ Paper edge هنوز شروع نشده یا معامله بسته‌شده ندارد.

Validation Blockers:
⛔ Decision COMPLETE کمتر از 100 است: 17
⛔ Paper trades بسته‌شده کمتر از 30 است: 0
==============================================================================================================

==============================================================================================================
🧬 Freakto Regime Performance Matrix v4.7
==============================================================================================================
Created UTC          : 2026-07-05T16:57:35.590074+00:00
Overall Verdict      : REGIME_DATA_MISSING
Known/Unknown Regime : 0 / 17
Best/Worst Regime    : UNKNOWN / UNKNOWN

Warnings:
⚠️ بیشتر نمونه‌ها regime_label ندارند؛ چند اجرای جدید monitor.py بعد از v4.7 لازم است.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : UNKNOWN / LONG / WATCHLIST
Samples            : 14
Win Rate           : 64.29%
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
Win Rate           : 100.00%
Avg 24h            : 1.8308%
Profit Factor      : 3.6617
Stop Rate          : 0.00%
Avg Score          : 53.00
Verdict            : LOW_SAMPLE
Note               : نمونه کمتر از 5 است؛ فقط برای رصد.
--------------------------------------------------------------------------------------------------------------
Regime/Side/Action : UNKNOWN / LONG / ACTIONABLE
Samples            : 1
Win Rate           : 0.00%
Avg 24h            : 0.4897%
Profit Factor      : 0.4897
Stop Rate          : 0.00%
Avg Score          : 70.00
Verdict            : LOW_SAMPLE
Note               : نمونه کمتر از 5 است؛ فقط برای رصد.
==============================================================================================================

==============================================================================================================
🚦 Freakto Advanced Live Readiness Score v4.7
==============================================================================================================
Created UTC       : 2026-07-05T16:57:35.619967+00:00
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
Note      : Win 100.00% | Expectancy 1.0470pct | PF 17.7989
Note      : Stop 0.00% | Sharpe-like 8.6425
Blocker   : Decision sample کمتر از 100 است: 17
--------------------------------------------------------------------------------------------------------------
Component : Paper Edge
Score     : 0/20
Status    : LOW
Note      : Paper quality: NO_DATA
Note      : Closed 0 | Win 0.00% | Expectancy 0.0000R | PF 0.0000
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