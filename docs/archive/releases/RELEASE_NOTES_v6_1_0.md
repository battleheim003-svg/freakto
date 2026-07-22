# Freakto v6.1.0 — Regime-Split Gate Matrix

## هدف

v6.1 بعد از v6.0 اضافه شد تا Gateهای Backtest/Robustness را به تفکیک Regime، Side و Symbol بررسی کند.

## فایل‌های جدید

```text
engine/regime_gate_matrix.py
regime_gate_matrix_dashboard.py
REGIME_GATE_MATRIX_RUNBOOK.md
RELEASE_NOTES_v6_1_0.md
```

## فایل‌های اصلاح‌شده

```text
engine/research_upgrade_suite.py
validation_suite_dashboard.py
README_NEXT_STEPS.md
RESEARCH_ROBUSTNESS_RUNBOOK.md
.github/workflows/freakto-forward-test.yml
.github/workflows/freakto-health-check.yml
```

## قابلیت‌ها

```text
Regime × Gate Matrix
Regime × Gate × Side Matrix
Regime × Side Matrix
Regime × Symbol Matrix
Avoid Regime Detection
Shadow-only proposal generation
Cost-adjusted net return با fee/slippage
Sample و overfit warning
ادغام با Research Suite و Validation Suite
```

## اجرای دستی

```cmd
python regime_gate_matrix_dashboard.py --compact
python regime_gate_matrix_dashboard.py --compact --primary-only
python freakto_research_suite_dashboard.py
python validation_suite_dashboard.py
```

## خروجی‌ها

```text
logs/research/v6_suite/regime_gate_matrix_*.json
logs/research/v6_suite/regime_gate_matrix_report_*.md
logs/research/v6_suite/regime_gate_matrix_results_*.csv
logs/research/v6_suite/regime_gate_side_matrix_results_*.csv
logs/research/v6_suite/regime_avoid_candidates_*.csv
logs/research/v6_suite/regime_shadow_proposals_*.json
```

## Safety

این نسخه هیچ سفارش واقعی ارسال نمی‌کند، هیچ Paper Trade جدید نمی‌سازد و فقط برای Research/Shadow Validation است.
