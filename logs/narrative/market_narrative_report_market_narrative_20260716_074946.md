==============================================================================================================
🧭 Freakto Market Narrative Engine v7.2.0
==============================================================================================================
Status                 : MARKET_NARRATIVE_READY
Run ID                 : market_narrative_20260716_074946
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Auto / Manual Events   : 20 / 2
Accepted / Noise       : 2 / 2

Market Narrative:
- Label                : MACRO_POLICY_DOMINANT
- Confidence           : MEDIUM
- Direction            : BEARISH
- Dominant Theme       : MACRO_POLICY
- Net Direction Score  : -4.1922
- Event Risk           : HIGH
- Tech/Event Conflict  : LOW
- Summary              : Narrative=MACRO_POLICY_DOMINANT; direction=BEARISH; theme=MACRO_POLICY; net_score=-4.1922; risk=HIGH. محرک اصلی فعلی از federal_reserve_speeches است: Bowman, Modernizing Financial Regulation
- Evidence Strength    : 0.5992 (MEDIUM)
- Claim Status         : PLAUSIBLE_HYPOTHESIS
- Independent Sources  : 2
- Direction Agreement  : 1.0

Alternative Explanations:
- The move may be explained by broad market beta or liquidity rather than the named event.
- The observed event and price move may be correlated without a causal relationship.
- An unobserved macro, positioning, or exchange-specific factor may dominate.

Theme Scores:
- MACRO_POLICY: score=-4.1922 | drivers=2 | bull=0 | bear=2

Top Narrative Drivers:
- BEARISH | w=-2.6469 | MACRO_POLICY | federal_reserve_speeches | Bowman, Modernizing Financial Regulation
- BEARISH | w=-1.5453 | MACRO_POLICY | federal_reserve_press | Federal Reserve Board issues enforcement action with TS Banking Group, Inc. and TS Contrarian Bancshares, Inc.

Recommendations:
→ automatic_event_collector_dashboard.py --compact باید قبل از market_narrative_dashboard.py اجرا شود.
→ اگر Narrative و Technical conflict بالا باشد، تصمیم فقط Research/Watchlist بماند.
→ برای ارتقا به Gate، narrative باید در Forward با outcomeهای بعدی validate شود.

Warnings:
⚠️ Market Narrative فقط روایت پژوهشی می‌سازد؛ سیگنال خرید/فروش مستقل نیست.
⚠️ اگر event sourceها نویز HTML/marketing بدهند، v7 آن‌ها را فیلتر می‌کند اما همچنان باید source health بررسی شود.
⚠️ Narrative remains a supported hypothesis, not a proven cause.
==============================================================================================================