# معاملات آزمایشی Freakto

این بخش تنها برای جمع‌آوری داده پژوهشی و شبیه‌سازی است. سه invariant همیشه برقرار است: `live_orders_enabled=false`، `real_capital_enabled=false` و `allocation_pct=0.0`.

شروع سریع: `start_paper_trading.bat`. وضعیت: `show_paper_status.bat`. توقف: `stop_paper_trading.bat`.

رابط canonical مستقل از ویندوز:

```text
freakto paper preflight
freakto paper arm-research
freakto paper cycle
freakto paper status
freakto paper dashboard
freakto paper disarm
```

فایل‌های Batch بالا wrapper همین رابط هستند. فرمان‌های مستقیم Python قدیمی فعلاً برای
سازگاری حفظ شده‌اند، ولی مسیر توصیه‌شده برای عملیات جدید `freakto paper ...` است.
