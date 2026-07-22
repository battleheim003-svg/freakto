# Full-History Bootstrap Fix

## مشکل مشاهده‌شده

در اجرای `3Y,5Y,FULL`، پنجره‌های 3Y و 5Y ساخته شدند اما FULL برای BTC، ETH و SOL با پیام زیر شکست خورد:

```text
No provider returned usable historical OHLCV data.
```

علت این بود که بعضی Providerها وقتی زمان درخواست قبل از Listing بازار است، Batch خالی می‌دهند. Fetcher قدیمی با اولین Batch خالی متوقف می‌شد و هرگز تا تاریخ Listing جلو نمی‌رفت.

## اصلاح

- اضافه‌شدن Listing-boundary discovery فقط برای FULL
- Probe مرحله‌ای بازه‌های خالی
- Binary refinement تا یک Timeframe
- شروع مستقل برای هر Symbol
- Fallback Provider بدون Provider mixing
- Replay فقط برای Symbolهای موجود
- وضعیت `PARTIAL_FULL_HISTORY` به‌جای شکست کل آرشیو در نبود بخشی از FULL
- حذف Replay stale در Skip/Empty
- ثبت Build issueها در `archive_build_issues.csv`

## ایمنی

این اصلاح Development Cutoff را تغییر نمی‌دهد و هیچ داده‌ای بعد از Cutoff وارد آرشیو نمی‌شود. Fresh OOS Freeze، Thresholdها، Paper و Live نیز بدون تغییر باقی می‌مانند.
