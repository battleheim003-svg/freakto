==============================================================================================================
🧠 Freakto Causal/Event Intelligence Core v7.2.0
==============================================================================================================
Status                 : CAUSAL_CONTEXT_WITH_BLOCKERS
Run ID                 : causal_intel_20260715_201948
Symbol / TF            : BTC/USDT | 4h
Collect Live Sources   : True
Sources OK/Failed      : 13 / 2
Trusted Sources OK     : 12
Manual Events Loaded   : 0
Auto Events Loaded     : 9

Causal Context:
- Primary Cause        : MULTI_SOURCE_EVENT_CONSENSUS
- Cause Confidence     : HIGH
- Catalyst Score       : 46/100
- Event Risk           : HIGH
- Technical Conflict   : HIGH
- Alignment            : CONFLICT_WITH_EXTERNAL_CONTEXT
- Verdict              : CAUSAL_CONFLICT_RESEARCH_ONLY
- Evidence Strength    : 0.6353 (MEDIUM)
- Claim Status         : PLAUSIBLE_HYPOTHESIS
- Independent Sources  : 7
- Direction Agreement  : 0.6667

Alternative Explanations:
- Internal alternative: STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION (structure_score>=10 but volume support is weak/missing)
- Conflicting evidence: DeFi TVL approx 7d change=3.495%, latest=$141.24B.
- The move may be explained by broad market beta or liquidity rather than the named event.

Internal Causes:
- STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION: dir=LONG | conf=LOW | score=12 | structure_score>=10 but volume support is weak/missing

Source Health:
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=BEARISH | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_REGULATOR | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=BEARISH | risk=HIGH
- coingecko_global: OK | TIER_2_MARKET_AGGREGATOR | dir=NEUTRAL | risk=LOW
- defillama_tvl: OK | TIER_1_PROTOCOL_AGGREGATOR | dir=BULLISH | risk=LOW
- defillama_stablecoins: OK | TIER_1_PROTOCOL_AGGREGATOR | dir=NEUTRAL | risk=LOW

Source Summaries:
- auto_events: Federal Reserve Speeches RSS: Speech At The Exchequer Club of Washington D.C., Washington, D.C.
- auto_events: Federal Reserve Speeches RSS: Speech At “Next-Gen Financial Inclusion,” the third annual Financial Inclusion Conference hosted by the Federal Reserve Board, Washington, D.C. (via pre-recorded video)
- auto_events: Federal Reserve Press Releases RSS: Minutes of the Board's discount rate meetings on June 8 and June 17, 2026
- auto_events: Federal Reserve Speeches RSS: Speech At “Next-Gen Financial Inclusion,” the third annual Financial Inclusion Conference hosted by the Federal Reserve Board
- auto_events: Federal Reserve Speeches RSS: Speech At the New York Association for Business Economics, New York, New York
- auto_events: Federal Reserve Speeches RSS: Speech At a Bank Policy Institute London Conference, London, United Kingdom
- auto_events: SEC Press Releases RSS: The Securities and Exchange Commission’s Office of Municipal Securities today announced it has updated its Registration of Municipal Advisors FAQs webpage to offer more clarity on municipal advisor registration and recordkeeping requirements. The…
- auto_events: Federal Reserve Press Releases RSS: Federal Reserve announces the leadership and objectives of its task forces to advance the conduct of monetary policy
- auto_events: Federal Reserve Press Releases RSS: Federal Reserve Board issues enforcement action with TS Banking Group, Inc. and TS Contrarian Bancshares, Inc.
- coingecko_global: Global crypto cap 24h change=0.558%, BTC dominance=56.29%, volume=$70.77B.
- defillama_tvl: DeFi TVL approx 7d change=3.495%, latest=$141.24B.
- defillama_stablecoins: Stablecoin listed circulating supply snapshot=$308.52B across 410 assets.

Blockers:
⛔ Causal conflict بالا است؛ هر استفاده عملی باید downgrade شود و فقط Research بماند.

Recommendations:
→ manual_events.csv فعال است؛ رویدادهای high-impact را با source_url معتبر ادامه بده.
→ auto_events.csv فعال است؛ Automatic Event Collector قبل از Causal Intelligence باید اجرا شود.
→ در v7 نتایج causal/narrative فقط به decision log و research reports اضافه می‌شود؛ هیچ Paper/Live فعال نمی‌شود.

Warnings:
⚠️ Causal Intelligence یک لایه پژوهشی است و به‌تنهایی سیگنال خرید/فروش نمی‌سازد.
⚠️ جمع‌آوری APIهای عمومی ممکن است با rate limit یا محدودیت منطقه‌ای روبه‌رو شود؛ شکست source نباید چرخه Forward را fail کند.
⚠️ بین جهت تکنیکال و context بیرونی/علتی تضاد دیده شده؛ confidence تصمیم باید پایین‌تر در نظر گرفته شود.
==============================================================================================================