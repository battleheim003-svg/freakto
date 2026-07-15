==============================================================================================================
🧬 Freakto Root Cause Discovery Engine v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_MIXED_WITH_CONTRADICTIONS
Run ID                 : root_cause_20260715_201925
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Decision Side/Score    : LONG | 69
Narrative              : MIXED_NARRATIVE_CONFLICT | BEARISH | MACRO_POLICY
Causal Context         : MULTI_SOURCE_EVENT_CONSENSUS | catalyst=46/100

Root Cause:
- Primary              : MACRO_POLICY_PRESSURE
- Direction            : BEARISH
- Confidence           : MEDIUM
- Probability Share    : 57.55%
- Evidence Quality     : HIGH
- Verdict              : PROBABLE_CAUSE_BUT_CONFLICTED
- Summary              : Probable root cause=MACRO_POLICY_PRESSURE; direction=BEARISH; confidence=MEDIUM; share=57.55%. قوی‌ترین evidence از federal_reserve_speeches است: Cook, Economic Outlook | هشدار: شواهد متضاد همزمان وجود دارد.
- Evidence Total       : 15 | official=10 | event_rows=10

Top Cause Hypotheses:
- MACRO_POLICY_PRESSURE: p=57.55% | score=83.8963 | dir=BEARISH | evidence=9 | verdict=PRIMARY_PROBABLE_CAUSE
- TECHNICAL_STRUCTURE_MOMENTUM: p=12.35% | score=18.0 | dir=BULLISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- MIXED_EVENT_CONFLICT: p=10.94% | score=15.9485 | dir=MIXED_OR_NEUTRAL | evidence=2 | verdict=WEAK_SUPPORTING_CAUSE
- LIQUIDITY_VOLUME_FLOW: p=10.29% | score=15.0 | dir=BULLISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- EXCHANGE_MARKET_ACCESS: p=5.13% | score=7.475 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- REGULATORY_RISK: p=3.75% | score=5.46 | dir=BEARISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE

Evidence:
- TECHNICAL_STRUCTURE_MOMENTUM | BULLISH | w=18.0 | decision_engine_features | Decision Engine structure/trend/momentum evidence
- LIQUIDITY_VOLUME_FLOW | BULLISH | w=15.0 | decision_engine_volume | Volume/flow evidence from Decision Engine
- MACRO_POLICY_PRESSURE | NEUTRAL | w=11.5 | federal_reserve_speeches | Cook, Economic Outlook
- MACRO_POLICY_PRESSURE | NEUTRAL | w=9.775 | federal_reserve_speeches | Bowman, Responsible Innovation and Financial Inclusion
- MACRO_POLICY_PRESSURE | NEUTRAL | w=9.775 | federal_reserve_press | Minutes of the Board's discount rate meetings on June 8 and June 17, 2026
- MACRO_POLICY_PRESSURE | NEUTRAL | w=9.775 | federal_reserve_speeches | Barr, Will Artificial Intelligence Broadly Raise Living Standards or Drive Income and Wealth Inequality?
- MACRO_POLICY_PRESSURE | NEUTRAL | w=9.775 | federal_reserve_speeches | Waller, Monetary Policy at a Crossroads
- MACRO_POLICY_PRESSURE | BEARISH | w=9.775 | federal_reserve_speeches | Bowman, Modernizing Financial Regulation
- MIXED_EVENT_CONFLICT | NEUTRAL | w=9.52 | causal_intelligence | Causal context: MULTI_SOURCE_EVENT_CONSENSUS
- MACRO_POLICY_PRESSURE | BEARISH | w=8.5713 | market_narrative | Market narrative theme: MACRO_POLICY
- EXCHANGE_MARKET_ACCESS | NEUTRAL | w=7.475 | sec_press_releases | SEC Office of Municipal Securities Updates FAQs for Registration of Municipal Advisors
- MACRO_POLICY_PRESSURE | NEUTRAL | w=7.475 | federal_reserve_press | Federal Reserve announces the leadership and objectives of its task forces to advance the conduct of monetary policy

Contradictions:
⚠️ شواهد bullish و bearish همزمان قوی‌اند: bull=33.0, bear=89.36

Recommendations:
→ automatic_event_collector، causal_intelligence، market_narrative و narrative_decision را قبل از root_cause اجرا کن.
→ اگر primary_root_cause چند هفته متوالی با outcome مثبت/منفی همبستگی داشت، بعداً می‌تواند وارد Root-Cause Gate Simulator شود.
→ برای افزایش دقت، داده‌های derivatives/on-chain/ETF flow را به evidence registry اضافه کن.

Warnings:
⚠️ Root Cause Discovery احتمالات علّی پژوهشی می‌سازد؛ علت قطعی یا سیگنال خرید/فروش نیست.
⚠️ این ماژول از outcome/return آینده برای تشخیص علت استفاده نمی‌کند تا leakage ایجاد نشود.
⚠️ تا وقتی علت‌ها با forward outcomes اعتبارسنجی نشوند، Paper/Live نباید از آن‌ها استفاده کند.
==============================================================================================================