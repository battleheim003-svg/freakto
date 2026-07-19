# Freakto Advanced Live Readiness Score v4.7.1

Created UTC: 2026-07-19T15:37:54.311748+00:00

- Readiness Level: **PAPER_TRADING_PHASE**
- Readiness Score: **60/100**
- Paper Ready: True
- Live Ready: False
- Allowed Risk: 0.00%
- Conclusion: پروژه در فاز Paper/Forward Test است؛ پول واقعی هنوز مجاز نیست.

## Components
### Data Sufficiency
- Score: 10/20
- Status: PARTIAL
- Note: Complete evaluations: 84/100
- Note: Closed paper trades: 0/30
- Blocker: Complete evaluations هنوز کافی نیست: 84/100
- Blocker: Closed paper trades هنوز کافی نیست: 0/30

### Decision Edge
- Score: 20/23
- Status: PARTIAL
- Note: Decision quality: MIXED_VALIDATION
- Note: Directional Win 63.10% | Expectancy 0.4376pct | PF 1.9447
- Note: Stop 36.90% | Sharpe-like 2.4436
- Blocker: Decision sample کمتر از 100 است: 84

### Paper Edge
- Score: 0/20
- Status: LOW
- Note: Paper quality: NO_DATA
- Note: Closed 0 | Paper Win 0.00% | Expectancy 0.0000R | PF 0.0000
- Note: Max drawdown 0.0000R
- Blocker: Paper sample کمتر از 30 معامله بسته‌شده است: 0
- Blocker: Paper expectancy هنوز مثبت نیست.

### Regime Stability
- Score: 13/18
- Status: PARTIAL
- Note: Regime verdict: REGIME_DATA_COLLECTING
- Note: Known/Unknown: 61/23
- Note: Best/Worst: TRENDING_BEAR/UNKNOWN
- Blocker: هنوز هیچ رژیم با Edge مثبت قابل اتکا مشخص نشده است.

### Validation Stability
- Score: 12/12
- Status: PASS
- Note: Strategy Lab اجرا شده و نمونه دارد.
- Note: Walk-Forward Validation اجرا شده و test sample دارد.

### Operational Safety
- Score: 5/7
- Status: PARTIAL
- Note: Auto-live trading در پروژه فعال نیست.
- Note: Readiness Gate قبل از هر تست عملی باید بررسی شود.
- Blocker: Stop Hit Rate بالاست: 36.90%

## Warnings
- Paper Trading هنوز نتیجه بسته‌شده ندارد.
- Market Replay v10 باید روی Test split و بعد در Forward تأیید شود؛ این مانع Paper آزمایشی نیست اما Live را مسدود می‌کند.
## Hard Blockers
- Complete evaluations هنوز کافی نیست: 84/100
- Closed paper trades هنوز کافی نیست: 0/30
- Decision sample کمتر از 100 است: 84
- Paper sample کمتر از 30 معامله بسته‌شده است: 0
- Paper expectancy هنوز مثبت نیست.
- هنوز هیچ رژیم با Edge مثبت قابل اتکا مشخص نشده است.
- Stop Hit Rate بالاست: 36.90%
- Market Replay هنوز برای Live معتبر نیست: NO_REPLAY_ROWS (rows=0, audit=FAILED_NO_REPLAY_ROWS)