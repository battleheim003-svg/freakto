# Freakto v6.2.0 — Regime Shadow Gate Activator

## چرا این نسخه ساخته شد؟

v6.1 نشان داد چند ترکیب خاص Regime/Gate در Backtest تاریخی بعد از هزینه‌ها مثبت‌اند:

```text
TRENDING_BEAR × STRUCTURE_SCORE_GE_10
TRENDING_BEAR × RISK_MEDIUM
TRENDING_BEAR × STRUCTURE_SCORE_GE_10 × SHORT
TRENDING_BEAR × RISK_MEDIUM × SHORT
```

v6.2 این ترکیب‌ها را وارد Shadow Forward می‌کند تا در داده زنده آینده بررسی شوند.

## تغییرات اصلی

- فعال‌سازی Regime-specific Shadow Gates در `engine/shadow_gates.py`
- پشتیبانی از filterهای `regime_label_in`، `regime_label`، `risk_label`، `symbol`، `side` و فیلترهای عددی `__ge/__le`
- اضافه شدن داشبورد focused:

```cmd
python regime_shadow_gate_dashboard.py --compact
```

- آپدیت `shadow_gate_dashboard.py` به v6.2
- اضافه شدن بخش `regime_shadow_gates` به Research Suite
- آپدیت توضیحات Forward Test و Validation Suite

## ایمنی

این نسخه:

```text
Live Trading را فعال نمی‌کند
Paper Trade جدید ایجاد نمی‌کند
هیچ سفارش واقعی ارسال نمی‌کند
فقط Shadow Label و گزارش می‌سازد
```

## تست پیشنهادی

```cmd
python shadow_gate_dashboard.py --compact
python regime_shadow_gate_dashboard.py --compact
python freakto_research_suite_dashboard.py
python validation_suite_dashboard.py --iterations 20 --trades 10
```
