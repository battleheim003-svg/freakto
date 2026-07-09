# Freakto v7.1.0 — Narrative/Decision Conflict Scoring

## خلاصه

v7.1 روایت بازار را از یک گزارش مستقل به یک لایه امتیازدهی research-level تبدیل می‌کند. از این نسخه، سیستم می‌تواند بگوید روایت بازار با bias تصمیم فعلی هم‌جهت است، در تضاد است، یا فقط context خنثی می‌دهد.

## فایل‌های جدید

- `engine/narrative_decision_conflict.py`
- `narrative_decision_dashboard.py`
- `NARRATIVE_DECISION_RUNBOOK.md`
- `RELEASE_NOTES_v7_1_0.md`

## فایل‌های آپدیت‌شده

- `engine/market_narrative.py`
- `monitor.py`
- `decision_logger.py`
- `decision_log_repair.py`
- `decision_evaluator.py`
- `engine/forward_test.py`
- `engine/research_upgrade_suite.py`
- `.github/workflows/freakto-forward-test.yml`
- `.github/workflows/freakto-health-check.yml`
- `README_NEXT_STEPS.md`
- `FORWARD_TEST_RUNBOOK.md`
- `MARKET_NARRATIVE_RUNBOOK.md`
- `RESEARCH_ROBUSTNESS_RUNBOOK.md`
- `SHADOW_GATE_RUNBOOK.md`

## فیلدهای جدید در decision log

- `narrative_alignment`
- `narrative_conflict_score`
- `narrative_adjustment`
- `narrative_adjusted_score`
- `narrative_action_override`
- `narrative_decision_verdict`
- `narrative_decision_notes`

## Forward Plan

مرحله جدید اضافه شد:

```text
narrative_decision_conflict_probe
Command: python -X utf8 narrative_decision_dashboard.py --compact
```

## Safety

v7.1 همچنان Research-only است:

- Live: خیر
- Paper جدید: خیر
- Order واقعی: خیر
- فقط narrative/decision metadata و validation context
