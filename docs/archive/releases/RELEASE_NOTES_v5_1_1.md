# Freakto v5.1.1 — Windows UTF-8 Forward Runner Patch

## هدف

این Patch خطای Windows `UnicodeEncodeError: 'charmap' codec can't encode` را در اجرای چرخه Forward Test رفع می‌کند.

در v5.1 وقتی `forward_test_dashboard.py --cycle` ماژول‌هایی مثل `monitor.py`، `portfolio_scanner.py`، `decision_evaluator.py` و `validation_suite_dashboard.py` را به‌صورت subprocess اجرا می‌کرد، خروجی فارسی و emoji داخل pipe ویندوز ممکن بود با code page قدیمی مثل `cp1252` encode شود و child process قبل از پایان کار crash کند.

## تغییرات

- `engine/forward_test.py`
  - نسخه به `v5.1.1` ارتقا یافت.
  - همه child Python commandها با `-X utf8` اجرا می‌شوند.
  - environment child processها شامل این مقادیر می‌شود:
    - `PYTHONUTF8=1`
    - `PYTHONIOENCODING=utf-8`
  - فایل‌های batch تولیدی حالا UTF-8-safe هستند و `chcp 65001` تنظیم می‌کنند.

- `forward_test_dashboard.py`
  - خروجی خود داشبورد هم با `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` ایمن شد.

## نتیجه مورد انتظار

این دستور دیگر نباید روی فارسی/emoji crash کند:

```cmd
python forward_test_dashboard.py --cycle --validate --continue-on-error --send
```

در خروجی Forward Test ممکن است بعضی taskها به دلایل واقعی بازار، اینترنت، API یا logic داخلی fail شوند؛ اما دیگر نباید خطای `UnicodeEncodeError` یا `cp1252` مربوط به چاپ فارسی/emoji دیده شود.

## نکته ویندوز

برای ساخت batchهای جدید:

```cmd
python forward_test_dashboard.py --write-bat
```

سپس:

```cmd
run_forward_test_cycle.bat
```
