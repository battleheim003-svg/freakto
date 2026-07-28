==============================================================================================================
🧬 Freakto Root Cause Discovery Engine v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_MIXED_WITH_CONTRADICTIONS
Run ID                 : root_cause_20260728_171626
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Decision Side/Score    : SHORT | 64
Narrative              : EVENT_CONTEXT_DOMINANT | MIXED_OR_NEUTRAL | REGULATORY_RISK
Causal Context         : STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION | catalyst=57/100

Root Cause:
- Primary              : LIQUIDITY_VOLUME_FLOW
- Direction            : BEARISH
- Confidence           : LOW
- Probability Share    : 32.73%
- Evidence Quality     : MEDIUM
- Verdict              : PROBABLE_CAUSE_BUT_CONFLICTED
- Summary              : Probable root cause=LIQUIDITY_VOLUME_FLOW; direction=BEARISH; confidence=LOW; share=32.73%. قوی‌ترین evidence از decision_engine_volume است: Volume/flow evidence from Decision Engine | هشدار: شواهد متضاد همزمان وجود دارد.
- Evidence Total       : 7 | official=3 | event_rows=3

Top Cause Hypotheses:
- LIQUIDITY_VOLUME_FLOW: p=32.73% | score=25.84 | dir=BEARISH | evidence=2 | verdict=SUPPORTING_CAUSE
- TECHNICAL_STRUCTURE_MOMENTUM: p=22.8% | score=18.0 | dir=BEARISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- REGULATORY_RISK: p=18.46% | score=14.5702 | dir=BEARISH | evidence=2 | verdict=WEAK_SUPPORTING_CAUSE
- EXCHANGE_MARKET_ACCESS: p=14.57% | score=11.5 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- REGULATORY_ACCESS_OR_MODERNIZATION: p=11.44% | score=9.035 | dir=BULLISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE

Evidence:
- TECHNICAL_STRUCTURE_MOMENTUM | BEARISH | w=18.0 | decision_engine_features | Decision Engine structure/trend/momentum evidence
- LIQUIDITY_VOLUME_FLOW | BEARISH | w=15.0 | decision_engine_volume | Volume/flow evidence from Decision Engine
- EXCHANGE_MARKET_ACCESS | NEUTRAL | w=11.5 | sec_press_releases | Small Business Forum’s Report to Congress Highlights Recommendations to Improve Capital-Raising Policy
- LIQUIDITY_VOLUME_FLOW | NEUTRAL | w=10.84 | causal_intelligence | Causal context: STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION
- REGULATORY_ACCESS_OR_MODERNIZATION | BULLISH | w=9.035 | sec_press_releases | SEC Announces Roundtable on Preparations for 24-Hour Trading
- REGULATORY_RISK | BEARISH | w=7.475 | sec_press_releases | SEC Announces Departure of Principal Deputy Director of Enforcement Sam Waldon
- REGULATORY_RISK | MIXED_OR_NEUTRAL | w=7.0952 | market_narrative | Market narrative theme: REGULATORY_RISK

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