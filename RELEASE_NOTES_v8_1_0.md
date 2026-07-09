# Release Notes — Freakto v8.1.0

## Root Cause Forward Validation

v8.1.0 یک لایه research-only اضافه می‌کند که خروجی‌های Root Cause Discovery را با کندل‌های آینده اعتبارسنجی می‌کند.

## New files

```text
engine/root_cause_forward_validation.py
root_cause_forward_validation_dashboard.py
ROOT_CAUSE_FORWARD_VALIDATION_RUNBOOK.md
RELEASE_NOTES_v8_1_0.md
```

## Updated files

```text
decision_evaluator.py
engine/forward_test.py
engine/research_upgrade_suite.py
validation_suite_dashboard.py
.github/workflows/freakto-forward-test.yml
.github/workflows/freakto-health-check.yml
README_NEXT_STEPS.md
FORWARD_TEST_RUNBOOK.md
ROOT_CAUSE_DISCOVERY_RUNBOOK.md
RESEARCH_ROBUSTNESS_RUNBOOK.md
SHADOW_GATE_RUNBOOK.md
```

## New evaluation fields

decision_evaluator.py now writes raw market returns in addition to side-adjusted decision returns:

```text
market_return_after_4h_pct
market_return_after_12h_pct
market_return_after_24h_pct
root_cause_signed_return_after_4h_pct
root_cause_signed_return_after_12h_pct
root_cause_signed_return_after_24h_pct
root_cause_direction_correct_after_4h
root_cause_direction_correct_after_12h
root_cause_direction_correct_after_24h
```

## New dashboard

```cmd
python root_cause_forward_validation_dashboard.py --compact
```

## Forward plan

New optional task:

```text
root_cause_forward_validation_probe
```

It runs after `decision_evaluator`, because it needs future-return evaluation rows.

## Safety

No Paper/Live changes. No real orders. Research-only validation.
