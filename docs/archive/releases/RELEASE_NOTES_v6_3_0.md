# Freakto v6.3.0 — Forward Shadow Coverage & Bull Regime Probe

## چرا این نسخه ساخته شد؟

بعد از v6.2.1، Forward regime labels درست شدند اما همه تصمیم‌های فعلی در `TRENDING_BULL` بودند. از طرف دیگر Regime Shadow Gates اصلی مخصوص `TRENDING_BEAR` هستند، پس signal صفر طبیعی بود.

v6.3 برای تشخیص coverage و جلوگیری از اعتماد عجولانه به Forward کم‌نمونه ساخته شد.

## Added

- `engine/forward_shadow_coverage.py`
- `forward_shadow_coverage_dashboard.py`
- `FORWARD_SHADOW_COVERAGE_RUNBOOK.md`
- `RELEASE_NOTES_v6_3_0.md`

## Updated

- `engine/research_upgrade_suite.py`
- `engine/forward_test.py`
- `validation_suite_dashboard.py`
- `.github/workflows/freakto-forward-test.yml`
- `.github/workflows/freakto-health-check.yml`
- `README_NEXT_STEPS.md`
- `FORWARD_TEST_RUNBOOK.md`
- `SHADOW_GATE_RUNBOOK.md`
- `REGIME_SHADOW_GATE_RUNBOOK.md`
- `RESEARCH_ROBUSTNESS_RUNBOOK.md`

## Behavior

v6.3 بررسی می‌کند:

- Forward decisions در کدام regime هستند.
- کدام Shadow Gateها واقعاً signal می‌گیرند.
- چرا Regime Bear gates صفر مانده‌اند.
- آیا Bull regime در Forward نشانه‌ای دارد یا فقط sample کم است.
- آیا Forward مثبت با Backtest منفی تضاد دارد.

## Safety

هیچ سفارش واقعی ارسال نمی‌شود و هیچ Paper Trade جدید ایجاد نمی‌شود.

## Commands

```cmd
python forward_shadow_coverage_dashboard.py --compact
python freakto_research_suite_dashboard.py
python validation_suite_dashboard.py --iterations 20 --trades 10
```
