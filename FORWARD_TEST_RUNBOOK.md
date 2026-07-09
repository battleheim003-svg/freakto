# Freakto Forward Test Runbook — v5.1.1

این Runbook برای اجرای امن چرخه Forward Test در ویندوز است. این چرخه هیچ سفارش واقعی ارسال نمی‌کند.

## وضعیت فعلی

```cmd
python forward_test_dashboard.py --status
```

## دیدن برنامه اجرا

```cmd
python forward_test_dashboard.py --plan
```

## اجرای چرخه Forward Test

```cmd
python forward_test_dashboard.py --cycle --validate --continue-on-error
```

برای ارسال گزارش به Telegram:

```cmd
python forward_test_dashboard.py --cycle --validate --continue-on-error --send
```

## رفع مشکل Unicode در Windows

از v5.1.1، Forward Test Runner همه child processها را با UTF-8 اجرا می‌کند:

- `python -X utf8 ...`
- `PYTHONUTF8=1`
- `PYTHONIOENCODING=utf-8`

اگر از فایل batch استفاده می‌کنی، batchهای جدید را بساز:

```cmd
python forward_test_dashboard.py --write-bat
```

سپس:

```cmd
run_forward_test_cycle.bat
```

## هدف داده‌ای

- حداقل 100 ارزیابی کامل
- حداقل 30 Paper Trade بسته‌شده
- حداقل 30 نمونه دارای regime_label
- حداقل 30 روز Forward Test

تا وقتی Live Readiness خروجی `MICRO_LIVE_READY` ندهد، ورود با پول واقعی ممنوع است.


## v5.1.2 Decision Log Repair

If `decision_evaluator.py` fails with a pandas CSV parser error after `monitor.py --once`, run:

```cmd
python decision_log_repair.py
python decision_evaluator.py
```

The Forward Test cycle now runs the repair step automatically before evaluation.


## v5.3.3 Shadow Gate Step

از v5.3.3 چرخه Forward Test بعد از `decision_evaluator.py` این مرحله optional را اجرا می‌کند:

```cmd
python -X utf8 shadow_gate_dashboard.py --compact
```

این مرحله فقط Gateهای تحقیقاتی را روی تصمیم‌های Forward علامت‌گذاری می‌کند و هیچ Paper/Live ایجاد نمی‌کند. خروجی‌های آن در مسیر زیر ذخیره می‌شوند:

```text
logs/shadow_gates/
```

---

## v6.2 Regime Shadow Gate Activator داخل Forward Cycle

از v6.2 به بعد، مرحله `shadow_gate_validator` علاوه بر gateهای پایه، gateهای Regime-specific را هم رصد می‌کند:

```text
REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10
REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT
REGIME_TRENDING_BEAR__RISK_MEDIUM
REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT
```

برای تست دستی:

```cmd
python forward_test_dashboard.py --cycle --validate --continue-on-error
python shadow_gate_dashboard.py --compact
python regime_shadow_gate_dashboard.py --compact
```

این مرحله هیچ Paper/Live ایجاد نمی‌کند.

---

## v6.2.1 — Forward Regime Label Injection در Cycle

از v6.2.1 چرخه Forward این مرحله را قبل از `decision_evaluator` اجرا می‌کند:

```text
forward_regime_label_injection
Command: python -X utf8 forward_regime_label_dashboard.py --compact
```

این مرحله ستون‌های زیر را در لاگ‌های Forward تضمین می‌کند:

```text
regime_label, regime_confidence, regime_source, regime_label_quality,
trend_state, volatility_state, market_phase
```

تست دستی:

```cmd
python forward_regime_label_dashboard.py --compact
python forward_test_dashboard.py --plan
```
