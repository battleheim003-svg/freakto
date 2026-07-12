# Freakto Advanced Live Readiness Score v4.7.1

Created UTC: 2026-07-12T11:48:47.716198+00:00

- Readiness Level: **PAPER_TRADING_PHASE**
- Readiness Score: **57/100**
- Paper Ready: True
- Live Ready: False
- Allowed Risk: 0.00%
- Conclusion: پروژه در فاز Paper/Forward Test است؛ پول واقعی هنوز مجاز نیست.

## Components
### Data Sufficiency
- Score: 7/20
- Status: LOW
- Note: Complete evaluations: 55/100
- Note: Closed paper trades: 0/30
- Blocker: Complete evaluations هنوز کافی نیست: 55/100
- Blocker: Closed paper trades هنوز کافی نیست: 0/30

### Decision Edge
- Score: 20/23
- Status: PARTIAL
- Note: Decision quality: MIXED_VALIDATION
- Note: Directional Win 72.73% | Expectancy 0.6557pct | PF 2.9253
- Note: Stop 41.82% | Sharpe-like 3.2077
- Blocker: Decision sample کمتر از 100 است: 55

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
- Note: Known/Unknown: 55/0
- Note: Best/Worst: TRENDING_BEAR/TRENDING_BULL
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
- Blocker: Stop Hit Rate بالاست: 41.82%

## Warnings
- Paper Trading هنوز نتیجه بسته‌شده ندارد.
- Market Replay v10 باید روی Test split و بعد در Forward تأیید شود؛ این مانع Paper آزمایشی نیست اما Live را مسدود می‌کند.
## Hard Blockers
- Complete evaluations هنوز کافی نیست: 55/100
- Closed paper trades هنوز کافی نیست: 0/30
- Decision sample کمتر از 100 است: 55
- Paper sample کمتر از 30 معامله بسته‌شده است: 0
- Paper expectancy هنوز مثبت نیست.
- هنوز هیچ رژیم با Edge مثبت قابل اتکا مشخص نشده است.
- Stop Hit Rate بالاست: 41.82%
- Market Replay هنوز برای Live معتبر نیست: NO_REPLAY_ROWS (rows=0, audit=FAILED_NO_REPLAY_ROWS)