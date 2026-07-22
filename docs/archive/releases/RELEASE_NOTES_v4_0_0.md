# Freakto v4.0.0 — Intelligence Layer

این نسخه یک لایه توضیح‌پذیر و تحلیلی روی موتور تصمیم‌گیری Freakto اضافه می‌کند.

## قابلیت‌های جدید

### Market Narrative Engine
خروجی عددی موتور را به روایت قابل فهم تبدیل می‌کند:
- وضعیت Bias
- کیفیت Confidence
- وضعیت Market Regime
- وضعیت MTF
- نقش Volume و Historical Edge

### Signal Conflict Engine
تضادهای داخلی سیگنال‌ها را تشخیص می‌دهد:
- Bias جهت‌دار در برابر MTF خنثی
- روند قوی بدون Volume
- روند قوی اما Momentum ضعیف
- تضاد Bias با Regime
- Risk Penalty بالا

### Explainable Score Map
نشان می‌دهد هر کامپوننت چه نقشی در تصمیم دارد:
- Trend
- Momentum
- Volume
- Structure
- Regime
- Risk
- Learning Override
- Adaptive
- Historical Edge
- MTF Consensus

### Trade Thesis Generator
برای هر خروجی یک Thesis می‌سازد:
- Bullish Thesis
- Bearish Thesis
- Neutral / Monitor Thesis

و بخش‌های زیر را تولید می‌کند:
- Evidence
- Against / Risks
- Conclusion
- Action Plan

### Intelligence Dashboard
فایل جدید:

```bash
python intelligence_dashboard.py
python intelligence_dashboard.py --send
```

گزارش‌ها در مسیر زیر ذخیره می‌شوند:

```text
logs/intelligence/
```

## فایل‌های جدید

```text
engine/intelligence.py
intelligence_dashboard.py
RELEASE_NOTES_v4_0_0.md
```

## فایل‌های تغییرکرده

```text
monitor.py
portfolio_scanner.py
engine/score.py
engine/portfolio.py
engine/daily_report.py
```

## نکته ایمنی

این نسخه هنوز هیچ تصمیم معاملاتی را خودکار اجرا نمی‌کند. فقط خروجی Decision Engine را توضیح‌پذیرتر و قابل خواندن‌تر می‌کند.
