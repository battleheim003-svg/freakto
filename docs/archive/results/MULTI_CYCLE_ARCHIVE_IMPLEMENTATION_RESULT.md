# Multi-Cycle Historical Archive v2.1 — Implementation Result

## وضعیت

```text
Status                    : IMPLEMENTED_AND_TESTED
Historical Store Version  : v10.0.2
Multi-Cycle Version       : 2.1.0
New regression tests      : 5 passed
Reconstructed suite       : 114 passed
Compile                    : passed
Promotion applied         : False
Paper/Live enabled        : False
```

نسخه کامل کاربر قبل از این اصلاح 131 تست داشت؛ پس انتظار محلی پس از جایگزینی فایل‌ها `136 passed` است.

## موارد تکمیل‌شده

- کشف خودکار Listing boundary برای FULL
- عبور مرحله‌ای از Batchهای خالی قبل از Listing
- پالایش مرز اولین داده تا دقت یک کندل
- شروع مستقل BTC/ETH/SOL
- Fallback Provider بدون ادغام Providerها
- ثبت تعداد Probe و منبع Listing boundary در Manifest
- Replay فقط با Symbolهای Archive‌شده و تأییدشده
- `PARTIAL_FULL_HISTORY` برای FULL ناقص ولی قابل استفاده
- Fail-Closed برای Hash، Provider mixing، Cutoff و Leakage failure
- حذف Replay قدیمی در خروجی خالی یا Skip
- خروجی `archive_build_issues.csv`

## محدودیت محیط اجرا

این محیط دسترسی اینترنتی به API صرافی و فایل‌های Market Replay کامل سیستم کاربر نداشت. رفتار Listing bootstrap، Provider fallback، Partial FULL و stale-output cleanup با Exchangeهای مصنوعی و تست‌های رگرسیون بررسی شد. اعداد واقعی FULL پس از اجرای دستور Runbook روی سیستم کاربر تولید می‌شوند.
