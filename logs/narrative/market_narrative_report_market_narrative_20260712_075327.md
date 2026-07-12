==============================================================================================================
🧭 Freakto Market Narrative Engine v7.2.0
==============================================================================================================
Status                 : MARKET_NARRATIVE_WITH_CONFLICTS
Run ID                 : market_narrative_20260712_075327
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Auto / Manual Events   : 13 / 2
Accepted / Noise       : 5 / 2

Market Narrative:
- Label                : MIXED_NARRATIVE_CONFLICT
- Confidence           : MEDIUM
- Direction            : BEARISH
- Dominant Theme       : MACRO_POLICY
- Net Direction Score  : -8.2978
- Event Risk           : HIGH
- Tech/Event Conflict  : HIGH
- Summary              : Narrative=MIXED_NARRATIVE_CONFLICT; direction=BEARISH; theme=MACRO_POLICY; net_score=-8.2978; risk=HIGH. محرک اصلی فعلی از federal_reserve_speeches است: Waller, Two Thoughts on the Transmission of Monetary Policy
- Evidence Strength    : 0.6705 (MEDIUM)
- Claim Status         : PLAUSIBLE_HYPOTHESIS
- Independent Sources  : 3
- Direction Agreement  : 0.8

Alternative Explanations:
- Competing theme: REGULATORY_RISK score=0.3611
- Conflicting evidence: SEC to Host Virtual Roundtable on Modernizing IPOs and Expanding Access to Public Markets
- The move may be explained by broad market beta or liquidity rather than the named event.

Theme Scores:
- MACRO_POLICY: score=-8.6589 | drivers=3 | bull=0 | bear=3
- REGULATORY_RISK: score=0.3611 | drivers=2 | bull=1 | bear=1

Top Narrative Drivers:
- BEARISH | w=-3.8184 | MACRO_POLICY | federal_reserve_speeches | Waller, Two Thoughts on the Transmission of Monetary Policy
- BEARISH | w=-2.7354 | MACRO_POLICY | federal_reserve_press | Federal Reserve Board issues enforcement action with TS Banking Group, Inc. and TS Contrarian Bancshares, Inc.
- BULLISH | w=2.4126 | REGULATORY_RISK | sec_press_releases | SEC to Host Virtual Roundtable on Modernizing IPOs and Expanding Access to Public Markets
- BEARISH | w=-2.1051 | MACRO_POLICY | federal_reserve_press | Federal Reserve Board requests comment on a proposal to amend its requirements for banks to maintain anti-money laundering programs
- BEARISH | w=-2.0515 | REGULATORY_RISK | sec_press_releases | SEC Forms New Retail Fraud Working Group

Contradictions:
⚠️ Causal Intelligence تضاد HIGH با context تکنیکال گزارش کرده است.

Recommendations:
→ automatic_event_collector_dashboard.py --compact باید قبل از market_narrative_dashboard.py اجرا شود.
→ اگر Narrative و Technical conflict بالا باشد، تصمیم فقط Research/Watchlist بماند.
→ برای ارتقا به Gate، narrative باید در Forward با outcomeهای بعدی validate شود.

Warnings:
⚠️ Market Narrative فقط روایت پژوهشی می‌سازد؛ سیگنال خرید/فروش مستقل نیست.
⚠️ اگر event sourceها نویز HTML/marketing بدهند، v7 آن‌ها را فیلتر می‌کند اما همچنان باید source health بررسی شود.
⚠️ Narrative remains a supported hypothesis, not a proven cause.
==============================================================================================================