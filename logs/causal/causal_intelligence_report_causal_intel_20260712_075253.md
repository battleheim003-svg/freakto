==============================================================================================================
🧠 Freakto Causal/Event Intelligence Core v7.2.0
==============================================================================================================
Status                 : CAUSAL_CONTEXT_WITH_BLOCKERS
Run ID                 : causal_intel_20260712_075253
Symbol / TF            : BTC/USDT | 4h
Collect Live Sources   : True
Sources OK/Failed      : 15 / 2
Trusted Sources OK     : 14
Manual Events Loaded   : 0
Auto Events Loaded     : 11

Causal Context:
- Primary Cause        : MULTI_SOURCE_EVENT_CONSENSUS
- Cause Confidence     : HIGH
- Catalyst Score       : 41/100
- Event Risk           : HIGH
- Technical Conflict   : HIGH
- Alignment            : CONFLICT_WITH_EXTERNAL_CONTEXT
- Verdict              : CAUSAL_CONFLICT_RESEARCH_ONLY
- Evidence Strength    : 0.6745 (MEDIUM)
- Claim Status         : PLAUSIBLE_HYPOTHESIS
- Independent Sources  : 7
- Direction Agreement  : 0.8

Alternative Explanations:
- Internal alternative: TREND_MOMENTUM_ALIGNMENT (trend and momentum components are aligned)
- Internal alternative: REGIME_ALIGNED_BULL_LONG (TRENDING_BULL regime supports LONG bias)
- Conflicting evidence: SEC Press Releases RSS: The Securities and Exchange Commission’s Office of the Advocate for Small Business Capital Formation and the Division of Corporation Finance will co-host a 

Internal Causes:
- TREND_MOMENTUM_ALIGNMENT: dir=LONG | conf=MEDIUM | score=18 | trend and momentum components are aligned
- REGIME_ALIGNED_BULL_LONG: dir=BULLISH | conf=MEDIUM | score=12 | TRENDING_BULL regime supports LONG bias

Source Health:
- auto_events: OK | TIER_1_OFFICIAL_REGULATOR | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=BEARISH | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_REGULATOR | dir=BULLISH | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_REGULATOR | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=BEARISH | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_REGULATOR | dir=BEARISH | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_REGULATOR | dir=NEUTRAL | risk=HIGH
- auto_events: OK | TIER_1_OFFICIAL_MACRO | dir=BEARISH | risk=HIGH
- coingecko_global: OK | TIER_2_MARKET_AGGREGATOR | dir=NEUTRAL | risk=LOW

Source Summaries:
- auto_events: SEC Press Releases RSS: The Securities and Exchange Commission’s Office of Municipal Securities today announced it has updated its Registration of Municipal Advisors FAQs webpage to offer more clarity on municipal advisor registration and recordkeeping requirements. The…
- auto_events: Federal Reserve Press Releases RSS: Federal Reserve announces the leadership and objectives of its task forces to advance the conduct of monetary policy
- auto_events: Federal Reserve Press Releases RSS: Federal Reserve Board issues enforcement action with TS Banking Group, Inc. and TS Contrarian Bancshares, Inc.
- auto_events: Federal Reserve Press Releases RSS: Minutes of the Federal Open Market Committee, June 16-17, 2026
- auto_events: SEC Press Releases RSS: The Securities and Exchange Commission’s Office of the Advocate for Small Business Capital Formation and the Division of Corporation Finance will co-host a livestreamed discussion on Monday, July 13, 2026, at 2 p.m. to re-examine…
- auto_events: SEC Press Releases RSS: The Securities and Exchange Commission’s Small Business Capital Formation Advisory Committee announced that it will hold a meeting on Tuesday, July 21, 2026 at 10 a.m. to explore ways to modernize public market access and encourage IPOs…
- auto_events: Federal Reserve Press Releases RSS: Federal Reserve Board requests comment on a proposal to amend its requirements for banks to maintain anti-money laundering programs
- auto_events: SEC Press Releases RSS: The Securities and Exchange Commission today announced the creation of the Retail Fraud Working Group designed to strengthen the Division of Enforcement’s efforts to identify and combat fraud targeting everyday investors.The Retail Fraud Working Group…
- auto_events: Federal Reserve Speeches RSS: Speech At the Financial Stability Board Virtual Outreach Event
- auto_events: SEC Press Releases RSS: The Securities and Exchange Commission today announced that Paul Knight has been named as the agency’s Chief Operating Officer (COO).As COO, Mr. Knight will oversee the SEC's operational and administrative functions, including the agency's Office of…
- auto_events: Federal Reserve Speeches RSS: Speech At "Challenges for Monetary Policy Transmission in a Changing World," a conference sponsored by the Bank of Italy for the research network initiated by the European System of Central Banks, Rome, Italy
- coingecko_global: Global crypto cap 24h change=-0.395%, BTC dominance=56.28%, volume=$46.7B.

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