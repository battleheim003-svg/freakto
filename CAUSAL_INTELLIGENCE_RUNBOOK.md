# Freakto v6.4.0 — Causal/Event Intelligence Core

این ماژول برای پاسخ به سؤال «چرا بازار حرکت کرد؟» اضافه شده است.

## هدف

Freakto از این نسخه فقط Direction/Score را نمی‌بیند؛ برای هر تصمیم یک Context علّی می‌سازد:

- علت داخلی بازار: ساختار، حجم، مومنتوم، regime، volatility، multi-timeframe
- منبع بیرونی معتبر: CoinGecko، DefiLlama، Binance Futures، FRED در صورت API key
- رویداد دستی معتبر: `data/manual_events.csv`
- تضاد بین تکنیکال و علت بازار
- catalyst score و event risk

## منابع داده

نسخه v6.4.0 اولویت را به منابع قابل‌اعتمادتر می‌دهد:

1. **Binance Futures official endpoints** برای funding/open interest همان صرافی.
2. **FRED** برای داده رسمی macro، اگر `FRED_API_KEY` تنظیم شود.
3. **DefiLlama** برای DeFi TVL و stablecoin liquidity.
4. **CoinGecko** برای global crypto market data.
5. **Manual curated events** برای خبرهایی که باید خودت فقط از منابع معتبر وارد کنی.
6. Fear & Greed فقط lower-tier sentiment است و هرگز به‌تنهایی سیگنال نمی‌سازد.

## دستورات

```cmd
python causal_intelligence_dashboard.py --compact
python causal_intelligence_dashboard.py --compact --no-live
python causal_intelligence_dashboard.py --sources
python causal_event_dashboard.py --init
python causal_event_dashboard.py --show
```

## manual_events.csv

برای خبرهای مهم، فایل زیر را بساز:

```cmd
python causal_event_dashboard.py --init
```

ستون‌ها:

```text
timestamp_utc,symbol,event_type,source_name,source_url,impact,direction,confidence,description
```

نمونه:

```text
2026-07-09T12:00:00+00:00,BTC/USDT,macro,Reuters,https://...,high,bullish,medium,Dovish Fed interpretation supports risk assets
```

## ایمنی

v6.4 هیچ Paper Trade جدید، هیچ سفارش واقعی و هیچ Live execution فعال نمی‌کند. این فقط Research/Tagging/Reporting است.


## v6.5.0 — Automatic Event Collector

این نسخه قبل از Causal Intelligence یک مرحله جدید اضافه می‌کند:

```cmd
python automatic_event_collector_dashboard.py --compact
```

خروجی اصلی آن `data/auto_events.csv` است. این فایل از منابع رسمی/معتبر ساخته می‌شود و Causal Intelligence آن را در کنار `manual_events.csv` می‌خواند. این لایه فقط Research است و Paper/Live فعال نمی‌کند.
