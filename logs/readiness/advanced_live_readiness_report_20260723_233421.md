# Freakto Advanced Live Readiness Score v4.7.1

Created UTC: 2026-07-23T23:34:21.262188+00:00

- Readiness Level: **PAPER_TRADING_PHASE**
- Readiness Score: **66/100**
- Paper Ready: True
- Live Ready: False
- Allowed Risk: 0.00%
- Conclusion: پروژه در فاز Paper/Forward Test است؛ پول واقعی هنوز مجاز نیست.

## Components
### Data Sufficiency
- Score: 12/20
- Status: PARTIAL
- Note: Complete evaluations: 100/100
- Note: Closed paper trades: 0/30
- Blocker: Closed paper trades هنوز کافی نیست: 0/30

### Decision Edge
- Score: 22/23
- Status: PASS
- Note: Decision quality: ROBUST_POSITIVE
- Note: Directional Win 60.00% | Expectancy 0.4137pct | PF 1.8978
- Note: Stop 31.00% | Sharpe-like 2.5668

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
- Note: Known/Unknown: 61/39
- Note: Best/Worst: TRENDING_BEAR/UNKNOWN
- Blocker: هنوز هیچ رژیم با Edge مثبت قابل اتکا مشخص نشده است.

### Validation Stability
- Score: 12/12
- Status: PASS
- Note: Strategy Lab اجرا شده و نمونه دارد.
- Note: Walk-Forward Validation اجرا شده و test sample دارد.

### Operational Safety
- Score: 7/7
- Status: PASS
- Note: Auto-live trading در پروژه فعال نیست.
- Note: Readiness Gate قبل از هر تست عملی باید بررسی شود.
- Note: Stop Hit Rate کنترل‌شده است: 31.00%

## Warnings
- Paper Trading هنوز نتیجه بسته‌شده ندارد.
- Market Replay v10 باید روی Test split و بعد در Forward تأیید شود؛ این مانع Paper آزمایشی نیست اما Live را مسدود می‌کند.
## Hard Blockers
- Closed paper trades هنوز کافی نیست: 0/30
- Paper sample کمتر از 30 معامله بسته‌شده است: 0
- Paper expectancy هنوز مثبت نیست.
- هنوز هیچ رژیم با Edge مثبت قابل اتکا مشخص نشده است.
- Market Replay هنوز برای Live معتبر نیست: NO_REPLAY_ROWS (rows=0, audit=FAILED_NO_REPLAY_ROWS)