# Freakto v5.3.3 — Candidate Gate Shadow Validator

## هدف

بعد از v5.3.2 چند Gate تحقیقاتی مثبت در Backtest پیدا شد. این نسخه آن Gateها را وارد Forward Test می‌کند، اما فقط در حالت Shadow.

## فایل‌های جدید

```text
engine/shadow_gates.py
shadow_gate_dashboard.py
SHADOW_GATE_RUNBOOK.md
RELEASE_NOTES_v5_3_3.md
```

## فایل‌های اصلاح‌شده

```text
decision_logger.py
engine/forward_test.py
validation_suite_dashboard.py
README_NEXT_STEPS.md
FORWARD_TEST_RUNBOOK.md
```

## Gateهای تحت نظر

```text
VOLUME_SCORE_GE_10
RISK_MEDIUM
HISTORICAL_EDGE_SCORE_GE_1
STRUCTURE_SCORE_GE_10
SCORE_GE_80
DOGE_SHORT_WATCH
BNB_LONG_SCORE_GE_60
```

## رفتار جدید Forward Cycle

از این نسخه به بعد، چرخه Forward بعد از `decision_evaluator.py` این مرحله را هم اجرا می‌کند:

```cmd
python -X utf8 shadow_gate_dashboard.py --compact
```

این مرحله optional است و اگر شکست بخورد، اصل جمع‌آوری داده را متوقف نمی‌کند.

## خروجی‌ها

```text
logs/shadow_gates/shadow_gate_signals.csv
logs/shadow_gates/shadow_gate_status_<run_id>.json
logs/shadow_gates/shadow_gate_report_<run_id>.md
logs/shadow_gates/shadow_gate_metrics_<run_id>.csv
logs/shadow_gates/shadow_gate_runs.csv
```

## نکته ایمنی

این نسخه هیچ معامله واقعی و هیچ Paper Trade باز نمی‌کند. فقط برچسب تحقیقاتی می‌زند و منتظر ارزیابی Forward می‌ماند.
