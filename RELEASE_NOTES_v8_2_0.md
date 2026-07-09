# Freakto v8.2.0 — Root Cause Sample Accumulator & Historical Bridge

## خلاصه

v8.2.0 برای تبدیل Root Cause Forward Validation به یک فرآیند جمع‌آوری نمونه پایدار ساخته شد.

در v8.1.1 فقط آخرین Root Cause JSON به decision_evaluations وصل می‌شد. این امن بود، اما برای sample accumulation کافی نبود. در v8.2.0، `decision_evaluator.py` همه Root Cause JSONها و ledger قبلی را بر اساس `decision_id` بررسی می‌کند و هر تصمیم matching را به metadata علت وصل می‌کند.

## فایل‌های جدید

```text
engine/root_cause_sample_tracker.py
root_cause_sample_dashboard.py
ROOT_CAUSE_SAMPLE_ACCUMULATOR_RUNBOOK.md
RELEASE_NOTES_v8_2_0.md
```

## فایل‌های تغییرکرده

```text
decision_evaluator.py
engine/forward_test.py
engine/research_upgrade_suite.py
validation_suite_dashboard.py
.github/workflows/freakto-forward-test.yml
.github/workflows/freakto-health-check.yml
FORWARD_TEST_RUNBOOK.md
README_NEXT_STEPS.md
ROOT_CAUSE_FORWARD_VALIDATION_RUNBOOK.md
RESEARCH_ROBUSTNESS_RUNBOOK.md
```

## قابلیت‌های جدید

- Historical Root Cause bridge بر اساس تمام JSONها و observations ledger.
- Root Cause Sample Accumulator dashboard.
- شمارش Root Cause rows و evaluated cells.
- محاسبه gap تا min/research/candidate sample thresholds.
- اضافه شدن مرحله `root_cause_sample_tracker` به Forward Plan و GitHub Actions.

## اجرای تست

```cmd
python root_cause_dashboard.py --compact
python decision_evaluator.py
python root_cause_forward_validation_dashboard.py --compact
python root_cause_sample_dashboard.py --compact
python forward_test_dashboard.py --plan
```

## وضعیت ایمنی

```text
Live: خیر
Paper جدید: خیر
Order واقعی: خیر
فقط root-cause sample tracking و maturity reporting
```
