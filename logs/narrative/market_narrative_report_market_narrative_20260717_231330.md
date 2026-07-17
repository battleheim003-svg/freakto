==============================================================================================================
🧭 Freakto Market Narrative Engine v7.2.0
==============================================================================================================
Status                 : MARKET_NARRATIVE_WITH_CONFLICTS
Run ID                 : market_narrative_20260717_231330
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Auto / Manual Events   : 23 / 2
Accepted / Noise       : 4 / 0

Market Narrative:
- Label                : MIXED_NARRATIVE_CONFLICT
- Confidence           : MEDIUM
- Direction            : BEARISH
- Dominant Theme       : MACRO_POLICY
- Net Direction Score  : -5.5162
- Event Risk           : HIGH
- Tech/Event Conflict  : HIGH
- Summary              : Narrative=MIXED_NARRATIVE_CONFLICT; direction=BEARISH; theme=MACRO_POLICY; net_score=-5.5162; risk=HIGH. محرک اصلی فعلی از federal_reserve_press است: Agencies issue joint statement on handling of highly sensitive information during bank examinations
- Evidence Strength    : 0.6 (MEDIUM)
- Claim Status         : PLAUSIBLE_HYPOTHESIS
- Independent Sources  : 3
- Direction Agreement  : 0.75

Alternative Explanations:
- Competing theme: REGULATORY_RISK score=3.2822
- Conflicting evidence: SEC Proposes New E-Delivery Approach to Make Information More Readily Accessible and Useful for Investors
- The move may be explained by broad market beta or liquidity rather than the named event.

Theme Scores:
- MACRO_POLICY: score=-8.7984 | drivers=3 | bull=0 | bear=3
- REGULATORY_RISK: score=3.2822 | drivers=1 | bull=1 | bear=0

Top Narrative Drivers:
- BEARISH | w=-3.3823 | MACRO_POLICY | federal_reserve_press | Agencies issue joint statement on handling of highly sensitive information during bank examinations
- BEARISH | w=-3.3225 | MACRO_POLICY | federal_reserve_press | Federal Reserve Board issues enforcement action with former chief lending officer of Heritage State Bank
- BULLISH | w=3.2822 | REGULATORY_RISK | sec_press_releases | SEC Proposes New E-Delivery Approach to Make Information More Readily Accessible and Useful for Investors
- BEARISH | w=-2.0936 | MACRO_POLICY | federal_reserve_speeches | Bowman, Modernizing Financial Regulation

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