==============================================================================================================
🧠 Freakto Causal/Event Intelligence Core v7.2.0
==============================================================================================================
Status                 : CAUSAL_CONTEXT_PARTIAL_SOURCES
Run ID                 : causal_intel_20260730_094455
Symbol / TF            : BTC/USDT | 4h
Collect Live Sources   : True
Sources OK/Failed      : 7 / 2
Trusted Sources OK     : 6
Manual Events Loaded   : 0
Auto Events Loaded     : 3

Causal Context:
- Primary Cause        : AUTO_EVENTS_CONTEXT
- Cause Confidence     : MEDIUM
- Catalyst Score       : 71/100
- Event Risk           : HIGH
- Technical Conflict   : LOW
- Alignment            : NEUTRAL_DECISION_CONTEXT_ONLY
- Verdict              : CAUSAL_CONTEXT_PROMISING_BUT_INCOMPLETE
- Evidence Strength    : 0.821 (STRONG)
- Claim Status         : SUPPORTED_HYPOTHESIS
- Independent Sources  : 6
- Direction Agreement  : 1.0

Alternative Explanations:
- Internal alternative: STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION (structure_score>=10 but volume support is weak/missing)
- The move may be explained by broad market beta or liquidity rather than the named event.
- The observed event and price move may be correlated without a causal relationship.

Internal Causes:
- STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION: dir=NEUTRAL | conf=LOW | score=12 | structure_score>=10 but volume support is weak/missing

Source Health:
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_REGULATOR | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_REGULATOR | dir=BULLISH | risk=HIGH
- coingecko_global: OK | TIER_2_MARKET_AGGREGATOR | dir=NEUTRAL | risk=LOW
- defillama_tvl: OK | TIER_1_PROTOCOL_AGGREGATOR | dir=NEUTRAL | risk=LOW
- defillama_stablecoins: OK | TIER_1_PROTOCOL_AGGREGATOR | dir=NEUTRAL | risk=LOW
- binance_futures_open_interest: FAILED | TIER_1_OFFICIAL_EXCHANGE | dir=NEUTRAL | risk=LOW | err=HTTPError: HTTP Error 451: 
- binance_futures_premium_funding: FAILED | TIER_1_OFFICIAL_EXCHANGE | dir=NEUTRAL | risk=LOW | err=HTTPError: HTTP Error 451: 
- fred_macro: SKIPPED_NO_KEY | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=LOW
- alternative_fng: OK | TIER_3_SENTIMENT | dir=NEUTRAL | risk=LOW

Source Summaries:
- auto_events: Federal Reserve Press Releases RSS: Federal Reserve issues FOMC statement
- auto_events: SEC Press Releases RSS: The Securities and Exchange Commission released a report to Congress today highlighting policy recommendations from the SEC’s 45th Annual Government-Business Forum on Small Business Capital Formation. The report provides a summary of the forum…
- auto_events: SEC Press Releases RSS: The Securities and Exchange Commission announced today that it will host a roundtable on Sept. 17, 2026, to discuss moving towards 24-hour trading in the U.S. equity markets, including preparations to support overnight trading, operations and resiliency…
- coingecko_global: Global crypto cap 24h change=-0.204%, BTC dominance=56.64%, volume=$66.23B.
- defillama_tvl: DeFi TVL approx 7d change=-0.948%, latest=$141.82B.
- defillama_stablecoins: Stablecoin listed circulating supply snapshot=$307.32B across 413 assets.
- binance_futures_open_interest: 
- binance_futures_premium_funding: 
- fred_macro: FRED_API_KEY is not configured; macro official-source collection skipped.
- alternative_fng: Fear & Greed=28.0 (Fear); used only as sentiment/crowding context.

Recommendations:
→ manual_events.csv فعال است؛ رویدادهای high-impact را با source_url معتبر ادامه بده.
→ auto_events.csv فعال است؛ Automatic Event Collector قبل از Causal Intelligence باید اجرا شود.
→ در v7 نتایج causal/narrative فقط به decision log و research reports اضافه می‌شود؛ هیچ Paper/Live فعال نمی‌شود.

Warnings:
⚠️ Causal Intelligence یک لایه پژوهشی است و به‌تنهایی سیگنال خرید/فروش نمی‌سازد.
⚠️ جمع‌آوری APIهای عمومی ممکن است با rate limit یا محدودیت منطقه‌ای روبه‌رو شود؛ شکست source نباید چرخه Forward را fail کند.
==============================================================================================================