==============================================================================================================
🧬 Freakto Root Cause Discovery Engine v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_MIXED_WITH_CONTRADICTIONS
Run ID                 : root_cause_20260714_125254
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Decision Side/Score    : NEUTRAL | 24
Narrative              : MACRO_POLICY_DOMINANT | BEARISH | MACRO_POLICY
Causal Context         : MULTI_SOURCE_EVENT_CONSENSUS | catalyst=25/100

Root Cause:
- Primary              : MACRO_POLICY_PRESSURE
- Direction            : BEARISH
- Confidence           : MEDIUM
- Probability Share    : 50.96%
- Evidence Quality     : HIGH
- Verdict              : PROBABLE_CAUSE_BUT_CONFLICTED
- Summary              : Probable root cause=MACRO_POLICY_PRESSURE; direction=BEARISH; confidence=MEDIUM; share=50.96%. قوی‌ترین evidence از federal_reserve_press است: Waller, Monetary Policy at a Crossroads | هشدار: شواهد متضاد همزمان وجود دارد.
- Evidence Total       : 14 | official=11 | event_rows=11

Top Cause Hypotheses:
- MACRO_POLICY_PRESSURE: p=50.96% | score=62.5149 | dir=BEARISH | evidence=7 | verdict=PRIMARY_PROBABLE_CAUSE
- TECHNICAL_STRUCTURE_MOMENTUM: p=14.67% | score=18.0 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- REGULATORY_ACCESS_OR_MODERNIZATION: p=13.46% | score=16.51 | dir=BULLISH | evidence=2 | verdict=WEAK_SUPPORTING_CAUSE
- REGULATORY_RISK: p=10.54% | score=12.935 | dir=BEARISH | evidence=2 | verdict=WEAK_SUPPORTING_CAUSE
- EXCHANGE_MARKET_ACCESS: p=6.09% | score=7.475 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- MIXED_EVENT_CONFLICT: p=4.28% | score=5.25 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE

Evidence:
- TECHNICAL_STRUCTURE_MOMENTUM | NEUTRAL | w=18.0 | decision_engine_features | Decision Engine structure/trend/momentum evidence
- MACRO_POLICY_PRESSURE | NEUTRAL | w=11.5 | federal_reserve_speeches | Waller, Monetary Policy at a Crossroads
- MACRO_POLICY_PRESSURE | BEARISH | w=11.3399 | market_narrative | Market narrative theme: MACRO_POLICY
- MACRO_POLICY_PRESSURE | BEARISH | w=9.775 | federal_reserve_speeches | Bowman, Modernizing Financial Regulation
- REGULATORY_ACCESS_OR_MODERNIZATION | BULLISH | w=9.035 | sec_press_releases | SEC to Host Virtual Roundtable on Modernizing IPOs and Expanding Access to Public Markets
- EXCHANGE_MARKET_ACCESS | NEUTRAL | w=7.475 | sec_press_releases | SEC Office of Municipal Securities Updates FAQs for Registration of Municipal Advisors
- MACRO_POLICY_PRESSURE | NEUTRAL | w=7.475 | federal_reserve_press | Federal Reserve announces the leadership and objectives of its task forces to advance the conduct of monetary policy
- MACRO_POLICY_PRESSURE | BEARISH | w=7.475 | federal_reserve_press | Federal Reserve Board issues enforcement action with TS Banking Group, Inc. and TS Contrarian Bancshares, Inc.
- MACRO_POLICY_PRESSURE | NEUTRAL | w=7.475 | federal_reserve_press | Minutes of the Federal Open Market Committee, June 16-17, 2026
- REGULATORY_ACCESS_OR_MODERNIZATION | BULLISH | w=7.475 | sec_press_releases | SEC Small Business Advisory Committee to Explore Modernizing Market Access
- MACRO_POLICY_PRESSURE | BEARISH | w=7.475 | federal_reserve_press | Federal Reserve Board requests comment on a proposal to amend its requirements for banks to maintain anti-money laundering programs
- REGULATORY_RISK | BEARISH | w=7.475 | sec_press_releases | SEC Forms New Retail Fraud Working Group

Contradictions:
⚠️ شواهد bullish و bearish همزمان قوی‌اند: bull=16.51, bear=75.45

Recommendations:
→ automatic_event_collector، causal_intelligence، market_narrative و narrative_decision را قبل از root_cause اجرا کن.
→ اگر primary_root_cause چند هفته متوالی با outcome مثبت/منفی همبستگی داشت، بعداً می‌تواند وارد Root-Cause Gate Simulator شود.
→ برای افزایش دقت، داده‌های derivatives/on-chain/ETF flow را به evidence registry اضافه کن.

Warnings:
⚠️ Root Cause Discovery احتمالات علّی پژوهشی می‌سازد؛ علت قطعی یا سیگنال خرید/فروش نیست.
⚠️ این ماژول از outcome/return آینده برای تشخیص علت استفاده نمی‌کند تا leakage ایجاد نشود.
⚠️ تا وقتی علت‌ها با forward outcomes اعتبارسنجی نشوند، Paper/Live نباید از آن‌ها استفاده کند.
==============================================================================================================