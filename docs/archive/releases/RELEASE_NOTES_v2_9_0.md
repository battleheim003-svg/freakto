# Freakto v2.9.0 — Daily AI Report Engine

## هدف
در v2.9 خروجی Portfolio Scanner از یک جدول تحلیلی به یک گزارش مدیریتی قابل‌خواندن تبدیل شد.

## قابلیت‌های جدید

### Daily AI Report Engine
فایل جدید: `engine/daily_report.py`

این موتور خروجی Portfolio Scanner و Market Breadth را به بخش‌های زیر تبدیل می‌کند:

- Executive Summary
- Market Context
- Candidates
- Risk Notes
- Action Plan

### ذخیره گزارش روزانه
هر اجرای `portfolio_scanner.py` یک گزارش Markdown در مسیر زیر ذخیره می‌کند:

```text
logs/reports/daily_report_YYYYMMDD_HHMMSS.md
```

### ارسال تلگرام
وقتی دستور زیر اجرا شود:

```bash
python portfolio_scanner.py --send
```

دو پیام ارسال می‌شود:

1. خلاصه Portfolio Scanner
2. Daily AI Report

### CSV ارتقا یافت
در `logs/portfolio_scans.csv` ستون `daily_report_file` اضافه شد تا هر اسکن به گزارش مدیریتی همان اجرا وصل شود.

## تست

```bash
python portfolio_scanner.py
python portfolio_scanner.py --send
```

## نکته
این نسخه به API هوش مصنوعی خارجی وابسته نیست. گزارش به صورت deterministic با داده‌های داخلی Freakto ساخته می‌شود، اما معماری طوری طراحی شده که بعداً بتوان آن را به LLM خارجی هم وصل کرد.
