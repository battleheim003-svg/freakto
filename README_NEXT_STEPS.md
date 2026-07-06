# Freakto Next Steps — v5.2

## وضعیت فعلی

پروژه وارد فاز Forward Test Collection شده و v5.2 امکان اجرای رایگان روی GitHub Actions را اضافه می‌کند.

## قدم بعدی عملی

1. پروژه را روی GitHub آپلود کن.
2. Secretهای Telegram را در GitHub Actions تنظیم کن.
3. Workflow را دستی یک بار اجرا کن.
4. مطمئن شو branch `data-logs` ساخته شده و لاگ‌ها در آن ذخیره می‌شوند.
5. اجازه بده workflow هر 4 ساعت اجرا شود.

## راهنمای کامل

فایل زیر را بخوان:

```text
GITHUB_ACTIONS_SETUP_FA.md
```

## هدف جمع‌آوری داده

```text
Complete evaluations >= 100
Closed paper trades >= 30
Regime-labeled samples >= 30
Forward days >= 30
```

تا وقتی این معیارها کامل نشده‌اند، پروژه همچنان نباید وارد پول واقعی شود.

## دستور دستی لوکال

```bash
python -X utf8 forward_test_dashboard.py --cycle --validate --continue-on-error --send
```

## اجرای خودکار رایگان

GitHub Actions workflow:

```text
.github/workflows/freakto-forward-test.yml
```

این workflow هر 4 ساعت اجرا می‌شود و لاگ‌ها را در branch `data-logs` ذخیره می‌کند.

---

## v5.2.1 — بعد از فعال شدن GitHub Actions

اگر `Freakto Forward Test Collector` روی GitHub سبز شده، قدم بعدی نصب v5.2.1 است.

این نسخه دو کار عملیاتی اضافه می‌کند:

```text
1. Health Check Workflow برای چک سبک وضعیت بدون اجرای چرخه کامل
2. GitHub Actions Health Summary برای دیدن وضعیت در صفحه Summary هر run
```

بعد از push کردن v5.2.1 به GitHub، در تب Actions باید دو workflow داشته باشی:

```text
Freakto Forward Test Collector
Freakto Health Check
```

Workflow اصلی هر ۴ ساعت دیتا جمع می‌کند. Health Check فقط وضعیت را از لاگ‌های ذخیره‌شده می‌خواند.

فعلاً هدف پروژه همچنان جمع‌آوری داده است، نه live trading:

```text
30 Forward Days
100 Complete Evaluations
30 Closed Paper Trades
30 Regime-labeled Samples
```

## v5.2.3 GitHub Actions Restore Hotfix
اگر در Health Check خطای زیر دیدی:

```text
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb6
```

نسخه v5.2.3 را نصب کن. این نسخه `scripts/github_actions_restore_logs.py` را اصلاح می‌کند تا خروجی باینری `git archive` به اشتباه به‌صورت متن UTF-8 decode نشود.
