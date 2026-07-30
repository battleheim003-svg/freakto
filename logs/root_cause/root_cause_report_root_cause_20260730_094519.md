==============================================================================================================
🧬 Freakto Root Cause Discovery Engine v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_WEAK_OR_DISTRIBUTED
Run ID                 : root_cause_20260730_094519
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Decision Side/Score    : NEUTRAL | 38
Narrative              : EVENT_CONTEXT_DOMINANT | MIXED_OR_NEUTRAL | REGULATORY_RISK
Causal Context         : AUTO_EVENTS_CONTEXT | catalyst=71/100

Root Cause:
- Primary              : TECHNICAL_STRUCTURE_MOMENTUM
- Direction            : MIXED_OR_NEUTRAL
- Confidence           : LOW
- Probability Share    : 32.23%
- Evidence Quality     : MEDIUM
- Verdict              : WEAK_OR_DISTRIBUTED_ROOT_CAUSE
- Summary              : Probable root cause=TECHNICAL_STRUCTURE_MOMENTUM; direction=MIXED_OR_NEUTRAL; confidence=LOW; share=32.23%. قوی‌ترین evidence از decision_engine_features است: Decision Engine structure/trend/momentum evidence
- Evidence Total       : 6 | official=3 | event_rows=3

Top Cause Hypotheses:
- TECHNICAL_STRUCTURE_MOMENTUM: p=32.23% | score=18.0 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=SUPPORTING_CAUSE
- MACRO_POLICY_PRESSURE: p=20.59% | score=11.5 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- EXCHANGE_MARKET_ACCESS: p=17.5% | score=9.775 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- REGULATORY_ACCESS_OR_MODERNIZATION: p=16.18% | score=9.035 | dir=BULLISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- REGULATORY_RISK: p=13.49% | score=7.5349 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE

Evidence:
- TECHNICAL_STRUCTURE_MOMENTUM | NEUTRAL | w=18.0 | decision_engine_features | Decision Engine structure/trend/momentum evidence
- UNKNOWN_OR_INSUFFICIENT_EVIDENCE | NEUTRAL | w=12.52 | causal_intelligence | Causal context: AUTO_EVENTS_CONTEXT
- MACRO_POLICY_PRESSURE | NEUTRAL | w=11.5 | federal_reserve_press | Federal Reserve issues FOMC statement
- EXCHANGE_MARKET_ACCESS | NEUTRAL | w=9.775 | sec_press_releases | Small Business Forum’s Report to Congress Highlights Recommendations to Improve Capital-Raising Policy
- REGULATORY_ACCESS_OR_MODERNIZATION | BULLISH | w=9.035 | sec_press_releases | SEC Announces Roundtable on Preparations for 24-Hour Trading
- REGULATORY_RISK | MIXED_OR_NEUTRAL | w=7.5349 | market_narrative | Market narrative theme: REGULATORY_RISK

Recommendations:
→ automatic_event_collector، causal_intelligence، market_narrative و narrative_decision را قبل از root_cause اجرا کن.
→ اگر primary_root_cause چند هفته متوالی با outcome مثبت/منفی همبستگی داشت، بعداً می‌تواند وارد Root-Cause Gate Simulator شود.
→ برای افزایش دقت، داده‌های derivatives/on-chain/ETF flow را به evidence registry اضافه کن.

Warnings:
⚠️ Root Cause Discovery احتمالات علّی پژوهشی می‌سازد؛ علت قطعی یا سیگنال خرید/فروش نیست.
⚠️ این ماژول از outcome/return آینده برای تشخیص علت استفاده نمی‌کند تا leakage ایجاد نشود.
⚠️ تا وقتی علت‌ها با forward outcomes اعتبارسنجی نشوند، Paper/Live نباید از آن‌ها استفاده کند.
==============================================================================================================