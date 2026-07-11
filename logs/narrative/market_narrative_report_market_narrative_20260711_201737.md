==============================================================================================================
🧭 Freakto Market Narrative Engine v7.2.0
==============================================================================================================
Status                 : MARKET_NARRATIVE_READY
Run ID                 : market_narrative_20260711_201737
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Auto / Manual Events   : 12 / 2
Accepted / Noise       : 5 / 2

Market Narrative:
- Label                : MACRO_POLICY_DOMINANT
- Confidence           : HIGH
- Direction            : BEARISH
- Dominant Theme       : MACRO_POLICY
- Net Direction Score  : -19.1678
- Event Risk           : HIGH
- Tech/Event Conflict  : LOW
- Summary              : Narrative=MACRO_POLICY_DOMINANT; direction=BEARISH; theme=MACRO_POLICY; net_score=-19.1678; risk=HIGH. محرک اصلی فعلی از federal_reserve_press است: Federal Reserve Board issues enforcement action with TS Banking Group, Inc. and TS Contrarian Bancshares, Inc.
- Evidence Strength    : 0.87 (STRONG)
- Claim Status         : SUPPORTED_HYPOTHESIS
- Independent Sources  : 3
- Direction Agreement  : 0.8

Alternative Explanations:
- Competing theme: REGULATORY_RISK score=1.1056
- Conflicting evidence: SEC to Host Virtual Roundtable on Modernizing IPOs and Expanding Access to Public Markets
- The move may be explained by broad market beta or liquidity rather than the named event.

Theme Scores:
- MACRO_POLICY: score=-20.2734 | drivers=3 | bull=0 | bear=3
- REGULATORY_RISK: score=1.1056 | drivers=2 | bull=1 | bear=1

Top Narrative Drivers:
- BEARISH | w=-8.3739 | MACRO_POLICY | federal_reserve_press | Federal Reserve Board issues enforcement action with TS Banking Group, Inc. and TS Contrarian Bancshares, Inc.
- BULLISH | w=7.3859 | REGULATORY_RISK | sec_press_releases | SEC to Host Virtual Roundtable on Modernizing IPOs and Expanding Access to Public Markets
- BEARISH | w=-6.4444 | MACRO_POLICY | federal_reserve_press | Federal Reserve Board requests comment on a proposal to amend its requirements for banks to maintain anti-money laundering programs
- BEARISH | w=-6.2803 | REGULATORY_RISK | sec_press_releases | SEC Forms New Retail Fraud Working Group
- BEARISH | w=-5.4551 | MACRO_POLICY | federal_reserve_speeches | Waller, Two Thoughts on the Transmission of Monetary Policy

Recommendations:
→ automatic_event_collector_dashboard.py --compact باید قبل از market_narrative_dashboard.py اجرا شود.
→ اگر Narrative و Technical conflict بالا باشد، تصمیم فقط Research/Watchlist بماند.
→ برای ارتقا به Gate، narrative باید در Forward با outcomeهای بعدی validate شود.

Warnings:
⚠️ Market Narrative فقط روایت پژوهشی می‌سازد؛ سیگنال خرید/فروش مستقل نیست.
⚠️ اگر event sourceها نویز HTML/marketing بدهند، v7 آن‌ها را فیلتر می‌کند اما همچنان باید source health بررسی شود.
⚠️ Narrative remains a supported hypothesis, not a proven cause.
==============================================================================================================