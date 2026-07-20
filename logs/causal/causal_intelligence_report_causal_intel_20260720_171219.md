==============================================================================================================
🧠 Freakto Causal/Event Intelligence Core v7.2.0
==============================================================================================================
Status                 : CAUSAL_CONTEXT_PARTIAL_SOURCES
Run ID                 : causal_intel_20260720_171219
Symbol / TF            : BTC/USDT | 4h
Collect Live Sources   : True
Sources OK/Failed      : 12 / 2
Trusted Sources OK     : 11
Manual Events Loaded   : 0
Auto Events Loaded     : 8

Causal Context:
- Primary Cause        : MULTI_SOURCE_EVENT_CONSENSUS
- Cause Confidence     : LOW
- Catalyst Score       : 59/100
- Event Risk           : HIGH
- Technical Conflict   : LOW
- Alignment            : NEUTRAL_DECISION_CONTEXT_ONLY
- Verdict              : CAUSAL_HYPOTHESIS_WEAK_EVIDENCE
- Evidence Strength    : 0.5291 (LOW)
- Claim Status         : WEAK_HYPOTHESIS
- Independent Sources  : 7
- Direction Agreement  : 0.6

Alternative Explanations:
- Internal alternative: STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION (structure_score>=10 but volume support is weak/missing)
- Conflicting evidence: Federal Reserve Press Releases RSS: Agencies issue joint statement on handling of highly sensitive information during bank examinations
- Conflicting evidence: Federal Reserve Press Releases RSS: Federal Reserve Board issues enforcement action with former chief lending officer of Heritage State Bank

Internal Causes:
- STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION: dir=NEUTRAL | conf=LOW | score=12 | structure_score>=10 but volume support is weak/missing

Source Health:
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=BEARISH | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=BEARISH | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_REGULATOR | dir=BULLISH | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- coingecko_global: OK | TIER_2_MARKET_AGGREGATOR | dir=BULLISH | risk=LOW
- defillama_tvl: OK | TIER_1_PROTOCOL_AGGREGATOR | dir=BULLISH | risk=LOW
- defillama_stablecoins: OK | TIER_1_PROTOCOL_AGGREGATOR | dir=NEUTRAL | risk=LOW
- binance_futures_open_interest: FAILED | TIER_1_OFFICIAL_EXCHANGE | dir=NEUTRAL | risk=LOW | err=HTTPError: HTTP Error 451: 

Source Summaries:
- auto_events: Federal Reserve Speeches RSS: Speech At the Stanford Institute for Economic Policy Research, Stanford University, Stanford, California
- auto_events: Federal Reserve Press Releases RSS: Agencies issue joint statement on handling of highly sensitive information during bank examinations
- auto_events: Federal Reserve Press Releases RSS: Federal Reserve Board issues enforcement action with former chief lending officer of Heritage State Bank
- auto_events: SEC Press Releases RSS: The Securities and Exchange Commission today proposed Regulation E-Delivery, a new rule that would expand the ability of issuers, broker-dealers, investment advisers, and others to use electronic delivery to satisfy information delivery requirements…
- auto_events: Federal Reserve Speeches RSS: Speech At The Exchequer Club of Washington D.C., Washington, D.C.
- auto_events: Federal Reserve Speeches RSS: Speech At “Next-Gen Financial Inclusion,” the third annual Financial Inclusion Conference hosted by the Federal Reserve Board, Washington, D.C. (via pre-recorded video)
- auto_events: Federal Reserve Press Releases RSS: Minutes of the Board's discount rate meetings on June 8 and June 17, 2026
- auto_events: Federal Reserve Speeches RSS: Speech At “Next-Gen Financial Inclusion,” the third annual Financial Inclusion Conference hosted by the Federal Reserve Board
- coingecko_global: Global crypto cap 24h change=1.098%, BTC dominance=56.67%, volume=$67.9B.
- defillama_tvl: DeFi TVL approx 7d change=3.245%, latest=$141.16B.
- defillama_stablecoins: Stablecoin listed circulating supply snapshot=$309.51B across 410 assets.
- binance_futures_open_interest: 

Recommendations:
→ manual_events.csv فعال است؛ رویدادهای high-impact را با source_url معتبر ادامه بده.
→ auto_events.csv فعال است؛ Automatic Event Collector قبل از Causal Intelligence باید اجرا شود.
→ در v7 نتایج causal/narrative فقط به decision log و research reports اضافه می‌شود؛ هیچ Paper/Live فعال نمی‌شود.

Warnings:
⚠️ Causal Intelligence یک لایه پژوهشی است و به‌تنهایی سیگنال خرید/فروش نمی‌سازد.
⚠️ جمع‌آوری APIهای عمومی ممکن است با rate limit یا محدودیت منطقه‌ای روبه‌رو شود؛ شکست source نباید چرخه Forward را fail کند.
==============================================================================================================