# Freakto v7.1 — Narrative/Decision Conflict Scoring Runbook

## هدف

این لایه بررسی می‌کند آیا روایت بازار با تصمیم تکنیکال هم‌جهت است یا در تضاد قرار دارد. این خروجی فقط برای Research و Forward Validation است و هیچ Paper/Live/Order واقعی فعال نمی‌کند.

## اجرای دستی

```cmd
python automatic_event_collector_dashboard.py --compact
python causal_intelligence_dashboard.py --compact
python market_narrative_dashboard.py --compact
python narrative_decision_dashboard.py --compact
```

## خروجی‌های اصلی

در گزارش `narrative_decision_dashboard.py` این فیلدها ساخته می‌شوند:

- `narrative_alignment`
- `narrative_conflict_score`
- `narrative_adjustment`
- `narrative_adjusted_score`
- `narrative_action_override`
- `narrative_decision_verdict`
- `narrative_decision_notes`

## تفسیر سریع

- `NARRATIVE_SUPPORTS_DECISION_RESEARCH_ONLY`: روایت بازار با تصمیم هم‌جهت است، اما فقط research-level.
- `DOWNGRADE_CONFIDENCE_RESEARCH_ONLY`: روایت بازار یا event risk باعث کاهش اعتماد می‌شود.
- `HIGH_CONFLICT_WATCHLIST_ONLY`: تضاد زیاد است و تصمیم باید فقط Watchlist/Research بماند.
- `NEUTRAL_DECISION_CONTEXT_ONLY`: تصمیم NEUTRAL است و روایت فقط context می‌دهد.

## فایل‌های خروجی

- `logs/narrative/narrative_decision_*.json`
- `logs/narrative/narrative_decision_report_*.md`
- `logs/narrative/narrative_decision_observations.csv`

## Safety

این ماژول:

- سفارش واقعی ارسال نمی‌کند
- Paper Trade جدید ایجاد نمی‌کند
- فقط metadata پژوهشی و forward-validation می‌سازد
