==============================================================================================================
🧭 Freakto Market Narrative Engine v7.2.0
==============================================================================================================
Status                 : MARKET_NARRATIVE_READY
Run ID                 : market_narrative_20260716_130850
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Auto / Manual Events   : 21 / 2
Accepted / Noise       : 3 / 1

Market Narrative:
- Label                : MACRO_POLICY_DOMINANT
- Confidence           : MEDIUM
- Direction            : MIXED_OR_NEUTRAL
- Dominant Theme       : MACRO_POLICY
- Net Direction Score  : -0.0413
- Event Risk           : HIGH
- Tech/Event Conflict  : LOW
- Summary              : Narrative=MACRO_POLICY_DOMINANT; direction=MIXED_OR_NEUTRAL; theme=MACRO_POLICY; net_score=-0.0413; risk=HIGH. محرک اصلی فعلی از sec_press_releases است: SEC Proposes New E-Delivery Approach to Make Information More Readily Accessible and Useful for Investors
- Evidence Strength    : 0.5875 (MEDIUM)
- Claim Status         : PLAUSIBLE_HYPOTHESIS
- Independent Sources  : 3
- Direction Agreement  : 0.5

Alternative Explanations:
- Competing theme: REGULATORY_RISK score=4.0203
- The move may be explained by broad market beta or liquidity rather than the named event.
- The observed event and price move may be correlated without a causal relationship.

Theme Scores:
- MACRO_POLICY: score=-4.0616 | drivers=2 | bull=0 | bear=2
- REGULATORY_RISK: score=4.0203 | drivers=1 | bull=1 | bear=0

Top Narrative Drivers:
- BULLISH | w=4.0203 | REGULATORY_RISK | sec_press_releases | SEC Proposes New E-Delivery Approach to Make Information More Readily Accessible and Useful for Investors
- BEARISH | w=-2.5645 | MACRO_POLICY | federal_reserve_speeches | Bowman, Modernizing Financial Regulation
- BEARISH | w=-1.4971 | MACRO_POLICY | federal_reserve_press | Federal Reserve Board issues enforcement action with TS Banking Group, Inc. and TS Contrarian Bancshares, Inc.

Recommendations:
→ automatic_event_collector_dashboard.py --compact باید قبل از market_narrative_dashboard.py اجرا شود.
→ اگر Narrative و Technical conflict بالا باشد، تصمیم فقط Research/Watchlist بماند.
→ برای ارتقا به Gate، narrative باید در Forward با outcomeهای بعدی validate شود.

Warnings:
⚠️ Market Narrative فقط روایت پژوهشی می‌سازد؛ سیگنال خرید/فروش مستقل نیست.
⚠️ اگر event sourceها نویز HTML/marketing بدهند، v7 آن‌ها را فیلتر می‌کند اما همچنان باید source health بررسی شود.
⚠️ Narrative remains a supported hypothesis, not a proven cause.
==============================================================================================================