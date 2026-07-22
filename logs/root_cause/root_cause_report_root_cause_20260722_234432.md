==============================================================================================================
🧬 Freakto Root Cause Discovery Engine v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_RESEARCH_CANDIDATE
Run ID                 : root_cause_20260722_234432
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Decision Side/Score    : NEUTRAL | 23
Narrative              : MACRO_POLICY_DOMINANT | BEARISH | MACRO_POLICY
Causal Context         : MULTI_SOURCE_EVENT_CONSENSUS | catalyst=41/100

Root Cause:
- Primary              : MACRO_POLICY_PRESSURE
- Direction            : BEARISH
- Confidence           : MEDIUM
- Probability Share    : 43.25%
- Evidence Quality     : HIGH
- Verdict              : ROOT_CAUSE_CANDIDATE_RESEARCH_ONLY
- Summary              : Probable root cause=MACRO_POLICY_PRESSURE; direction=BEARISH; confidence=MEDIUM; share=43.25%. قوی‌ترین evidence از federal_reserve_press است: Market narrative theme: MACRO_POLICY
- Evidence Total       : 8 | official=5 | event_rows=5

Top Cause Hypotheses:
- MACRO_POLICY_PRESSURE: p=43.25% | score=31.3372 | dir=BEARISH | evidence=4 | verdict=SUPPORTING_CAUSE
- TECHNICAL_STRUCTURE_MOMENTUM: p=19.18% | score=13.9 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- REGULATORY_RISK: p=15.87% | score=11.5 | dir=BEARISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- EXCHANGE_MARKET_ACCESS: p=12.47% | score=9.035 | dir=BULLISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- MIXED_EVENT_CONFLICT: p=9.23% | score=6.69 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE

Evidence:
- TECHNICAL_STRUCTURE_MOMENTUM | NEUTRAL | w=13.9 | decision_engine_features | Decision Engine structure/trend/momentum evidence
- REGULATORY_RISK | BEARISH | w=11.5 | sec_press_releases | SEC Announces Departure of Principal Deputy Director of Enforcement Sam Waldon
- EXCHANGE_MARKET_ACCESS | BULLISH | w=9.035 | sec_press_releases | SEC Proposes New E-Delivery Approach to Make Information More Readily Accessible and Useful for Investors
- MACRO_POLICY_PRESSURE | BEARISH | w=8.9122 | market_narrative | Market narrative theme: MACRO_POLICY
- MACRO_POLICY_PRESSURE | NEUTRAL | w=7.475 | federal_reserve_speeches | Jefferson, Navigating Economic Shocks: A Monetary Policymaker’s Perspective
- MACRO_POLICY_PRESSURE | BEARISH | w=7.475 | federal_reserve_press | Agencies issue joint statement on handling of highly sensitive information during bank examinations
- MACRO_POLICY_PRESSURE | BEARISH | w=7.475 | federal_reserve_press | Federal Reserve Board issues enforcement action with former chief lending officer of Heritage State Bank
- MIXED_EVENT_CONFLICT | NEUTRAL | w=6.69 | causal_intelligence | Causal context: MULTI_SOURCE_EVENT_CONSENSUS

Recommendations:
→ automatic_event_collector، causal_intelligence، market_narrative و narrative_decision را قبل از root_cause اجرا کن.
→ اگر primary_root_cause چند هفته متوالی با outcome مثبت/منفی همبستگی داشت، بعداً می‌تواند وارد Root-Cause Gate Simulator شود.
→ برای افزایش دقت، داده‌های derivatives/on-chain/ETF flow را به evidence registry اضافه کن.

Warnings:
⚠️ Root Cause Discovery احتمالات علّی پژوهشی می‌سازد؛ علت قطعی یا سیگنال خرید/فروش نیست.
⚠️ این ماژول از outcome/return آینده برای تشخیص علت استفاده نمی‌کند تا leakage ایجاد نشود.
⚠️ تا وقتی علت‌ها با forward outcomes اعتبارسنجی نشوند، Paper/Live نباید از آن‌ها استفاده کند.
==============================================================================================================