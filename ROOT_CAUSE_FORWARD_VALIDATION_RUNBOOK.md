# Freakto v8.1.0 — Root Cause Forward Validation Runbook

این ماژول بررسی می‌کند که Root Causeهای کشف‌شده در v8 بعد از چند کندل واقعاً با جهت بازار هم‌سو بوده‌اند یا نه.

Safety:
- Research-only
- No Paper Trade creation
- No Live order
- No exchange order

## هدف

v8 می‌گفت علت محتمل فعلی چیست. v8.1 می‌سنجد آیا آن علت در Forward ارزش آماری دارد یا نه.

مثال:

```text
Root Cause: MACRO_POLICY_PRESSURE
Direction: BEARISH
Next 24h market return: -0.82%
Result: correct
```

## اجرای پیشنهادی

```cmd
python automatic_event_collector_dashboard.py --compact
python causal_intelligence_dashboard.py --compact
python market_narrative_dashboard.py --compact
python narrative_decision_dashboard.py --compact
python root_cause_dashboard.py --compact
python decision_evaluator.py
python root_cause_forward_validation_dashboard.py --compact
python forward_test_dashboard.py --plan
```

## خروجی‌ها

```text
logs/root_cause/root_cause_forward_validation_*.json
logs/root_cause/root_cause_forward_validation_report_*.md
logs/root_cause/root_cause_forward_summary_*.csv
logs/root_cause/root_cause_forward_rows_*.csv
logs/root_cause/root_cause_forward_validation_observations.csv
```

## معیارها

برای هر Root Cause:

```text
samples_4h / hit_rate_4h / avg_signed_return_4h_pct
samples_12h / hit_rate_12h / avg_signed_return_12h_pct
samples_24h / hit_rate_24h / avg_signed_return_24h_pct
validation_score
verdict
```

`avg_signed_return` یعنی بازده بازار در جهت Root Cause:

- اگر direction=BULLISH، رشد بازار مثبت حساب می‌شود.
- اگر direction=BEARISH، افت بازار مثبت حساب می‌شود.

## Verdictها

```text
ROOT_CAUSE_FORWARD_RESEARCH_CANDIDATE
FORWARD_PROMISING_LOW_SAMPLE
MIXED_BUT_POSITIVE_FORWARD_EDGE
LOW_SAMPLE
WEAK_OR_NEGATIVE_FORWARD_EVIDENCE
```

## نکته مهم

تا وقتی sample کافی نباشد، حتی Root Causeهای promising هم فقط Research/Shadow هستند و نباید Paper/Live را فعال کنند.
