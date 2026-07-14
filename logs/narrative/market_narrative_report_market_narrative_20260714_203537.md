==============================================================================================================
🧭 Freakto Market Narrative Engine v7.2.0
==============================================================================================================
Status                 : MARKET_NARRATIVE_WEAK_EVIDENCE
Run ID                 : market_narrative_20260714_203537
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Auto / Manual Events   : 19 / 2
Accepted / Noise       : 3 / 2

Market Narrative:
- Label                : MACRO_POLICY_DOMINANT
- Confidence           : LOW
- Direction            : BEARISH
- Dominant Theme       : MACRO_POLICY
- Net Direction Score  : -3.4895
- Event Risk           : HIGH
- Tech/Event Conflict  : LOW
- Summary              : Narrative=MACRO_POLICY_DOMINANT; direction=BEARISH; theme=MACRO_POLICY; net_score=-3.4895; risk=HIGH. محرک اصلی فعلی از federal_reserve_speeches است: Bowman, Modernizing Financial Regulation
- Evidence Strength    : 0.5492 (LOW)
- Claim Status         : WEAK_HYPOTHESIS
- Independent Sources  : 3
- Direction Agreement  : 0.6667

Alternative Explanations:
- Competing theme: REGULATORY_RISK score=1.681
- Conflicting evidence: SEC to Host Virtual Roundtable on Modernizing IPOs and Expanding Access to Public Markets
- The move may be explained by broad market beta or liquidity rather than the named event.

Theme Scores:
- MACRO_POLICY: score=-5.1705 | drivers=2 | bull=0 | bear=2
- REGULATORY_RISK: score=1.681 | drivers=1 | bull=1 | bear=0

Top Narrative Drivers:
- BEARISH | w=-3.2646 | MACRO_POLICY | federal_reserve_speeches | Bowman, Modernizing Financial Regulation
- BEARISH | w=-1.9059 | MACRO_POLICY | federal_reserve_press | Federal Reserve Board issues enforcement action with TS Banking Group, Inc. and TS Contrarian Bancshares, Inc.
- BULLISH | w=1.681 | REGULATORY_RISK | sec_press_releases | SEC to Host Virtual Roundtable on Modernizing IPOs and Expanding Access to Public Markets

Recommendations:
→ automatic_event_collector_dashboard.py --compact باید قبل از market_narrative_dashboard.py اجرا شود.
→ اگر Narrative و Technical conflict بالا باشد، تصمیم فقط Research/Watchlist بماند.
→ برای ارتقا به Gate، narrative باید در Forward با outcomeهای بعدی validate شود.

Warnings:
⚠️ Market Narrative فقط روایت پژوهشی می‌سازد؛ سیگنال خرید/فروش مستقل نیست.
⚠️ اگر event sourceها نویز HTML/marketing بدهند، v7 آن‌ها را فیلتر می‌کند اما همچنان باید source health بررسی شود.
⚠️ Narrative wording is hypothesis-only because evidence strength is insufficient.
==============================================================================================================