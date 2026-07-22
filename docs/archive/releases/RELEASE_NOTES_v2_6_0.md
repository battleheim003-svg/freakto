# Freakto v2.6.0 - Portfolio Quality Upgrade

## هدف
این نسخه کیفیت خروجی Portfolio Scanner را بهتر می‌کند. به جای اینکه فقط نمادها بر اساس Score خام مرتب شوند، یک Opportunity Score چندعاملی ساخته می‌شود.

## قابلیت‌ها

### Opportunity Ranking Engine v2
رتبه‌بندی جدید از این عوامل استفاده می‌کند:
- Decision Score
- Confidence
- Historical Edge
- Multi-Timeframe Consensus
- Risk Quality
- Actionability

### Smart Watchlist
نمادها به جای یک جدول ساده، در چند بخش نمایش داده می‌شوند:
- Elite Opportunities
- Actionable Candidates
- Smart Watchlist
- Closest / Monitor Candidates

### Elite Opportunity Filter
فقط وقتی یک نماد به سطح Elite می‌رسد که:
- جهت‌دار باشد
- Opportunity Score بالا داشته باشد
- Confidence کافی داشته باشد
- MTF با آن هم‌راستا باشد

### Portfolio Telegram Report v2
گزارش تلگرام خلاصه‌تر و تصمیم‌محورتر شده است.

## تست
```bash
python portfolio_scanner.py
python portfolio_scanner.py --send
```
