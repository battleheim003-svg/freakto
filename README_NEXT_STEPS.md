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
