==============================================================================================================
🧬 Freakto Root Cause Discovery Engine v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_MIXED_WITH_CONTRADICTIONS
Run ID                 : root_cause_20260723_170658
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Decision Side/Score    : SHORT | 78
Narrative              : MACRO_POLICY_DOMINANT | MIXED_OR_NEUTRAL | MACRO_POLICY
Causal Context         : AUTO_EVENTS_CONTEXT | catalyst=46/100

Root Cause:
- Primary              : MACRO_POLICY_PRESSURE
- Direction            : BEARISH
- Confidence           : LOW
- Probability Share    : 28.22%
- Evidence Quality     : HIGH
- Verdict              : PROBABLE_CAUSE_BUT_CONFLICTED
- Summary              : Probable root cause=MACRO_POLICY_PRESSURE; direction=BEARISH; confidence=LOW; share=28.22%. قوی‌ترین evidence از federal_reserve_speeches است: Jefferson, Navigating Economic Shocks: A Monetary Policymaker’s Perspective | هشدار: شواهد متضاد همزمان وجود دارد.
- Evidence Total       : 8 | official=4 | event_rows=4

Top Cause Hypotheses:
- MACRO_POLICY_PRESSURE: p=28.22% | score=22.2764 | dir=BEARISH | evidence=3 | verdict=SUPPORTING_CAUSE
- TECHNICAL_STRUCTURE_MOMENTUM: p=22.8% | score=18.0 | dir=BEARISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- LIQUIDITY_VOLUME_FLOW: p=19.0% | score=15.0 | dir=BEARISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- REGULATORY_ACCESS_OR_MODERNIZATION: p=17.61% | score=13.9 | dir=BULLISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- REGULATORY_RISK: p=12.38% | score=9.775 | dir=BEARISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE

Evidence:
- TECHNICAL_STRUCTURE_MOMENTUM | BEARISH | w=18.0 | decision_engine_features | Decision Engine structure/trend/momentum evidence
- LIQUIDITY_VOLUME_FLOW | BEARISH | w=15.0 | decision_engine_volume | Volume/flow evidence from Decision Engine
- REGULATORY_ACCESS_OR_MODERNIZATION | BULLISH | w=13.9 | sec_press_releases | SEC Announces Roundtable on Preparations for 24-Hour Trading
- REGULATORY_RISK | BEARISH | w=9.775 | sec_press_releases | SEC Announces Departure of Principal Deputy Director of Enforcement Sam Waldon
- UNKNOWN_OR_INSUFFICIENT_EVIDENCE | NEUTRAL | w=9.52 | causal_intelligence | Causal context: AUTO_EVENTS_CONTEXT
- MACRO_POLICY_PRESSURE | NEUTRAL | w=7.475 | federal_reserve_speeches | Jefferson, Navigating Economic Shocks: A Monetary Policymaker’s Perspective
- MACRO_POLICY_PRESSURE | BEARISH | w=7.475 | federal_reserve_press | Agencies issue joint statement on handling of highly sensitive information during bank examinations
- MACRO_POLICY_PRESSURE | MIXED_OR_NEUTRAL | w=7.3264 | market_narrative | Market narrative theme: MACRO_POLICY

Contradictions:
⚠️ علت دوم از نظر وزن به علت اول نزدیک است؛ root cause هنوز تک‌علتی نیست.

Recommendations:
→ automatic_event_collector، causal_intelligence، market_narrative و narrative_decision را قبل از root_cause اجرا کن.
→ اگر primary_root_cause چند هفته متوالی با outcome مثبت/منفی همبستگی داشت، بعداً می‌تواند وارد Root-Cause Gate Simulator شود.
→ برای افزایش دقت، داده‌های derivatives/on-chain/ETF flow را به evidence registry اضافه کن.

Warnings:
⚠️ Root Cause Discovery احتمالات علّی پژوهشی می‌سازد؛ علت قطعی یا سیگنال خرید/فروش نیست.
⚠️ این ماژول از outcome/return آینده برای تشخیص علت استفاده نمی‌کند تا leakage ایجاد نشود.
⚠️ تا وقتی علت‌ها با forward outcomes اعتبارسنجی نشوند، Paper/Live نباید از آن‌ها استفاده کند.
==============================================================================================================