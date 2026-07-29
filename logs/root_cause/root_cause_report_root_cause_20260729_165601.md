==============================================================================================================
🧬 Freakto Root Cause Discovery Engine v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_MIXED_WITH_CONTRADICTIONS
Run ID                 : root_cause_20260729_165601
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Decision Side/Score    : SHORT | 62
Narrative              : MIXED_NARRATIVE_CONFLICT | MIXED_OR_NEUTRAL | REGULATORY_RISK
Causal Context         : STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION | catalyst=69/100

Root Cause:
- Primary              : LIQUIDITY_VOLUME_FLOW
- Direction            : BEARISH
- Confidence           : LOW
- Probability Share    : 32.58%
- Evidence Quality     : MEDIUM
- Verdict              : PROBABLE_CAUSE_BUT_CONFLICTED
- Summary              : Probable root cause=LIQUIDITY_VOLUME_FLOW; direction=BEARISH; confidence=LOW; share=32.58%. قوی‌ترین evidence از decision_engine_volume است: Volume/flow evidence from Decision Engine | هشدار: شواهد متضاد همزمان وجود دارد.
- Evidence Total       : 7 | official=2 | event_rows=2

Top Cause Hypotheses:
- LIQUIDITY_VOLUME_FLOW: p=32.58% | score=24.21 | dir=BEARISH | evidence=2 | verdict=SUPPORTING_CAUSE
- TECHNICAL_STRUCTURE_MOMENTUM: p=24.22% | score=18.0 | dir=BEARISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- EXCHANGE_MARKET_ACCESS: p=13.16% | score=9.775 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- REGULATORY_ACCESS_OR_MODERNIZATION: p=12.16% | score=9.035 | dir=BULLISH | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- REGULATORY_RISK: p=10.22% | score=7.5913 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE
- MIXED_EVENT_CONFLICT: p=7.66% | score=5.6934 | dir=MIXED_OR_NEUTRAL | evidence=1 | verdict=WEAK_SUPPORTING_CAUSE

Evidence:
- TECHNICAL_STRUCTURE_MOMENTUM | BEARISH | w=18.0 | decision_engine_features | Decision Engine structure/trend/momentum evidence
- LIQUIDITY_VOLUME_FLOW | BEARISH | w=15.0 | decision_engine_volume | Volume/flow evidence from Decision Engine
- EXCHANGE_MARKET_ACCESS | NEUTRAL | w=9.775 | sec_press_releases | Small Business Forum’s Report to Congress Highlights Recommendations to Improve Capital-Raising Policy
- LIQUIDITY_VOLUME_FLOW | NEUTRAL | w=9.21 | causal_intelligence | Causal context: STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION
- REGULATORY_ACCESS_OR_MODERNIZATION | BULLISH | w=9.035 | sec_press_releases | SEC Announces Roundtable on Preparations for 24-Hour Trading
- REGULATORY_RISK | MIXED_OR_NEUTRAL | w=7.5913 | market_narrative | Market narrative theme: REGULATORY_RISK
- MIXED_EVENT_CONFLICT | NEUTRAL | w=5.6934 | market_narrative | Narrative has mixed/conflicting drivers

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