==============================================================================================================
🧭 Freakto Market Narrative Engine v7.2.0
==============================================================================================================
Status                 : MARKET_NARRATIVE_WEAK_EVIDENCE
Run ID                 : market_narrative_20260720_112432
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Auto / Manual Events   : 22 / 2
Accepted / Noise       : 3 / 0

Market Narrative:
- Label                : MACRO_POLICY_DOMINANT
- Confidence           : LOW
- Direction            : MIXED_OR_NEUTRAL
- Dominant Theme       : MACRO_POLICY
- Net Direction Score  : -2.3921
- Event Risk           : HIGH
- Tech/Event Conflict  : LOW
- Summary              : Narrative=MACRO_POLICY_DOMINANT; direction=MIXED_OR_NEUTRAL; theme=MACRO_POLICY; net_score=-2.3921; risk=HIGH. محرک اصلی فعلی از federal_reserve_press است: Agencies issue joint statement on handling of highly sensitive information during bank examinations
- Evidence Strength    : 0.5042 (LOW)
- Claim Status         : WEAK_HYPOTHESIS
- Independent Sources  : 2
- Direction Agreement  : 0.5

Alternative Explanations:
- Competing theme: REGULATORY_RISK score=2.2939
- The move may be explained by broad market beta or liquidity rather than the named event.
- The observed event and price move may be correlated without a causal relationship.

Theme Scores:
- MACRO_POLICY: score=-4.686 | drivers=2 | bull=0 | bear=2
- REGULATORY_RISK: score=2.2939 | drivers=1 | bull=1 | bear=0

Top Narrative Drivers:
- BEARISH | w=-2.3639 | MACRO_POLICY | federal_reserve_press | Agencies issue joint statement on handling of highly sensitive information during bank examinations
- BEARISH | w=-2.3221 | MACRO_POLICY | federal_reserve_press | Federal Reserve Board issues enforcement action with former chief lending officer of Heritage State Bank
- BULLISH | w=2.2939 | REGULATORY_RISK | sec_press_releases | SEC Proposes New E-Delivery Approach to Make Information More Readily Accessible and Useful for Investors

Recommendations:
→ automatic_event_collector_dashboard.py --compact باید قبل از market_narrative_dashboard.py اجرا شود.
→ اگر Narrative و Technical conflict بالا باشد، تصمیم فقط Research/Watchlist بماند.
→ برای ارتقا به Gate، narrative باید در Forward با outcomeهای بعدی validate شود.

Warnings:
⚠️ Market Narrative فقط روایت پژوهشی می‌سازد؛ سیگنال خرید/فروش مستقل نیست.
⚠️ اگر event sourceها نویز HTML/marketing بدهند، v7 آن‌ها را فیلتر می‌کند اما همچنان باید source health بررسی شود.
⚠️ Narrative wording is hypothesis-only because evidence strength is insufficient.
==============================================================================================================