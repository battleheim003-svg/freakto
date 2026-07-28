==============================================================================================================
🧬 Freakto Root Cause Discovery Engine v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_MIXED_WITH_CONTRADICTIONS
Run ID                 : root_cause_20260728_101430
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Decision Side/Score    : NEUTRAL | 39
Narrative              : EVENT_CONTEXT_DOMINANT | MIXED_OR_NEUTRAL | REGULATORY_RISK
Causal Context         : STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION | catalyst=50/100

Root Cause:
- Primary              : TECHNICAL_STRUCTURE_MOMENTUM
- Direction            : MIXED_OR_NEUTRAL
- Confidence           : LOW
- Probability Share    : 28.52%
- Evidence Quality     : MEDIUM
- Verdict              : PROBABLE_CAUSE_BUT_CONFLICTED
- Summary              : Probable root cause=TECHNICAL_STRUCTURE_MOMENTUM; direction=MIXED_OR_NEUTRAL; confidence=LOW; share=28.52%. قوی‌ترین evidence از decision_engine_features است: Decision Engine structure/trend/momentum evidence | هشدار: شواهد متضاد همزمان وجود دارد.
- Evidence Total       : 6 | official=3 | event_rows=3

Top Cause Hypotheses:
- TECHNICAL_STRUCTURE_MOMENTUM: p=28.52% | score=18.0 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=SUPPORTING_CAUSE
- REGULATORY_RISK: p=23.09% | score=14.5743 | dir=BEARISH | evidence=2 | verdict=WEAK_SUPPORTING_CAUSE
- EXCHANGE_MARKET_ACCESS: p=18.22% | score=11.5 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- LIQUIDITY_VOLUME_FLOW: p=15.85% | score=10.0 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- REGULATORY_ACCESS_OR_MODERNIZATION: p=14.32% | score=9.035 | dir=BULLISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE

Evidence:
- TECHNICAL_STRUCTURE_MOMENTUM | NEUTRAL | w=18.0 | decision_engine_features | Decision Engine structure/trend/momentum evidence
- EXCHANGE_MARKET_ACCESS | NEUTRAL | w=11.5 | sec_press_releases | Small Business Forum’s Report to Congress Highlights Recommendations to Improve Capital-Raising Policy
- LIQUIDITY_VOLUME_FLOW | NEUTRAL | w=10.0 | causal_intelligence | Causal context: STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION
- REGULATORY_ACCESS_OR_MODERNIZATION | BULLISH | w=9.035 | sec_press_releases | SEC Announces Roundtable on Preparations for 24-Hour Trading
- REGULATORY_RISK | BEARISH | w=7.475 | sec_press_releases | SEC Announces Departure of Principal Deputy Director of Enforcement Sam Waldon
- REGULATORY_RISK | MIXED_OR_NEUTRAL | w=7.0993 | market_narrative | Market narrative theme: REGULATORY_RISK

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