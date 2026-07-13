==============================================================================================================
🧬 Freakto Root Cause Discovery Engine v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_MIXED_WITH_CONTRADICTIONS
Run ID                 : root_cause_20260713_114549
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Decision Side/Score    : SHORT | 57
Narrative              : MACRO_POLICY_DOMINANT | BEARISH | MACRO_POLICY
Causal Context         : MULTI_SOURCE_EVENT_CONSENSUS | catalyst=6/100

Root Cause:
- Primary              : MACRO_POLICY_PRESSURE
- Direction            : BEARISH
- Confidence           : MEDIUM
- Probability Share    : 45.4%
- Evidence Quality     : HIGH
- Verdict              : PROBABLE_CAUSE_BUT_CONFLICTED
- Summary              : Probable root cause=MACRO_POLICY_PRESSURE; direction=BEARISH; confidence=MEDIUM; share=45.4%. قوی‌ترین evidence از federal_reserve_press است: Market narrative theme: MACRO_POLICY | هشدار: شواهد متضاد همزمان وجود دارد.
- Evidence Total       : 17 | official=13 | event_rows=13

Top Cause Hypotheses:
- MACRO_POLICY_PRESSURE: p=45.4% | score=69.1995 | dir=BEARISH | evidence=8 | verdict=PRIMARY_PROBABLE_CAUSE
- TECHNICAL_STRUCTURE_MOMENTUM: p=11.81% | score=18.0 | dir=BEARISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- EXCHANGE_MARKET_ACCESS: p=11.32% | score=17.25 | dir=MIXED_OR_NEUTRAL | evidence=2 | verdict=WEAK_SUPPORTING_CAUSE
- REGULATORY_ACCESS_OR_MODERNIZATION: p=10.83% | score=16.51 | dir=BULLISH | evidence=2 | verdict=WEAK_SUPPORTING_CAUSE
- LIQUIDITY_VOLUME_FLOW: p=9.84% | score=15.0 | dir=BEARISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- REGULATORY_RISK: p=8.49% | score=12.935 | dir=BEARISH | evidence=2 | verdict=WEAK_SUPPORTING_CAUSE
- MIXED_EVENT_CONFLICT: p=2.32% | score=3.54 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE

Evidence:
- TECHNICAL_STRUCTURE_MOMENTUM | BEARISH | w=18.0 | decision_engine_features | Decision Engine structure/trend/momentum evidence
- LIQUIDITY_VOLUME_FLOW | BEARISH | w=15.0 | decision_engine_volume | Volume/flow evidence from Decision Engine
- MACRO_POLICY_PRESSURE | BEARISH | w=12.8495 | market_narrative | Market narrative theme: MACRO_POLICY
- MACRO_POLICY_PRESSURE | BEARISH | w=11.5 | federal_reserve_speeches | Bowman, Modernizing Financial Regulation
- EXCHANGE_MARKET_ACCESS | NEUTRAL | w=9.775 | sec_press_releases | SEC Office of Municipal Securities Updates FAQs for Registration of Municipal Advisors
- REGULATORY_ACCESS_OR_MODERNIZATION | BULLISH | w=9.035 | sec_press_releases | SEC to Host Virtual Roundtable on Modernizing IPOs and Expanding Access to Public Markets
- MACRO_POLICY_PRESSURE | NEUTRAL | w=7.475 | federal_reserve_press | Federal Reserve announces the leadership and objectives of its task forces to advance the conduct of monetary policy
- MACRO_POLICY_PRESSURE | BEARISH | w=7.475 | federal_reserve_press | Federal Reserve Board issues enforcement action with TS Banking Group, Inc. and TS Contrarian Bancshares, Inc.
- MACRO_POLICY_PRESSURE | NEUTRAL | w=7.475 | federal_reserve_press | Minutes of the Federal Open Market Committee, June 16-17, 2026
- REGULATORY_ACCESS_OR_MODERNIZATION | BULLISH | w=7.475 | sec_press_releases | SEC Small Business Advisory Committee to Explore Modernizing Market Access
- MACRO_POLICY_PRESSURE | BEARISH | w=7.475 | federal_reserve_press | Federal Reserve Board requests comment on a proposal to amend its requirements for banks to maintain anti-money laundering programs
- REGULATORY_RISK | BEARISH | w=7.475 | sec_press_releases | SEC Forms New Retail Fraud Working Group

Contradictions:
⚠️ شواهد bullish و bearish همزمان قوی‌اند: bull=16.51, bear=115.13

Recommendations:
→ automatic_event_collector، causal_intelligence، market_narrative و narrative_decision را قبل از root_cause اجرا کن.
→ اگر primary_root_cause چند هفته متوالی با outcome مثبت/منفی همبستگی داشت، بعداً می‌تواند وارد Root-Cause Gate Simulator شود.
→ برای افزایش دقت، داده‌های derivatives/on-chain/ETF flow را به evidence registry اضافه کن.

Warnings:
⚠️ Root Cause Discovery احتمالات علّی پژوهشی می‌سازد؛ علت قطعی یا سیگنال خرید/فروش نیست.
⚠️ این ماژول از outcome/return آینده برای تشخیص علت استفاده نمی‌کند تا leakage ایجاد نشود.
⚠️ تا وقتی علت‌ها با forward outcomes اعتبارسنجی نشوند، Paper/Live نباید از آن‌ها استفاده کند.
==============================================================================================================