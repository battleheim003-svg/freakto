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

---

## v8.1.1 Bridge Patch

اگر `root_cause_forward_validation_dashboard.py` مقدار `Root Cause Rows: 0` نشان داد، با v8.1.1 این مسیر بررسی می‌شود:

1. آخرین فایل `logs/root_cause/root_cause_*.json` خوانده می‌شود.
2. اگر `latest_decision_id` آن با `decision_id` یک ردیف در `decisions.csv` برابر باشد، فیلدهای `root_cause_*` هنگام `decision_evaluator.py` به `decision_evaluations.csv` تزریق می‌شوند.
3. سپس Forward Validation می‌تواند جهت Root Cause را با `market_return_after_4h/12h/24h` بسنجد.

ترتیب امن:

```cmd
python root_cause_dashboard.py --compact
python decision_evaluator.py
python root_cause_forward_validation_dashboard.py --compact
```

این bridge فقط روی ردیف matching decision_id اعمال می‌شود و Root Cause جدید را به همه ردیف‌های تاریخی تعمیم نمی‌دهد.

---

## v8.2 Historical Bridge + Sample Accumulator

در v8.2، `decision_evaluator.py` فقط آخرین Root Cause JSON را نمی‌خواند. همه فایل‌های Root Cause JSON و `root_cause_observations.csv` را بر اساس `decision_id` بررسی می‌کند و metadata علت را به evaluation row مربوط وصل می‌کند.

بعد از اجرای validation این دستور را هم بزن:

```cmd
python root_cause_sample_dashboard.py --compact
```

اگر خروجی هنوز `LOW_SAMPLE` بود، طبیعی است. هدف v8.2 این است که sampleها با گذر زمان به 30 تا 90 evaluated cells برسند.
