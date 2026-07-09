# Freakto v6.2.1 — Forward Regime Label Injection Runbook

## هدف

v6.2.1 مطمئن می‌شود تصمیم‌های Forward و ارزیابی‌های آن‌ها دارای `regime_label` و metadata لازم باشند تا Regime Shadow Gateهای v6.2 بتوانند واقعاً signal جمع کنند.

## ایمنی

این Patch هیچ سفارش واقعی ارسال نمی‌کند، هیچ Paper Trade جدید نمی‌سازد و فقط فایل‌های research log را با داده‌هایی که در لحظه تصمیم قابل دانستن بوده‌اند غنی می‌کند.

## دستورهای اصلی

```cmd
python forward_regime_label_dashboard.py --compact
python forward_regime_label_dashboard.py --compact --dry-run
python regime_shadow_gate_dashboard.py --compact
python forward_test_dashboard.py --plan
python forward_test_dashboard.py --cycle --validate --continue-on-error
```

## خروجی‌ها

```text
logs/research/v6_suite/forward_regime_labeling_*.json
logs/research/v6_suite/forward_regime_labeling_report_*.md
logs/decisions.csv.bak_v621_*
logs/decision_evaluations.csv.bak_v621_*
```

## ستون‌هایی که اضافه/ترمیم می‌شوند

```text
regime_label
regime_confidence
regime_adjustment
regime_source
regime_label_quality
trend_state
volatility_state
market_phase
```

## ترتیب اجرای Forward Cycle

در v6.2.1 این مرحله به چرخه Forward اضافه شده است:

```text
decision_log_repair
forward_regime_label_injection
decision_evaluator
shadow_gate_validator
```

این ترتیب باعث می‌شود `decision_evaluator.py` هم regime metadata را وارد `decision_evaluations.csv` کند.

## کیفیت labelها

- `DIRECT_ENGINE`: از خود DecisionEngine آمده و قابل‌اعتمادترین نوع است.
- `TEXT_INFERRED`: از متن reasons/warnings قدیمی استخراج شده است.
- `LOW_CONF_PROXY`: از score/componentهای لحظه تصمیم ساخته شده و فقط برای research است.
- `UNKNOWN`: هنوز evidence کافی وجود ندارد.

## معیار خوب شدن وضعیت

برای شروع تحلیل Regime Shadow باید حداقل این‌ها رشد کنند:

```text
Known Forward regime rows >= 30
Regime Shadow signals > 0
برای هر gate حداقل 30 evaluated samples
```

تا قبل از آن Paper/Live همچنان ممنوع است.
