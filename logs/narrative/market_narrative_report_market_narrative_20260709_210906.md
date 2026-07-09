==============================================================================================================
🧭 Freakto Market Narrative Engine v7.1.0
==============================================================================================================
Status                 : MARKET_NARRATIVE_WITH_CONFLICTS
Run ID                 : market_narrative_20260709_210906
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Auto / Manual Events   : 12 / 2
Accepted / Noise       : 7 / 0

Market Narrative:
- Label                : MIXED_NARRATIVE_CONFLICT
- Confidence           : MEDIUM
- Direction            : BEARISH
- Dominant Theme       : MACRO_POLICY
- Net Direction Score  : -25.5204
- Event Risk           : HIGH
- Tech/Event Conflict  : LOW
- Summary              : Narrative=MIXED_NARRATIVE_CONFLICT; direction=BEARISH; theme=MACRO_POLICY; net_score=-25.5204; risk=HIGH. محرک اصلی فعلی از federal_reserve_press است: Federal Reserve Board issues enforcement action with TS Banking Group, Inc. and TS Contrarian Bancshares, Inc.

Theme Scores:
- MACRO_POLICY: score=-18.8861 | drivers=4 | bull=1 | bear=3
- REGULATORY_RISK: score=-6.6343 | drivers=3 | bull=1 | bear=2

Top Narrative Drivers:
- BEARISH | w=-11.0865 | MACRO_POLICY | federal_reserve_press | Federal Reserve Board issues enforcement action with TS Banking Group, Inc. and TS Contrarian Bancshares, Inc.
- BULLISH | w=9.7784 | REGULATORY_RISK | sec_press_releases | SEC to Host Virtual Roundtable on Modernizing IPOs and Expanding Access to Public Markets
- BEARISH | w=-8.532 | MACRO_POLICY | federal_reserve_press | Federal Reserve Board requests comment on a proposal to amend its requirements for banks to maintain anti-money laundering programs
- BEARISH | w=-8.3147 | REGULATORY_RISK | sec_press_releases | SEC Forms New Retail Fraud Working Group
- BEARISH | w=-8.098 | REGULATORY_RISK | manual_events | Example: enforcement headline increasing crypto regulatory risk
- BULLISH | w=7.9546 | MACRO_POLICY | manual_events | Example: dovish macro interpretation supporting risk assets
- BEARISH | w=-7.2222 | MACRO_POLICY | federal_reserve_speeches | Waller, Two Thoughts on the Transmission of Monetary Policy

Contradictions:
⚠️ همزمان eventهای bullish و bearish قوی دیده شد: bull=17.73, bear=43.25

Recommendations:
→ automatic_event_collector_dashboard.py --compact باید قبل از market_narrative_dashboard.py اجرا شود.
→ اگر Narrative و Technical conflict بالا باشد، تصمیم فقط Research/Watchlist بماند.
→ برای ارتقا به Gate، narrative باید در Forward با outcomeهای بعدی validate شود.

Warnings:
⚠️ Market Narrative فقط روایت پژوهشی می‌سازد؛ سیگنال خرید/فروش مستقل نیست.
⚠️ اگر event sourceها نویز HTML/marketing بدهند، v7 آن‌ها را فیلتر می‌کند اما همچنان باید source health بررسی شود.
==============================================================================================================