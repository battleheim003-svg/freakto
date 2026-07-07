# Freakto v6.0 — Research Robustness & Intelligence Suite

این نسخه ۱۱ مسیر بهبود را به شکل research-only وارد Freakto می‌کند. هیچ بخش این نسخه سفارش واقعی ارسال نمی‌کند و Paper Trade جدید نمی‌سازد.

## اجرای همه بخش‌ها

```cmd
python freakto_research_suite_dashboard.py
```

ارسال خلاصه به تلگرام:

```cmd
python freakto_research_suite_dashboard.py --send
```

## داشبوردهای جداگانه

```cmd
python gate_robustness_dashboard.py --horizon 24h --min-samples 30
python cost_adjusted_backtest_dashboard.py --fee-bps 10 --slippage-bps 5
python meta_labeling_dashboard.py --horizon 24h
python ensemble_explainability_dashboard.py
python data_enrichment_dashboard.py
python regime_research_dashboard.py
python cross_exchange_validation_dashboard.py
python research_db_dashboard.py
python pipeline_health_dashboard.py
python statistical_readiness_dashboard.py
python position_sizing_lab_dashboard.py
python airdrop_shadow_dashboard.py
```

## خروجی‌ها

```text
logs/research/v6_suite/*.json
logs/research/v6_suite/*.md
logs/research/freakto_research.db
logs/research_dashboard/index.html
```

## ۱۱ بخش پیاده‌سازی‌شده

1. Gate Robustness / Walk-forward / Multiple-testing penalty / Embargo proxy
2. Cost-adjusted Backtest با Fee و Slippage
3. Meta-labeling Research Layer
4. Ensemble و Explainability برای score و componentها
5. Data Enrichment Readiness برای on-chain/derivatives/microstructure
6. Regime Research رسمی‌تر
7. Cross-exchange validation بر اساس provider
8. SQLite Research DB
9. Static HTML Dashboard و Pipeline Health Monitoring
10. Strict Statistical Readiness شامل CI، t-stat، regime coverage و BTC beta check
11. Position Sizing Lab و Airdrop Shadow Research

## محدودیت مهم

خروجی‌های v6 برای تصمیم live کافی نیستند. هر gate یا مدل باید بعد از Backtest، در Shadow/Forward نمونه کافی بگیرد.
