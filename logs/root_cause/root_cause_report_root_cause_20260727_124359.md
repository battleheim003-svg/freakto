==============================================================================================================
🧬 Freakto Root Cause Discovery Engine v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_MIXED_WITH_CONTRADICTIONS
Run ID                 : root_cause_20260727_124359
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Decision Side/Score    : NEUTRAL | 20
Narrative              : EVENT_CONTEXT_DOMINANT | MIXED_OR_NEUTRAL | REGULATORY_RISK
Causal Context         : STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION | catalyst=69/100

Root Cause:
- Primary              : TECHNICAL_STRUCTURE_MOMENTUM
- Direction            : MIXED_OR_NEUTRAL
- Confidence           : LOW
- Probability Share    : 33.39%
- Evidence Quality     : MEDIUM
- Verdict              : PROBABLE_CAUSE_BUT_CONFLICTED
- Summary              : Probable root cause=TECHNICAL_STRUCTURE_MOMENTUM; direction=MIXED_OR_NEUTRAL; confidence=LOW; share=33.39%. قوی‌ترین evidence از decision_engine_features است: Decision Engine structure/trend/momentum evidence | هشدار: شواهد متضاد همزمان وجود دارد.
- Evidence Total       : 5 | official=2 | event_rows=2

Top Cause Hypotheses:
- TECHNICAL_STRUCTURE_MOMENTUM: p=33.39% | score=18.0 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=SUPPORTING_CAUSE
- REGULATORY_RISK: p=27.06% | score=14.5878 | dir=BEARISH | evidence=2 | verdict=SUPPORTING_CAUSE
- LIQUIDITY_VOLUME_FLOW: p=22.78% | score=12.28 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- REGULATORY_ACCESS_OR_MODERNIZATION: p=16.76% | score=9.035 | dir=BULLISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE

Evidence:
- TECHNICAL_STRUCTURE_MOMENTUM | NEUTRAL | w=18.0 | decision_engine_features | Decision Engine structure/trend/momentum evidence
- LIQUIDITY_VOLUME_FLOW | NEUTRAL | w=12.28 | causal_intelligence | Causal context: STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION
- REGULATORY_ACCESS_OR_MODERNIZATION | BULLISH | w=9.035 | sec_press_releases | SEC Announces Roundtable on Preparations for 24-Hour Trading
- REGULATORY_RISK | BEARISH | w=7.475 | sec_press_releases | SEC Announces Departure of Principal Deputy Director of Enforcement Sam Waldon
- REGULATORY_RISK | MIXED_OR_NEUTRAL | w=7.1128 | market_narrative | Market narrative theme: REGULATORY_RISK

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