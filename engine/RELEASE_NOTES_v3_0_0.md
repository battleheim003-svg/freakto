# Freakto v3.0.0 — Performance & Learning Dashboard

## هدف نسخه

این نسخه Freakto را وارد فاز «یادگیری از عملکرد» می‌کند. تا قبل از v3.0، سیستم تصمیم می‌گرفت، پورتفو را اسکن می‌کرد و گزارش می‌ساخت. از این نسخه به بعد، سیستم لاگ‌های خودش را می‌خواند و یک داشبورد عملکرد تولید می‌کند.

## قابلیت‌های جدید

### Performance & Learning Engine

فایل جدید:

```text
engine/performance.py
```

این ماژول از فایل‌های زیر داده می‌خواند:

```text
logs/decisions.csv
logs/decision_evaluations.csv
logs/portfolio_scans.csv
logs/reports/*.md
```

و بخش‌های زیر را تولید می‌کند:

- Decision Log Summary
- Decision Evaluation Summary
- Portfolio Scanner Summary
- Daily Reports Summary
- Learning Recommendations

### Performance Dashboard CLI

فایل جدید:

```text
performance_dashboard.py
```

اجرا:

```cmd
python performance_dashboard.py
```

ارسال به تلگرام:

```cmd
python performance_dashboard.py --send
```

### ذخیره گزارش عملکرد

گزارش‌ها در مسیر زیر ذخیره می‌شوند:

```text
logs/performance/performance_report_YYYYMMDD_HHMMSS.md
```

## چرا این نسخه مهم است؟

از این نسخه به بعد Freakto فقط تحلیل نمی‌کند؛ از تاریخچه خودش هم گزارش می‌گیرد. این پایه لازم برای مراحل بعدی مثل Parameter Optimization، Self-Learning و ML Probability Engine است.

## تست پیشنهادی

```cmd
python decision_evaluator.py
python portfolio_scanner.py
python performance_dashboard.py
```
