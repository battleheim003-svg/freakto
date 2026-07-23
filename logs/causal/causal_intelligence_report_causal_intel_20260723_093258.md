==============================================================================================================
🧠 Freakto Causal/Event Intelligence Core v7.2.0
==============================================================================================================
Status                 : CAUSAL_CONTEXT_PARTIAL_SOURCES
Run ID                 : causal_intel_20260723_093258
Symbol / TF            : BTC/USDT | 4h
Collect Live Sources   : True
Sources OK/Failed      : 9 / 2
Trusted Sources OK     : 8
Manual Events Loaded   : 0
Auto Events Loaded     : 5

Causal Context:
- Primary Cause        : MULTI_SOURCE_EVENT_CONSENSUS
- Cause Confidence     : LOW
- Catalyst Score       : 28/100
- Event Risk           : HIGH
- Technical Conflict   : LOW
- Alignment            : NEUTRAL_DECISION_CONTEXT_ONLY
- Verdict              : CAUSAL_HYPOTHESIS_WEAK_EVIDENCE
- Evidence Strength    : 0.5347 (LOW)
- Claim Status         : WEAK_HYPOTHESIS
- Independent Sources  : 7
- Direction Agreement  : 0.6

Alternative Explanations:
- Internal alternative: NO_CLEAR_INTERNAL_CAUSE (No strong causal pattern detected from current internal features)
- Conflicting evidence: SEC Press Releases RSS: The Securities and Exchange Commission today proposed Regulation E-Delivery, a new rule that would expand the ability of issuers, broker-dealers, investment
- Conflicting evidence: DeFi TVL approx 7d change=1.756%, latest=$143.05B.

Internal Causes:
- NO_CLEAR_INTERNAL_CAUSE: dir=NEUTRAL | conf=LOW | score=0 | No strong causal pattern detected from current internal features

Source Health:
- auto_events: OK | TIER_1_OFFICIAL_REGULATOR | dir=BEARISH | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=BEARISH | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=BEARISH | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_REGULATOR | dir=BULLISH | risk=HIGH
- coingecko_global: OK | TIER_2_MARKET_AGGREGATOR | dir=NEUTRAL | risk=LOW
- defillama_tvl: OK | TIER_1_PROTOCOL_AGGREGATOR | dir=BULLISH | risk=LOW
- defillama_stablecoins: OK | TIER_1_PROTOCOL_AGGREGATOR | dir=NEUTRAL | risk=LOW
- binance_futures_open_interest: FAILED | TIER_1_OFFICIAL_EXCHANGE | dir=NEUTRAL | risk=LOW | err=HTTPError: HTTP Error 451: 
- binance_futures_premium_funding: FAILED | TIER_1_OFFICIAL_EXCHANGE | dir=NEUTRAL | risk=LOW | err=HTTPError: HTTP Error 451: 
- fred_macro: SKIPPED_NO_KEY | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=LOW
- alternative_fng: OK | TIER_3_SENTIMENT | dir=NEUTRAL | risk=LOW

Source Summaries:
- auto_events: SEC Press Releases RSS: The Securities and Exchange Commission today announced that Sam Waldon, Principal Deputy Director of the Division of Enforcement, will depart the agency on July 31, 2026, after more than 14 years at the SEC. He will be succeeded as Principal Deputy…
- auto_events: Federal Reserve Speeches RSS: Speech At the Stanford Institute for Economic Policy Research, Stanford University, Stanford, California
- auto_events: Federal Reserve Press Releases RSS: Agencies issue joint statement on handling of highly sensitive information during bank examinations
- auto_events: Federal Reserve Press Releases RSS: Federal Reserve Board issues enforcement action with former chief lending officer of Heritage State Bank
- auto_events: SEC Press Releases RSS: The Securities and Exchange Commission today proposed Regulation E-Delivery, a new rule that would expand the ability of issuers, broker-dealers, investment advisers, and others to use electronic delivery to satisfy information delivery requirements…
- coingecko_global: Global crypto cap 24h change=-0.188%, BTC dominance=56.66%, volume=$59.97B.
- defillama_tvl: DeFi TVL approx 7d change=1.756%, latest=$143.05B.
- defillama_stablecoins: Stablecoin listed circulating supply snapshot=$310.06B across 411 assets.
- binance_futures_open_interest: 
- binance_futures_premium_funding: 
- fred_macro: FRED_API_KEY is not configured; macro official-source collection skipped.
- alternative_fng: Fear & Greed=31.0 (Fear); used only as sentiment/crowding context.

Recommendations:
→ manual_events.csv فعال است؛ رویدادهای high-impact را با source_url معتبر ادامه بده.
→ auto_events.csv فعال است؛ Automatic Event Collector قبل از Causal Intelligence باید اجرا شود.
→ در v7 نتایج causal/narrative فقط به decision log و research reports اضافه می‌شود؛ هیچ Paper/Live فعال نمی‌شود.

Warnings:
⚠️ Causal Intelligence یک لایه پژوهشی است و به‌تنهایی سیگنال خرید/فروش نمی‌سازد.
⚠️ جمع‌آوری APIهای عمومی ممکن است با rate limit یا محدودیت منطقه‌ای روبه‌رو شود؛ شکست source نباید چرخه Forward را fail کند.
==============================================================================================================