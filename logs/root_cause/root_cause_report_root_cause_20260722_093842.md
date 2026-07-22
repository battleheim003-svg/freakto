==============================================================================================================
🧬 Freakto Root Cause Discovery Engine v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_PRIMARY_PROBABLE
Run ID                 : root_cause_20260722_093842
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Decision Side/Score    : NEUTRAL | 30
Narrative              : MACRO_POLICY_DOMINANT | MIXED_OR_NEUTRAL | MACRO_POLICY
Causal Context         : MULTI_SOURCE_EVENT_CONSENSUS | catalyst=52/100

Root Cause:
- Primary              : MACRO_POLICY_PRESSURE
- Direction            : BEARISH
- Confidence           : HIGH
- Probability Share    : 55.08%
- Evidence Quality     : HIGH
- Verdict              : PRIMARY_PROBABLE_ROOT_CAUSE
- Summary              : Probable root cause=MACRO_POLICY_PRESSURE; direction=BEARISH; confidence=HIGH; share=55.08%. قوی‌ترین evidence از federal_reserve_speeches است: Market narrative theme: MACRO_POLICY
- Evidence Total       : 8 | official=5 | event_rows=5

Top Cause Hypotheses:
- MACRO_POLICY_PRESSURE: p=55.08% | score=37.5358 | dir=BEARISH | evidence=5 | verdict=PRIMARY_PROBABLE_CAUSE
- TECHNICAL_STRUCTURE_MOMENTUM: p=20.4% | score=13.9 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- EXCHANGE_MARKET_ACCESS: p=13.26% | score=9.035 | dir=BULLISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- MIXED_EVENT_CONFLICT: p=11.27% | score=7.68 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE

Evidence:
- TECHNICAL_STRUCTURE_MOMENTUM | NEUTRAL | w=13.9 | decision_engine_features | Decision Engine structure/trend/momentum evidence
- EXCHANGE_MARKET_ACCESS | BULLISH | w=9.035 | sec_press_releases | SEC Proposes New E-Delivery Approach to Make Information More Readily Accessible and Useful for Investors
- MIXED_EVENT_CONFLICT | NEUTRAL | w=7.68 | causal_intelligence | Causal context: MULTI_SOURCE_EVENT_CONSENSUS
- MACRO_POLICY_PRESSURE | MIXED_OR_NEUTRAL | w=7.6358 | market_narrative | Market narrative theme: MACRO_POLICY
- MACRO_POLICY_PRESSURE | NEUTRAL | w=7.475 | federal_reserve_speeches | Jefferson, Navigating Economic Shocks: A Monetary Policymaker’s Perspective
- MACRO_POLICY_PRESSURE | BEARISH | w=7.475 | federal_reserve_press | Agencies issue joint statement on handling of highly sensitive information during bank examinations
- MACRO_POLICY_PRESSURE | BEARISH | w=7.475 | federal_reserve_press | Federal Reserve Board issues enforcement action with former chief lending officer of Heritage State Bank
- MACRO_POLICY_PRESSURE | NEUTRAL | w=7.475 | federal_reserve_speeches | Cook, Economic Outlook

Recommendations:
→ automatic_event_collector، causal_intelligence، market_narrative و narrative_decision را قبل از root_cause اجرا کن.
→ اگر primary_root_cause چند هفته متوالی با outcome مثبت/منفی همبستگی داشت، بعداً می‌تواند وارد Root-Cause Gate Simulator شود.
→ برای افزایش دقت، داده‌های derivatives/on-chain/ETF flow را به evidence registry اضافه کن.

Warnings:
⚠️ Root Cause Discovery احتمالات علّی پژوهشی می‌سازد؛ علت قطعی یا سیگنال خرید/فروش نیست.
⚠️ این ماژول از outcome/return آینده برای تشخیص علت استفاده نمی‌کند تا leakage ایجاد نشود.
⚠️ تا وقتی علت‌ها با forward outcomes اعتبارسنجی نشوند، Paper/Live نباید از آن‌ها استفاده کند.
==============================================================================================================