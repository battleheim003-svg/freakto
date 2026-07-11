# Freakto — Crypto Research & Decision Intelligence Platform

Freakto یک سیستم پژوهشی برای تحلیل بازار کریپتو، ساخت تصمیم، ارزیابی تاریخی، Forward Test، Paper Trading و تحلیل علت‌های حرکت بازار است.

هدف پروژه تولید سیگنال کور نیست. هر تصمیم باید از چند لایه عبور کند:

```text
Market Data
→ Technical Features
→ Decision Engine
→ Regime / Risk / Actionability
→ Event & Narrative Intelligence
→ Root Cause & Evidence Graph
→ Historical Replay / Forward Validation
→ Shadow / Paper Review
```

## وضعیت ایمنی

- اجرای خودکار Live order در پروژه فعال نیست.
- Backtest و Market Replay جای Forward Test و Paper Trading را نمی‌گیرند.
- هیچ نتیجه‌ای سود را تضمین نمی‌کند.
- ورود به پول واقعی فقط بعد از داده‌ی کافی تاریخی، Forward و Paper قابل بررسی است.

## قابلیت‌های اصلی

- دریافت OHLCV از چند صرافی با fallback؛
- Decision Engine برای LONG، SHORT و NEUTRAL؛
- Trend، Momentum، Volume، Structure، Risk و Regime scoring؛
- Portfolio Scanner و Multi-Timeframe analysis؛
- Historical Backtest، Walk-Forward و Gate Simulator؛
- Market Replay چندساله و کندل‌به‌کندل با کنترل Lookahead؛
- Forward Test و Decision Evaluation؛
- Shadow Gates و Regime-specific validation؛
- Paper Trading جدا از Live؛
- Automatic Event Collector، Market Narrative و Causal Intelligence؛
- Root Cause Discovery، Root Cause Forward Validation و Sample Tracking؛
- Evidence Graph برای اتصال منبع شواهد به علت و Outcome؛
- Research Suite، Validation Suite و Live Readiness checks؛
- GitHub Actions برای جمع‌آوری Forward data و اجرای Workflowهای تحقیقاتی.

## نصب

پایتون 3.10 یا بالاتر:

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

فایل `.env` حاوی Token و API Key است و نباید روی GitHub قرار بگیرد.

## اجرای روزمره‌ی پایه

یک تصمیم جدید:

```cmd
python -X utf8 monitor.py --once
```

اسکن پورتفو در حالت Paper Gate:

```cmd
python -X utf8 portfolio_scanner.py --paper
```

چرخه Forward:

```cmd
python -X utf8 forward_test_dashboard.py --cycle --validate --continue-on-error
```

Research Suite:

```cmd
python -X utf8 freakto_research_suite_dashboard.py
```

## Market Replay v10

وضعیت داده‌های محلی:

```cmd
python -X utf8 market_replay_dashboard.py --status --compact
```

ساخت سه سال داده و Replay:

```cmd
python -X utf8 market_replay_dashboard.py --full --symbols BTC/USDT,ETH/USDT,SOL/USDT --timeframe 4h --years 3 --step 1
```

راهنمای کامل:

```text
MARKET_REPLAY_RUNBOOK.md
```

## مسیرهای مهم

```text
engine/                         موتورهای تحلیل و اعتبارسنجی
logs/                           خروجی‌های Research/Forward/Paper
history/                        پایگاه‌های داده محلی
scripts/                        ابزارهای GitHub Actions و عملیات
.github/workflows/              Workflowهای خودکار
data/market_replay/             Cache تاریخی تولیدشده در v10
data/manual_events.csv          رویدادهای curated اختیاری
```

## وضعیت فعلی پروژه

Freakto در فاز **Research, Historical Replay, Forward Validation و Paper Evaluation** است. وجود ماژول‌های پیشرفته به معنی آماده‌بودن Live نیست؛ کیفیت نهایی به تعداد نمونه، ثبات در دوره‌های مختلف بازار، هزینه‌ی معامله و نتیجه‌ی Forward/Paper بستگی دارد.


## Replay Score Calibration (v10.2)

```cmd
python -X utf8 replay_score_calibration_dashboard.py --compact
```

This research-only lab checks score monotonicity, component-feature attribution, interactions and symbol/regime/side stability without changing Paper or Live settings.
