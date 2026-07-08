# Freakto v6.2.0 — Regime Shadow Gate Activator Runbook

## هدف

v6.2 پیشنهادهای v6.1 Regime-Gate Matrix را وارد Shadow Forward می‌کند تا در اجرای‌های آینده، بدون Paper و بدون Live، جداگانه رصد شوند.

## Gateهای Regime فعال‌شده

```text
REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10
REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT
REGIME_TRENDING_BEAR__RISK_MEDIUM
REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT
```

این‌ها از خروجی v6.1 آمده‌اند و همگی `SHADOW_ONLY` هستند.

## دستورهای تست

```cmd
python shadow_gate_dashboard.py --compact
python regime_shadow_gate_dashboard.py --compact
python freakto_research_suite_dashboard.py
python validation_suite_dashboard.py --iterations 20 --trades 10
```

## خروجی‌ها

```text
logs/shadow_gates/shadow_gate_signals.csv
logs/shadow_gates/shadow_gate_metrics_<run_id>.csv
logs/shadow_gates/shadow_gate_status_<run_id>.json
logs/shadow_gates/shadow_gate_report_<run_id>.md
logs/shadow_gates/shadow_gate_runs.csv
```

## معیار تأیید

هر Regime Shadow Gate برای عبور از مرحله Research باید حداقل این‌ها را در Forward واقعی بگیرد:

```text
حداقل 30 نمونه کامل
Avg Return مثبت
Win Rate حداقل 50%
Target 1 Hit Rate >= Stop Rate
MFE/MAE >= 1
```

## ایمنی

v6.2 هیچ سفارش واقعی ارسال نمی‌کند و هیچ Paper Trade جدید ایجاد نمی‌کند. این نسخه فقط label/research/report می‌سازد.
