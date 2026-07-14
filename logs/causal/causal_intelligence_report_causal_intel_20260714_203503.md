==============================================================================================================
🧠 Freakto Causal/Event Intelligence Core v7.2.0
==============================================================================================================
Status                 : CAUSAL_CONTEXT_PARTIAL_SOURCES
Run ID                 : causal_intel_20260714_203503
Symbol / TF            : BTC/USDT | 4h
Collect Live Sources   : True
Sources OK/Failed      : 15 / 2
Trusted Sources OK     : 14
Manual Events Loaded   : 0
Auto Events Loaded     : 11

Causal Context:
- Primary Cause        : MULTI_SOURCE_EVENT_CONSENSUS
- Cause Confidence     : LOW
- Catalyst Score       : 60/100
- Event Risk           : HIGH
- Technical Conflict   : LOW
- Alignment            : NEUTRAL_DECISION_CONTEXT_ONLY
- Verdict              : CAUSAL_HYPOTHESIS_WEAK_EVIDENCE
- Evidence Strength    : 0.5101 (LOW)
- Claim Status         : WEAK_HYPOTHESIS
- Independent Sources  : 7
- Direction Agreement  : 0.5

Alternative Explanations:
- Internal alternative: STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION (structure_score>=10 but volume support is weak/missing)
- Conflicting evidence: SEC Press Releases RSS: The Securities and Exchange Commission’s Office of the Advocate for Small Business Capital Formation and the Division of Corporation Finance will co-host a 
- Conflicting evidence: Global crypto cap 24h change=3.238%, BTC dominance=56.24%, volume=$73.24B.

Internal Causes:
- STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION: dir=NEUTRAL | conf=LOW | score=12 | structure_score>=10 but volume support is weak/missing

Source Health:
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=BEARISH | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_REGULATOR | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=BEARISH | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_REGULATOR | dir=BULLISH | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_REGULATOR | dir=NEUTRAL | risk=HIGH
- coingecko_global: OK | TIER_2_MARKET_AGGREGATOR | dir=BULLISH | risk=LOW

Source Summaries:
- auto_events: Federal Reserve Speeches RSS: Speech At “Next-Gen Financial Inclusion,” the third annual Financial Inclusion Conference hosted by the Federal Reserve Board, Washington, D.C. (via pre-recorded video)
- auto_events: Federal Reserve Press Releases RSS: Minutes of the Board's discount rate meetings on June 8 and June 17, 2026
- auto_events: Federal Reserve Speeches RSS: Speech At “Next-Gen Financial Inclusion,” the third annual Financial Inclusion Conference hosted by the Federal Reserve Board
- auto_events: Federal Reserve Speeches RSS: Speech At the New York Association for Business Economics, New York, New York
- auto_events: Federal Reserve Speeches RSS: Speech At a Bank Policy Institute London Conference, London, United Kingdom
- auto_events: SEC Press Releases RSS: The Securities and Exchange Commission’s Office of Municipal Securities today announced it has updated its Registration of Municipal Advisors FAQs webpage to offer more clarity on municipal advisor registration and recordkeeping requirements. The…
- auto_events: Federal Reserve Press Releases RSS: Federal Reserve announces the leadership and objectives of its task forces to advance the conduct of monetary policy
- auto_events: Federal Reserve Press Releases RSS: Federal Reserve Board issues enforcement action with TS Banking Group, Inc. and TS Contrarian Bancshares, Inc.
- auto_events: Federal Reserve Press Releases RSS: Minutes of the Federal Open Market Committee, June 16-17, 2026
- auto_events: SEC Press Releases RSS: The Securities and Exchange Commission’s Office of the Advocate for Small Business Capital Formation and the Division of Corporation Finance will co-host a livestreamed discussion on Monday, July 13, 2026, at 2 p.m. to re-examine…
- auto_events: SEC Press Releases RSS: The Securities and Exchange Commission’s Small Business Capital Formation Advisory Committee announced that it will hold a meeting on Tuesday, July 21, 2026 at 10 a.m. to explore ways to modernize public market access and encourage IPOs…
- coingecko_global: Global crypto cap 24h change=3.238%, BTC dominance=56.24%, volume=$73.24B.

Recommendations:
→ manual_events.csv فعال است؛ رویدادهای high-impact را با source_url معتبر ادامه بده.
→ auto_events.csv فعال است؛ Automatic Event Collector قبل از Causal Intelligence باید اجرا شود.
→ در v7 نتایج causal/narrative فقط به decision log و research reports اضافه می‌شود؛ هیچ Paper/Live فعال نمی‌شود.

Warnings:
⚠️ Causal Intelligence یک لایه پژوهشی است و به‌تنهایی سیگنال خرید/فروش نمی‌سازد.
⚠️ جمع‌آوری APIهای عمومی ممکن است با rate limit یا محدودیت منطقه‌ای روبه‌رو شود؛ شکست source نباید چرخه Forward را fail کند.
==============================================================================================================