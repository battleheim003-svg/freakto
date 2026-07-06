# Freakto v3.1.0 — Self-Learning Engine

## هدف

این نسخه Freakto را وارد فاز یادگیری محافظه‌کارانه از عملکرد خودش می‌کند.

در v3.1 سیستم هنوز هیچ وزن یا قانون اجرایی را خودکار تغییر نمی‌دهد؛ فقط از خروجی‌های واقعی `decision_evaluations.csv` و `decisions.csv` تحلیل می‌سازد و پیشنهادهای قابل بررسی ارائه می‌دهد.

## فایل‌های اضافه‌شده

```text
engine/self_learning.py
self_learning_dashboard.py
RELEASE_NOTES_v3_1_0.md
```

## قابلیت‌ها

### 1. Self-Learning Report

گزارش یادگیری از تصمیم‌های قبلی ساخته می‌شود:

```cmd
python self_learning_dashboard.py
```

### 2. تحلیل Overall Edge

سیستم بررسی می‌کند:

- Win Rate کلی
- Avg 24h Return
- Stop Rate
- Avg 4h Return

### 3. تحلیل Score Bucket

تصمیم‌ها بر اساس بازه امتیاز بررسی می‌شوند:

```text
<50
50-59
60-69
70-79
80+
```

و مشخص می‌شود آیا Scoreهای بالا واقعاً عملکرد بهتری داشته‌اند یا نه.

### 4. تحلیل Component Weight

در صورت وجود داده کافی، اثر نسبی بخش‌های زیر بررسی می‌شود:

- Trend
- Momentum
- Volume
- Structure
- Risk

### 5. تحلیل Actionability

سیستم بررسی می‌کند Watchlist / Actionable واقعاً عملکرد قابل قبول داشته‌اند یا Quality Gate باید سخت‌گیرتر شود.

### 6. خروجی Markdown و JSON

گزارش‌ها ذخیره می‌شوند در:

```text
logs/learning/self_learning_report_YYYYMMDD_HHMMSS.md
logs/learning/self_learning_recommendations.json
```

فایل JSON در آینده می‌تواند مبنای Adaptive Weight Config باشد.

## اجرا

```cmd
python decision_evaluator.py
python self_learning_dashboard.py
```

ارسال به تلگرام:

```cmd
python self_learning_dashboard.py --send
```

## نکته مهم

این نسخه فقط Advisory است:

```text
Auto-apply: OFF
```

یعنی هیچ تغییری در وزن‌های موتور به شکل خودکار اعمال نمی‌شود.
