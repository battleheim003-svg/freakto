==============================================================================================================
🧬 Freakto Root Cause Discovery Engine v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_MIXED_WITH_CONTRADICTIONS
Run ID                 : root_cause_20260721_170302
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Decision Side/Score    : LONG | 65
Narrative              : MACRO_POLICY_DOMINANT | MIXED_OR_NEUTRAL | MACRO_POLICY
Causal Context         : MULTI_SOURCE_EVENT_CONSENSUS | catalyst=65/100

Root Cause:
- Primary              : MACRO_POLICY_PRESSURE
- Direction            : BEARISH
- Confidence           : MEDIUM
- Probability Share    : 50.81%
- Evidence Quality     : HIGH
- Verdict              : PROBABLE_CAUSE_BUT_CONFLICTED
- Summary              : Probable root cause=MACRO_POLICY_PRESSURE; direction=BEARISH; confidence=MEDIUM; share=50.81%. قوی‌ترین evidence از federal_reserve_speeches است: Market narrative theme: MACRO_POLICY | هشدار: شواهد متضاد همزمان وجود دارد.
- Evidence Total       : 11 | official=7 | event_rows=7

Top Cause Hypotheses:
- MACRO_POLICY_PRESSURE: p=50.81% | score=52.5519 | dir=BEARISH | evidence=7 | verdict=PRIMARY_PROBABLE_CAUSE
- TECHNICAL_STRUCTURE_MOMENTUM: p=17.4% | score=18.0 | dir=BULLISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- LIQUIDITY_VOLUME_FLOW: p=14.5% | score=15.0 | dir=BULLISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- EXCHANGE_MARKET_ACCESS: p=8.73% | score=9.035 | dir=BULLISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- MIXED_EVENT_CONFLICT: p=8.56% | score=8.85 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE

Evidence:
- TECHNICAL_STRUCTURE_MOMENTUM | BULLISH | w=18.0 | decision_engine_features | Decision Engine structure/trend/momentum evidence
- LIQUIDITY_VOLUME_FLOW | BULLISH | w=15.0 | decision_engine_volume | Volume/flow evidence from Decision Engine
- EXCHANGE_MARKET_ACCESS | BULLISH | w=9.035 | sec_press_releases | SEC Proposes New E-Delivery Approach to Make Information More Readily Accessible and Useful for Investors
- MIXED_EVENT_CONFLICT | NEUTRAL | w=8.85 | causal_intelligence | Causal context: MULTI_SOURCE_EVENT_CONSENSUS
- MACRO_POLICY_PRESSURE | MIXED_OR_NEUTRAL | w=7.7019 | market_narrative | Market narrative theme: MACRO_POLICY
- MACRO_POLICY_PRESSURE | NEUTRAL | w=7.475 | federal_reserve_speeches | Jefferson, Navigating Economic Shocks: A Monetary Policymaker’s Perspective
- MACRO_POLICY_PRESSURE | BEARISH | w=7.475 | federal_reserve_press | Agencies issue joint statement on handling of highly sensitive information during bank examinations
- MACRO_POLICY_PRESSURE | BEARISH | w=7.475 | federal_reserve_press | Federal Reserve Board issues enforcement action with former chief lending officer of Heritage State Bank
- MACRO_POLICY_PRESSURE | NEUTRAL | w=7.475 | federal_reserve_speeches | Cook, Economic Outlook
- MACRO_POLICY_PRESSURE | NEUTRAL | w=7.475 | federal_reserve_speeches | Bowman, Responsible Innovation and Financial Inclusion
- MACRO_POLICY_PRESSURE | NEUTRAL | w=7.475 | federal_reserve_press | Minutes of the Board's discount rate meetings on June 8 and June 17, 2026

Contradictions:
⚠️ شواهد bullish و bearish همزمان قوی‌اند: bull=42.03, bear=52.55

Recommendations:
→ automatic_event_collector، causal_intelligence، market_narrative و narrative_decision را قبل از root_cause اجرا کن.
→ اگر primary_root_cause چند هفته متوالی با outcome مثبت/منفی همبستگی داشت، بعداً می‌تواند وارد Root-Cause Gate Simulator شود.
→ برای افزایش دقت، داده‌های derivatives/on-chain/ETF flow را به evidence registry اضافه کن.

Warnings:
⚠️ Root Cause Discovery احتمالات علّی پژوهشی می‌سازد؛ علت قطعی یا سیگنال خرید/فروش نیست.
⚠️ این ماژول از outcome/return آینده برای تشخیص علت استفاده نمی‌کند تا leakage ایجاد نشود.
⚠️ تا وقتی علت‌ها با forward outcomes اعتبارسنجی نشوند، Paper/Live نباید از آن‌ها استفاده کند.
==============================================================================================================