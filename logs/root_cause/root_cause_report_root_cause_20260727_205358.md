==============================================================================================================
🧬 Freakto Root Cause Discovery Engine v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_MIXED_WITH_CONTRADICTIONS
Run ID                 : root_cause_20260727_205358
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Decision Side/Score    : LONG | 75
Narrative              : EVENT_CONTEXT_DOMINANT | MIXED_OR_NEUTRAL | REGULATORY_RISK
Causal Context         : STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION | catalyst=66/100

Root Cause:
- Primary              : LIQUIDITY_VOLUME_FLOW
- Direction            : BULLISH
- Confidence           : LOW
- Probability Share    : 39.28%
- Evidence Quality     : MEDIUM
- Verdict              : PROBABLE_CAUSE_BUT_CONFLICTED
- Summary              : Probable root cause=LIQUIDITY_VOLUME_FLOW; direction=BULLISH; confidence=LOW; share=39.28%. قوی‌ترین evidence از decision_engine_volume است: Volume/flow evidence from Decision Engine | هشدار: شواهد متضاد همزمان وجود دارد.
- Evidence Total       : 6 | official=2 | event_rows=2

Top Cause Hypotheses:
- LIQUIDITY_VOLUME_FLOW: p=39.28% | score=26.92 | dir=BULLISH | evidence=2 | verdict=SUPPORTING_CAUSE
- TECHNICAL_STRUCTURE_MOMENTUM: p=26.26% | score=18.0 | dir=BULLISH | evidence=1 | verdict=SUPPORTING_CAUSE
- REGULATORY_RISK: p=21.28% | score=14.5825 | dir=BEARISH | evidence=2 | verdict=WEAK_SUPPORTING_CAUSE
- REGULATORY_ACCESS_OR_MODERNIZATION: p=13.18% | score=9.035 | dir=BULLISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE

Evidence:
- TECHNICAL_STRUCTURE_MOMENTUM | BULLISH | w=18.0 | decision_engine_features | Decision Engine structure/trend/momentum evidence
- LIQUIDITY_VOLUME_FLOW | BULLISH | w=15.0 | decision_engine_volume | Volume/flow evidence from Decision Engine
- LIQUIDITY_VOLUME_FLOW | NEUTRAL | w=11.92 | causal_intelligence | Causal context: STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION
- REGULATORY_ACCESS_OR_MODERNIZATION | BULLISH | w=9.035 | sec_press_releases | SEC Announces Roundtable on Preparations for 24-Hour Trading
- REGULATORY_RISK | BEARISH | w=7.475 | sec_press_releases | SEC Announces Departure of Principal Deputy Director of Enforcement Sam Waldon
- REGULATORY_RISK | MIXED_OR_NEUTRAL | w=7.1075 | market_narrative | Market narrative theme: REGULATORY_RISK

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