# Freakto v8.0.0 — Root Cause Discovery Engine

این ماژول یک لایه‌ی کاملاً Research-only است که تلاش می‌کند برای حرکت/زمینه‌ی فعلی بازار، چند علت محتمل را وزن‌دهی کند.

## هدف

به جای اینکه فقط بگوییم روایت بازار bearish یا bullish است، این ماژول می‌پرسد:

- احتمالاً علت اصلی چیست؟
- شواهد از کدام منبع آمده‌اند؟
- سهم نسبی هر علت چقدر است؟
- آیا علت‌ها با هم تضاد دارند؟
- کیفیت evidence چقدر است؟

## منابع مورد استفاده

```text
1. data/auto_events.csv
2. data/manual_events.csv
3. logs/causal/causal_observations.csv
4. logs/narrative/market_narrative_observations.csv
5. logs/narrative/narrative_decision_observations.csv
6. logs/decisions.csv
```

## خروجی‌های اصلی

```text
primary_root_cause
root_cause_direction
root_cause_confidence
root_cause_probability_pct
root_cause_evidence_quality
root_cause_verdict
root_cause_summary
top_causes
root_cause_evidence
```

## اجرای دستی

```cmd
python automatic_event_collector_dashboard.py --compact
python causal_intelligence_dashboard.py --compact
python market_narrative_dashboard.py --compact
python narrative_decision_dashboard.py --compact
python root_cause_dashboard.py --compact
```

## نکته ایمنی

Root Cause Discovery علت قطعی تولید نمی‌کند. این فقط hypothesis ranking است و نباید به‌تنهایی باعث ورود، Paper یا Live شود.

## مسیر بعدی

بعد از جمع‌آوری چند هفته داده، خروجی root cause باید با outcomeهای forward مقایسه شود:

```text
Root cause → بعد از 4h/12h/24h چه عملکردی داشته؟
```

این مرحله پایه‌ی v8.1 یعنی Root-Cause Outcome Validator خواهد بود.

---

## v8.1 — Forward Validation برای Root Causeها

Root Cause Discovery علت‌های محتمل را تولید می‌کند. برای اینکه بفهمیم این علت‌ها واقعاً ارزش پژوهشی دارند، v8.1 خروجی‌ها را با کندل‌های بعدی می‌سنجد:

```cmd
python decision_evaluator.py
python root_cause_forward_validation_dashboard.py --compact
```

اگر یک Root Cause در چندین نمونه hit-rate و avg_signed_return مثبت بگیرد، بعداً می‌تواند وارد Root-Cause Gate Simulator شود. تا آن زمان فقط Research-only است.
