# Freakto v4.6.1 — Breadth Clarity Patch

این نسخه یک Patch کوچک اما مهم برای خوانایی خروجی Market Breadth است.

## مشکل نسخه قبل

در v4.6 وقتی تمام نمادها خنثی بودند، خروجی چیزی شبیه این می‌داد:

```text
Market Mode : NEUTRAL
Strength    : 100/100
Avg Opp     : 1.5
```

از نظر محاسباتی `Strength=100` یعنی همه نمادها روی حالت خنثی توافق داشتند، اما از نظر کاربر ممکن بود این برداشت ایجاد شود که بازار یا فرصت معاملاتی خیلی قوی است.

## اصلاح v4.6.1

از این نسخه به بعد `Strength` به دو مفهوم جدا تقسیم شد:

```text
Agreement   : 100/100
Opp Strength: 2/100
```

### Market Agreement

یعنی بازار چقدر روی یک حالت جمعی توافق دارد.

مثلاً:

```text
Neutral 100%
```

یعنی همه نمادها خنثی‌اند، نه اینکه فرصت قوی وجود دارد.

### Opportunity Strength

یعنی قدرت واقعی فرصت‌های معاملاتی در پورتفو.

اگر بازار خنثی باشد ولی Opportunity پایین باشد، خروجی حالا واضح می‌گوید:

```text
Market Agreement بالا روی خنثی بودن است، اما Opportunity Strength پایین است.
```

## فایل‌های تغییرکرده

```text
engine/market_breadth.py
engine/daily_report.py
engine/intelligence.py
engine/portfolio.py
engine/performance.py
portfolio_scanner.py
intelligence_dashboard.py
RELEASE_NOTES_v4_6_1.md
```

## خروجی جدید مورد انتظار

```text
Market Mode : NEUTRAL
Risk Tone   : MONITOR
Agreement   : 100/100
Opp Strength: 2/100
Avg Opp     : 1.5
```

## هدف

جلوگیری از برداشت اشتباه از `Strength=100` در بازارهای کاملاً خنثی.

این نسخه هیچ منطق معاملاتی اصلی را تغییر نمی‌دهد؛ فقط شفافیت خروجی و لاگ‌ها را بهتر می‌کند.
