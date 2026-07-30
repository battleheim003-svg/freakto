==============================================================================================================
🧭 Freakto Market Narrative Engine v7.2.0
==============================================================================================================
Status                 : MARKET_NARRATIVE_WEAK_EVIDENCE
Run ID                 : market_narrative_20260730_094458
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Auto / Manual Events   : 16 / 2
Accepted / Noise       : 1 / 0

Market Narrative:
- Label                : EVENT_CONTEXT_DOMINANT
- Confidence           : LOW
- Direction            : MIXED_OR_NEUTRAL
- Dominant Theme       : REGULATORY_RISK
- Net Direction Score  : 1.5283
- Event Risk           : HIGH
- Tech/Event Conflict  : LOW
- Summary              : Narrative=EVENT_CONTEXT_DOMINANT; direction=MIXED_OR_NEUTRAL; theme=REGULATORY_RISK; net_score=1.5283; risk=HIGH. محرک اصلی فعلی از sec_press_releases است: SEC Announces Roundtable on Preparations for 24-Hour Trading
- Evidence Strength    : 0.3608 (LOW)
- Claim Status         : WEAK_HYPOTHESIS
- Independent Sources  : 1
- Direction Agreement  : 0.5

Alternative Explanations:
- The move may be explained by broad market beta or liquidity rather than the named event.
- The observed event and price move may be correlated without a causal relationship.
- An unobserved macro, positioning, or exchange-specific factor may dominate.

Theme Scores:
- REGULATORY_RISK: score=1.5283 | drivers=1 | bull=1 | bear=0

Top Narrative Drivers:
- BULLISH | w=1.5283 | REGULATORY_RISK | sec_press_releases | SEC Announces Roundtable on Preparations for 24-Hour Trading

Recommendations:
→ automatic_event_collector_dashboard.py --compact باید قبل از market_narrative_dashboard.py اجرا شود.
→ اگر Narrative و Technical conflict بالا باشد، تصمیم فقط Research/Watchlist بماند.
→ برای ارتقا به Gate، narrative باید در Forward با outcomeهای بعدی validate شود.

Warnings:
⚠️ Market Narrative فقط روایت پژوهشی می‌سازد؛ سیگنال خرید/فروش مستقل نیست.
⚠️ اگر event sourceها نویز HTML/marketing بدهند، v7 آن‌ها را فیلتر می‌کند اما همچنان باید source health بررسی شود.
⚠️ Narrative wording is hypothesis-only because evidence strength is insufficient.
==============================================================================================================