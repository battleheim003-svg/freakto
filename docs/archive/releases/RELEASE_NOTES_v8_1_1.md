# Freakto v8.1.1 — Root Cause Evaluation Bridge Patch

این Patch اتصال بین `root_cause_dashboard.py` و `decision_evaluator.py` را کامل می‌کند.

## مشکل نسخه v8.1.0

`root_cause_dashboard.py` علت اصلی را می‌ساخت و در `logs/root_cause/*.json` ذخیره می‌کرد، اما اگر ردیف‌های قدیمی `decisions.csv` هنوز ستون‌های `root_cause_*` خالی داشتند، `decision_evaluator.py` همان مقدارهای خالی را به `decision_evaluations.csv` منتقل می‌کرد. در نتیجه:

```text
Root Cause Rows: 0
NO_ROOT_CAUSE_ROWS_EVALUATED
```

## اصلاح v8.1.1

`decision_evaluator.py` اکنون آخرین Root Cause JSON را می‌خواند و فقط وقتی `latest_decision_id` آن با `decision_id` ردیف تصمیم برابر باشد، metadata علت را به evaluation تزریق می‌کند.

این رفتار محافظه‌کارانه است و از اعمال اشتباه Root Cause امروز روی همه تصمیم‌های تاریخی جلوگیری می‌کند.

## ستون جدید

```text
root_cause_bridge_source
```

اگر bridge اعمال شود مقدار آن می‌شود:

```text
LATEST_ROOT_CAUSE_JSON_MATCHED_DECISION_ID
```

## ترتیب اجرای پیشنهادی

```cmd
python root_cause_dashboard.py --compact
python decision_evaluator.py
python root_cause_forward_validation_dashboard.py --compact
```

## ایمنی

این Patch همچنان Research-only است و هیچ Paper/Live/Order واقعی ایجاد نمی‌کند.
