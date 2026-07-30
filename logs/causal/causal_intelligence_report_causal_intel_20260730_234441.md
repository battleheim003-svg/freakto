==============================================================================================================
🧠 Freakto Causal/Event Intelligence Core v7.2.0
==============================================================================================================
Status                 : CAUSAL_CONTEXT_PARTIAL_SOURCES
Run ID                 : causal_intel_20260730_234441
Symbol / TF            : BTC/USDT | 4h
Collect Live Sources   : True
Sources OK/Failed      : 9 / 2
Trusted Sources OK     : 8
Manual Events Loaded   : 0
Auto Events Loaded     : 5

Causal Context:
- Primary Cause        : MULTI_SOURCE_EVENT_CONSENSUS
- Cause Confidence     : MEDIUM
- Catalyst Score       : 40/100
- Event Risk           : HIGH
- Technical Conflict   : LOW
- Alignment            : NEUTRAL_DECISION_CONTEXT_ONLY
- Verdict              : CAUSAL_CONTEXT_NEUTRAL
- Evidence Strength    : 0.6469 (MEDIUM)
- Claim Status         : PLAUSIBLE_HYPOTHESIS
- Independent Sources  : 6
- Direction Agreement  : 0.6667

Alternative Explanations:
- Internal alternative: STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION (structure_score>=10 but volume support is weak/missing)
- Conflicting evidence: Global crypto cap 24h change=1.317%, BTC dominance=56.64%, volume=$58.72B.
- The move may be explained by broad market beta or liquidity rather than the named event.

Internal Causes:
- STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION: dir=NEUTRAL | conf=LOW | score=12 | structure_score>=10 but volume support is weak/missing

Source Health:
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=BEARISH | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=BEARISH | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_REGULATOR | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_REGULATOR | dir=NEUTRAL | risk=HIGH
- coingecko_global: OK | TIER_2_MARKET_AGGREGATOR | dir=BULLISH | risk=LOW
- defillama_tvl: OK | TIER_1_PROTOCOL_AGGREGATOR | dir=NEUTRAL | risk=LOW
- defillama_stablecoins: OK | TIER_1_PROTOCOL_AGGREGATOR | dir=NEUTRAL | risk=LOW
- binance_futures_open_interest: FAILED | TIER_1_OFFICIAL_EXCHANGE | dir=NEUTRAL | risk=LOW | err=HTTPError: HTTP Error 451: 
- binance_futures_premium_funding: FAILED | TIER_1_OFFICIAL_EXCHANGE | dir=NEUTRAL | risk=LOW | err=HTTPError: HTTP Error 451: 
- fred_macro: SKIPPED_NO_KEY | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=LOW
- alternative_fng: OK | TIER_3_SENTIMENT | dir=NEUTRAL | risk=LOW

Source Summaries:
- auto_events: Federal Reserve Press Releases RSS: Federal Reserve Board issues enforcement actions with former employee of Regions Bank and former employee of First Interstate Bank
- auto_events: Federal Reserve Press Releases RSS: Federal Reserve Board issues enforcement action with Iuka Bancshares, Inc. and The Iuka State Bank
- auto_events: SEC Press Releases RSS: The Securities and Exchange Commission announced that the Small Business Capital Formation Advisory Committee meeting held on July 21, 2026, will reconvene August 6, 2026, at 1 p.m. ET, virtually, on SEC.gov. The committee will…
- auto_events: Federal Reserve Press Releases RSS: Federal Reserve issues FOMC statement
- auto_events: SEC Press Releases RSS: The Securities and Exchange Commission released a report to Congress today highlighting policy recommendations from the SEC’s 45th Annual Government-Business Forum on Small Business Capital Formation. The report provides a summary of the forum…
- coingecko_global: Global crypto cap 24h change=1.317%, BTC dominance=56.64%, volume=$58.72B.
- defillama_tvl: DeFi TVL approx 7d change=-0.501%, latest=$142.44B.
- defillama_stablecoins: Stablecoin listed circulating supply snapshot=$306.83B across 413 assets.
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