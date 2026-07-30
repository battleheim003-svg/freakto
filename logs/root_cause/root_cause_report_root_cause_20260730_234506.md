==============================================================================================================
🧬 Freakto Root Cause Discovery Engine v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_RESEARCH_CANDIDATE
Run ID                 : root_cause_20260730_234506
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Decision Side/Score    : NEUTRAL | 38
Narrative              : MACRO_POLICY_DOMINANT | BEARISH | MACRO_POLICY
Causal Context         : MULTI_SOURCE_EVENT_CONSENSUS | catalyst=40/100

Root Cause:
- Primary              : MACRO_POLICY_PRESSURE
- Direction            : BEARISH
- Confidence           : MEDIUM
- Probability Share    : 48.12%
- Evidence Quality     : HIGH
- Verdict              : ROOT_CAUSE_CANDIDATE_RESEARCH_ONLY
- Summary              : Probable root cause=MACRO_POLICY_PRESSURE; direction=BEARISH; confidence=MEDIUM; share=48.12%. قوی‌ترین evidence از federal_reserve_press است: Federal Reserve Board issues enforcement actions with former employee of Regions Bank and former employee of First Interstate Bank
- Evidence Total       : 8 | official=5 | event_rows=5

Top Cause Hypotheses:
- MACRO_POLICY_PRESSURE: p=48.12% | score=42.4496 | dir=BEARISH | evidence=4 | verdict=PRIMARY_PROBABLE_CAUSE
- EXCHANGE_MARKET_ACCESS: p=21.51% | score=18.975 | dir=MIXED_OR_NEUTRAL | evidence=2 | verdict=WEAK_SUPPORTING_CAUSE
- TECHNICAL_STRUCTURE_MOMENTUM: p=20.4% | score=18.0 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- MIXED_EVENT_CONFLICT: p=9.97% | score=8.8 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE

Evidence:
- TECHNICAL_STRUCTURE_MOMENTUM | NEUTRAL | w=18.0 | decision_engine_features | Decision Engine structure/trend/momentum evidence
- MACRO_POLICY_PRESSURE | BEARISH | w=11.5 | federal_reserve_press | Federal Reserve Board issues enforcement actions with former employee of Regions Bank and former employee of First Interstate Bank
- MACRO_POLICY_PRESSURE | BEARISH | w=11.5 | federal_reserve_press | Federal Reserve Board issues enforcement action with Iuka Bancshares, Inc. and The Iuka State Bank
- EXCHANGE_MARKET_ACCESS | NEUTRAL | w=11.5 | sec_press_releases | SEC Announces Continuation of Small Business Advisory Committee Meeting
- MACRO_POLICY_PRESSURE | NEUTRAL | w=9.775 | federal_reserve_press | Federal Reserve issues FOMC statement
- MACRO_POLICY_PRESSURE | BEARISH | w=9.6746 | market_narrative | Market narrative theme: MACRO_POLICY
- MIXED_EVENT_CONFLICT | NEUTRAL | w=8.8 | causal_intelligence | Causal context: MULTI_SOURCE_EVENT_CONSENSUS
- EXCHANGE_MARKET_ACCESS | NEUTRAL | w=7.475 | sec_press_releases | Small Business Forum’s Report to Congress Highlights Recommendations to Improve Capital-Raising Policy

Recommendations:
→ automatic_event_collector، causal_intelligence، market_narrative و narrative_decision را قبل از root_cause اجرا کن.
→ اگر primary_root_cause چند هفته متوالی با outcome مثبت/منفی همبستگی داشت، بعداً می‌تواند وارد Root-Cause Gate Simulator شود.
→ برای افزایش دقت، داده‌های derivatives/on-chain/ETF flow را به evidence registry اضافه کن.

Warnings:
⚠️ Root Cause Discovery احتمالات علّی پژوهشی می‌سازد؛ علت قطعی یا سیگنال خرید/فروش نیست.
⚠️ این ماژول از outcome/return آینده برای تشخیص علت استفاده نمی‌کند تا leakage ایجاد نشود.
⚠️ تا وقتی علت‌ها با forward outcomes اعتبارسنجی نشوند، Paper/Live نباید از آن‌ها استفاده کند.
==============================================================================================================