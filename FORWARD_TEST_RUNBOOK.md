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
