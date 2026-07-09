==============================================================================================================
🧠 Freakto Causal/Event Intelligence Core v6.4.0
==============================================================================================================
Status                 : CAUSAL_CONTEXT_READY
Run ID                 : causal_intel_20260709_125408
Symbol / TF            : BTC/USDT | 4h
Collect Live Sources   : True
Sources OK/Failed      : 6 / 0
Trusted Sources OK     : 5
Manual Events Loaded   : 0

Causal Context:
- Primary Cause        : NO_CLEAR_INTERNAL_CAUSE
- Cause Confidence     : LOW
- Catalyst Score       : 58/100
- Event Risk           : MEDIUM
- Technical Conflict   : LOW
- Alignment            : NEUTRAL_DECISION_CONTEXT_ONLY
- Verdict              : CAUSAL_CONTEXT_NEUTRAL

Internal Causes:
- NO_CLEAR_INTERNAL_CAUSE: dir=NEUTRAL | conf=LOW | score=0 | No strong causal pattern detected from current internal features

Source Health:
- coingecko_global: OK | TIER_2_MARKET_AGGREGATOR | dir=NEUTRAL | risk=LOW
- defillama_tvl: OK | TIER_1_PROTOCOL_AGGREGATOR | dir=BULLISH | risk=LOW
- defillama_stablecoins: OK | TIER_1_PROTOCOL_AGGREGATOR | dir=NEUTRAL | risk=LOW
- binance_futures_open_interest: OK | TIER_1_OFFICIAL_EXCHANGE | dir=NEUTRAL | risk=LOW
- binance_futures_premium_funding: OK | TIER_1_OFFICIAL_EXCHANGE | dir=NEUTRAL | risk=LOW
- fred_macro: SKIPPED_NO_KEY | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=LOW
- alternative_fng: OK | TIER_3_SENTIMENT | dir=SENTIMENT_FEAR_RISK | risk=MEDIUM

Source Summaries:
- coingecko_global: Global crypto cap 24h change=0.636%, BTC dominance=56.08%, volume=$63.34B.
- defillama_tvl: DeFi TVL approx 7d change=3.49%, latest=$134.84B.
- defillama_stablecoins: Stablecoin listed circulating supply snapshot=$309.84B across 407 assets.
- binance_futures_open_interest: BTCUSDT open interest snapshot=98804.078 contracts/units on Binance USD-M Futures.
- binance_futures_premium_funding: BTCUSDT funding=0.0064%, mark-index premium=-0.0275%.
- fred_macro: FRED_API_KEY is not configured; macro official-source collection skipped.
- alternative_fng: Fear & Greed=22.0 (Extreme Fear); used only as sentiment/crowding context.

Recommendations:
→ برای خبر/رویدادهای خیلی مهم، data/manual_events.csv را از example بساز و فقط منابع معتبر مثل Fed/SEC/Reuters/official project را وارد کن.
→ در v6.4 نتایج فقط به decision log و research reports اضافه می‌شود؛ هیچ Paper/Live فعال نمی‌شود.

Warnings:
⚠️ Causal Intelligence یک لایه پژوهشی است و به‌تنهایی سیگنال خرید/فروش نمی‌سازد.
⚠️ جمع‌آوری APIهای عمومی ممکن است با rate limit یا محدودیت منطقه‌ای روبه‌رو شود؛ شکست source نباید چرخه Forward را fail کند.
==============================================================================================================