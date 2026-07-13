# Multi-Cycle Historical Archive v2 — Implementation Result

## وضعیت پیاده‌سازی

```text
Status              : IMPLEMENTED_AND_TESTED
Mode                : DEVELOPMENT_RESEARCH_ONLY
New tests           : 16 passed
Reconstructed suite : 109 passed
Compileall          : passed
Promotion applied   : False
Paper/Live enabled  : False
```

## موارد تکمیل‌شده

- آرشیو جداگانه `3Y / 5Y / FULL`
- سقف زمانی مشترک و منجمد Development Cutoff
- عدم تغییر `data/market_replay`
- عدم تغییر Fresh OOS Freeze
- نسخه‌بندی Dataset و SHA-256
- کنترل Provider consistency
- تشخیص Listing/Provider boundary
- Replay جداگانه هر پنجره با `save=False`
- Fixed benchmark بدون تنظیم مجدد Threshold
- Rolling-window validation
- Expanding-window validation بدون هم‌پوشانی Train/Test
- Drift diagnostics با PSI و distribution shift
- Regime stability درون و بین پنجره‌ها
- Fail-Closed در Hash mismatch، Provider mixing، Post-cutoff rows یا Leakage failure

## Smoke Test مصنوعی

برای اطمینان از تولید واقعی تمام خروجی‌ها، سه آرشیو و سه Replay مصنوعی ساخته و بررسی شدند:

```text
Dataset manifests  : 3
Validation status  : COMPLETE_NO_PROMOTION
Rolling windows    : 47
Expanding windows  : 35
Drift diagnostics  : 21
Regime rows        : 8
```

## محدودیت اجرای این محیط

دریافت تاریخچه واقعی صرافی و اجرای Replay چندساله به اتصال اینترنت و Cache محلی فعلی پروژه نیاز دارد. این محیط به دیتاست فعلی 6593 کندلی سیستم کاربر و API صرافی دسترسی نداشت؛ بنابراین نتیجه واقعی 3Y/5Y/FULL باید با دستور Runbook روی سیستم پروژه تولید شود.

این محدودیت روی کامل‌بودن کد و تست‌ها اثر ندارد، اما اعداد واقعی Profit Factor، Expectancy و Drift فقط بعد از اجرای محلی معتبر خواهند بود.
