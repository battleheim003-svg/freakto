==============================================================================================================
🧬 Freakto Root Cause Discovery Engine v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_RESEARCH_CANDIDATE
Run ID                 : root_cause_20260730_171248
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Decision Side/Score    : NEUTRAL | 30
Narrative              : MACRO_POLICY_DOMINANT | BEARISH | MACRO_POLICY
Causal Context         : MULTI_SOURCE_EVENT_CONSENSUS | catalyst=39/100

Root Cause:
- Primary              : MACRO_POLICY_PRESSURE
- Direction            : BEARISH
- Confidence           : MEDIUM
- Probability Share    : 48.01%
- Evidence Quality     : HIGH
- Verdict              : ROOT_CAUSE_CANDIDATE_RESEARCH_ONLY
- Summary              : Probable root cause=MACRO_POLICY_PRESSURE; direction=BEARISH; confidence=MEDIUM; share=48.01%. قوی‌ترین evidence از federal_reserve_press است: Federal Reserve Board issues enforcement actions with former employee of Regions Bank and former employee of First Interstate Bank
- Evidence Total       : 8 | official=5 | event_rows=5

Top Cause Hypotheses:
- MACRO_POLICY_PRESSURE: p=48.01% | score=44.2806 | dir=BEARISH | evidence=4 | verdict=PRIMARY_PROBABLE_CAUSE
- EXCHANGE_MARKET_ACCESS: p=23.07% | score=21.275 | dir=MIXED_OR_NEUTRAL | evidence=2 | verdict=WEAK_SUPPORTING_CAUSE
- TECHNICAL_STRUCTURE_MOMENTUM: p=19.52% | score=18.0 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- MIXED_EVENT_CONFLICT: p=9.41% | score=8.68 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE

Evidence:
- TECHNICAL_STRUCTURE_MOMENTUM | NEUTRAL | w=18.0 | decision_engine_features | Decision Engine structure/trend/momentum evidence
- MACRO_POLICY_PRESSURE | BEARISH | w=11.5 | federal_reserve_press | Federal Reserve Board issues enforcement actions with former employee of Regions Bank and former employee of First Interstate Bank
- MACRO_POLICY_PRESSURE | BEARISH | w=11.5 | federal_reserve_press | Federal Reserve Board issues enforcement action with Iuka Bancshares, Inc. and The Iuka State Bank
- EXCHANGE_MARKET_ACCESS | NEUTRAL | w=11.5 | sec_press_releases | SEC Announces Continuation of Small Business Advisory Committee Meeting
- MACRO_POLICY_PRESSURE | NEUTRAL | w=11.5 | federal_reserve_press | Federal Reserve issues FOMC statement
- MACRO_POLICY_PRESSURE | BEARISH | w=9.7806 | market_narrative | Market narrative theme: MACRO_POLICY
- EXCHANGE_MARKET_ACCESS | NEUTRAL | w=9.775 | sec_press_releases | Small Business Forum’s Report to Congress Highlights Recommendations to Improve Capital-Raising Policy
- MIXED_EVENT_CONFLICT | NEUTRAL | w=8.68 | causal_intelligence | Causal context: MULTI_SOURCE_EVENT_CONSENSUS

Recommendations:
→ automatic_event_collector، causal_intelligence، market_narrative و narrative_decision را قبل از root_cause اجرا کن.
→ اگر primary_root_cause چند هفته متوالی با outcome مثبت/منفی همبستگی داشت، بعداً می‌تواند وارد Root-Cause Gate Simulator شود.
→ برای افزایش دقت، داده‌های derivatives/on-chain/ETF flow را به evidence registry اضافه کن.

Warnings:
⚠️ Root Cause Discovery احتمالات علّی پژوهشی می‌سازد؛ علت قطعی یا سیگنال خرید/فروش نیست.
⚠️ این ماژول از outcome/return آینده برای تشخیص علت استفاده نمی‌کند تا leakage ایجاد نشود.
⚠️ تا وقتی علت‌ها با forward outcomes اعتبارسنجی نشوند، Paper/Live نباید از آن‌ها استفاده کند.
==============================================================================================================