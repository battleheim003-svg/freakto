==============================================================================================================
🧬 Freakto Root Cause Discovery Engine v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_PRIMARY_PROBABLE
Run ID                 : root_cause_20260718_113453
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Decision Side/Score    : NEUTRAL | 15
Narrative              : MACRO_POLICY_DOMINANT | BEARISH | MACRO_POLICY
Causal Context         : MULTI_SOURCE_EVENT_CONSENSUS | catalyst=42/100

Root Cause:
- Primary              : MACRO_POLICY_PRESSURE
- Direction            : BEARISH
- Confidence           : HIGH
- Probability Share    : 69.19%
- Evidence Quality     : HIGH
- Verdict              : PRIMARY_PROBABLE_ROOT_CAUSE
- Summary              : Probable root cause=MACRO_POLICY_PRESSURE; direction=BEARISH; confidence=HIGH; share=69.19%. قوی‌ترین evidence از federal_reserve_speeches است: Market narrative theme: MACRO_POLICY
- Evidence Total       : 13 | official=10 | event_rows=10

Top Cause Hypotheses:
- MACRO_POLICY_PRESSURE: p=69.19% | score=87.2688 | dir=BEARISH | evidence=10 | verdict=PRIMARY_PROBABLE_CAUSE
- TECHNICAL_STRUCTURE_MOMENTUM: p=14.27% | score=18.0 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- EXCHANGE_MARKET_ACCESS: p=9.37% | score=11.815 | dir=BULLISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- MIXED_EVENT_CONFLICT: p=7.17% | score=9.04 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE

Evidence:
- TECHNICAL_STRUCTURE_MOMENTUM | NEUTRAL | w=18.0 | decision_engine_features | Decision Engine structure/trend/momentum evidence
- EXCHANGE_MARKET_ACCESS | BULLISH | w=11.815 | sec_press_releases | SEC Proposes New E-Delivery Approach to Make Information More Readily Accessible and Useful for Investors
- MACRO_POLICY_PRESSURE | BEARISH | w=10.7938 | market_narrative | Market narrative theme: MACRO_POLICY
- MACRO_POLICY_PRESSURE | NEUTRAL | w=9.775 | federal_reserve_speeches | Jefferson, Navigating Economic Shocks: A Monetary Policymaker’s Perspective
- MACRO_POLICY_PRESSURE | BEARISH | w=9.775 | federal_reserve_press | Agencies issue joint statement on handling of highly sensitive information during bank examinations
- MACRO_POLICY_PRESSURE | BEARISH | w=9.775 | federal_reserve_press | Federal Reserve Board issues enforcement action with former chief lending officer of Heritage State Bank
- MACRO_POLICY_PRESSURE | NEUTRAL | w=9.775 | federal_reserve_speeches | Cook, Economic Outlook
- MIXED_EVENT_CONFLICT | NEUTRAL | w=9.04 | causal_intelligence | Causal context: MULTI_SOURCE_EVENT_CONSENSUS
- MACRO_POLICY_PRESSURE | NEUTRAL | w=7.475 | federal_reserve_speeches | Bowman, Responsible Innovation and Financial Inclusion
- MACRO_POLICY_PRESSURE | NEUTRAL | w=7.475 | federal_reserve_press | Minutes of the Board's discount rate meetings on June 8 and June 17, 2026
- MACRO_POLICY_PRESSURE | NEUTRAL | w=7.475 | federal_reserve_speeches | Barr, Will Artificial Intelligence Broadly Raise Living Standards or Drive Income and Wealth Inequality?
- MACRO_POLICY_PRESSURE | NEUTRAL | w=7.475 | federal_reserve_speeches | Waller, Monetary Policy at a Crossroads

Recommendations:
→ automatic_event_collector، causal_intelligence، market_narrative و narrative_decision را قبل از root_cause اجرا کن.
→ اگر primary_root_cause چند هفته متوالی با outcome مثبت/منفی همبستگی داشت، بعداً می‌تواند وارد Root-Cause Gate Simulator شود.
→ برای افزایش دقت، داده‌های derivatives/on-chain/ETF flow را به evidence registry اضافه کن.

Warnings:
⚠️ Root Cause Discovery احتمالات علّی پژوهشی می‌سازد؛ علت قطعی یا سیگنال خرید/فروش نیست.
⚠️ این ماژول از outcome/return آینده برای تشخیص علت استفاده نمی‌کند تا leakage ایجاد نشود.
⚠️ تا وقتی علت‌ها با forward outcomes اعتبارسنجی نشوند، Paper/Live نباید از آن‌ها استفاده کند.
==============================================================================================================