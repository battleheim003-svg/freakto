# Freakto v7.0.0 — Market Narrative Engine

این ماژول Research-only است و از eventهای فیلترشده، manual events و آخرین خروجی Causal Intelligence یک روایت بازار می‌سازد.

## اجرا

```cmd
python automatic_event_collector_dashboard.py --compact
python causal_intelligence_dashboard.py --compact
python market_narrative_dashboard.py --compact
```

## خروجی‌های اصلی

- `narrative_label`
- `narrative_confidence`
- `dominant_direction`
- `dominant_theme`
- `net_direction_score`
- `event_risk`
- `technical_event_conflict`
- `top_drivers`

## منطق v7

1. eventهای auto/manual را می‌خواند.
2. صفحه‌های محصول، navigation و HTML noise را حذف می‌کند.
3. رویدادها را بر اساس tier، impact، confidence و تازگی وزن‌دهی می‌کند.
4. theme غالب مثل `MACRO_POLICY` یا `REGULATORY_RISK` را پیدا می‌کند.
5. اگر شواهد bullish و bearish همزمان قوی باشند، conflict گزارش می‌دهد.

## ایمنی

این ماژول هیچ Paper/Live فعال نمی‌کند و فقط برای research/reporting است.

## v7.1 — Narrative/Decision Conflict Scoring

مرحله جدید:

```cmd
python narrative_decision_dashboard.py --compact
```

این مرحله بررسی می‌کند روایت بازار با تصمیم فعلی هم‌جهت است یا نه و این فیلدها را برای Research/Forward اضافه می‌کند:

- `narrative_alignment`
- `narrative_conflict_score`
- `narrative_adjustment`
- `narrative_adjusted_score`
- `narrative_action_override`
- `narrative_decision_verdict`

این لایه هیچ Paper/Live/Order واقعی فعال نمی‌کند.



## اتصال به v8 Root Cause Discovery

Market Narrative در v8 دیگر فقط روایت نهایی نیست؛ `dominant_theme`, `dominant_direction`, `net_direction_score` و contradictions به عنوان evidence برای root-cause hypothesis ranking استفاده می‌شوند.
