# Freakto v6.2.1 — Forward Regime Label Injection Patch

## چرا این نسخه ساخته شد؟

v6.2 Regime Shadow Gateها را فعال کرد، اما خروجی نشان داد هنوز هیچ Forward decision این gateها را پاس نکرده است. یکی از علت‌های محتمل این بود که `regime_label` در Forward/evaluation logs کامل وارد نشده یا برای لاگ‌های legacy خالی مانده است.

## تغییرات اصلی

### اضافه شد

```text
engine/forward_regime_labeling.py
forward_regime_label_dashboard.py
FORWARD_REGIME_LABELING_RUNBOOK.md
RELEASE_NOTES_v6_2_1.md
```

### آپدیت شد

```text
decision_logger.py
decision_log_repair.py
decision_evaluator.py
engine/forward_test.py
engine/shadow_gates.py
engine/research_upgrade_suite.py
validation_suite_dashboard.py
README_NEXT_STEPS.md
FORWARD_TEST_RUNBOOK.md
SHADOW_GATE_RUNBOOK.md
REGIME_SHADOW_GATE_RUNBOOK.md
RESEARCH_ROBUSTNESS_RUNBOOK.md
.github/workflows/freakto-forward-test.yml
.github/workflows/freakto-health-check.yml
```

## قابلیت‌ها

- اضافه شدن `forward_regime_label_injection` به Forward Cycle.
- تضمین ستون‌های regime در `decisions.csv`.
- کپی regime metadata به `decision_evaluations.csv`.
- backfill محافظه‌کارانه برای لاگ‌های قدیمی با `TEXT_INFERRED` یا `LOW_CONF_PROXY`.
- گزارش وضعیت coverage برای known/unknown regime rows.
- اضافه شدن بخش `forward_regime_labeling` به Research Suite و Validation Suite.

## ایمنی

این نسخه outcome را برای تشخیص regime استفاده نمی‌کند. ستون‌هایی مثل return/target/stop/MFE/MAE فقط بعداً برای ارزیابی استفاده می‌شوند، نه برای تزریق label.

## دستور تست

```cmd
python forward_regime_label_dashboard.py --compact
python forward_regime_label_dashboard.py --compact --dry-run
python forward_test_dashboard.py --plan
python regime_shadow_gate_dashboard.py --compact
python freakto_research_suite_dashboard.py
```

## وضعیت تصمیم‌گیری

```text
Live Trading: ممنوع
Paper Trade جدید: خیر
Research/Shadow: فعال
هدف: آماده‌سازی Forward logs برای Regime Shadow Gate validation
```
