# Freakto v8.2.0 — Root Cause Sample Accumulator Runbook

## هدف

این ماژول برای این ساخته شده که بعد از Root Cause Discovery و Root Cause Forward Validation، وضعیت بلوغ نمونه‌ها را پایش کند.

v8.1.1 مشکل Bridge را حل کرد. v8.2.0 یک قدم جلوتر می‌رود:

- همه Root Cause JSONهای قبلی را بر اساس `decision_id` به `decision_evaluations.csv` وصل می‌کند.
- فقط latest snapshot را استفاده نمی‌کند؛ history را هم بررسی می‌کند.
- تعداد Root Cause rows، evaluated cells، gap تا حداقل نمونه و gap تا research/candidate readiness را گزارش می‌کند.
- هیچ Paper/Live فعال نمی‌کند.

## اجرای پیشنهادی

```cmd
python root_cause_dashboard.py --compact
python decision_evaluator.py
python root_cause_forward_validation_dashboard.py --compact
python root_cause_sample_dashboard.py --compact
```

## خروجی‌های اصلی

```text
logs/root_cause/root_cause_sample_tracker_*.json
logs/root_cause/root_cause_sample_tracker_report_*.md
logs/root_cause/root_cause_sample_buckets_*.csv
logs/root_cause/root_cause_sample_tracker_observations.csv
```

## آستانه‌ها

پیش‌فرض‌ها:

```text
min_cells       = 10
research_cells  = 30
candidate_cells = 90
```

هر تصمیم کامل Root Cause می‌تواند حداکثر 3 cell تولید کند:

```text
4h
12h
24h
```

## تفسیر وضعیت‌ها

```text
ROOT_CAUSE_SAMPLE_COLLECTION_ACTIVE_LOW_SAMPLE
```
نمونه کم است؛ فقط جمع‌آوری ادامه پیدا کند.

```text
ROOT_CAUSE_MIN_SAMPLE_READY
```
حداقل نمونه خام رسیده، ولی هنوز برای نتیجه‌گیری کافی نیست.

```text
ROOT_CAUSE_RESEARCH_SAMPLE_READY
```
برای تحلیل پژوهشی اولیه مناسب است، اما هنوز Gate/Paper نیست.

```text
ROOT_CAUSE_SAMPLE_TARGET_REACHED_MIXED
```
نمونه کافی‌تر است ولی نتیجه هنوز نیاز به validation دارد.

```text
ROOT_CAUSE_VALIDATION_RESEARCH_CANDIDATES_FOUND
```
یک یا چند Root Cause از نظر forward validation کاندید پژوهشی شده‌اند.

## نکته مهم

این ماژول فقط maturity tracker است. حتی اگر sample کافی شد، Paper/Live فعال نمی‌شود. مرحله بعد از sample کافی، Root-Cause Gate Simulator است.


## اتصال به v9 Evidence Graph

پس از اینکه Root Cause sample tracker نمونه‌ها را شمرد، `evidence_graph_dashboard.py` می‌تواند همان نمونه‌ها را به مسیرهای evidence تبدیل کند و نشان دهد کدام مسیرها در Forward بهتر یا بدتر بوده‌اند.
