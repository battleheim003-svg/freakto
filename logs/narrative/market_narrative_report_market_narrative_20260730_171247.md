==============================================================================================================
🧭 Freakto Market Narrative Engine v7.2.0
==============================================================================================================
Status                 : MARKET_NARRATIVE_WEAK_EVIDENCE
Run ID                 : market_narrative_20260730_171247
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Auto / Manual Events   : 18 / 2
Accepted / Noise       : 2 / 0

Market Narrative:
- Label                : MACRO_POLICY_DOMINANT
- Confidence           : LOW
- Direction            : BEARISH
- Dominant Theme       : MACRO_POLICY
- Net Direction Score  : -7.9446
- Event Risk           : HIGH
- Tech/Event Conflict  : LOW
- Summary              : Narrative=MACRO_POLICY_DOMINANT; direction=BEARISH; theme=MACRO_POLICY; net_score=-7.9446; risk=HIGH. محرک اصلی فعلی از federal_reserve_press است: Federal Reserve Board issues enforcement actions with former employee of Regions Bank and former employee of First Inter
- Evidence Strength    : 0.5158 (LOW)
- Claim Status         : WEAK_HYPOTHESIS
- Independent Sources  : 1
- Direction Agreement  : 1.0

Alternative Explanations:
- The move may be explained by broad market beta or liquidity rather than the named event.
- The observed event and price move may be correlated without a causal relationship.
- An unobserved macro, positioning, or exchange-specific factor may dominate.

Theme Scores:
- MACRO_POLICY: score=-7.9446 | drivers=2 | bull=0 | bear=2

Top Narrative Drivers:
- BEARISH | w=-3.9723 | MACRO_POLICY | federal_reserve_press | Federal Reserve Board issues enforcement actions with former employee of Regions Bank and former employee of First Interstate Bank
- BEARISH | w=-3.9723 | MACRO_POLICY | federal_reserve_press | Federal Reserve Board issues enforcement action with Iuka Bancshares, Inc. and The Iuka State Bank

Recommendations:
→ automatic_event_collector_dashboard.py --compact باید قبل از market_narrative_dashboard.py اجرا شود.
→ اگر Narrative و Technical conflict بالا باشد، تصمیم فقط Research/Watchlist بماند.
→ برای ارتقا به Gate، narrative باید در Forward با outcomeهای بعدی validate شود.

Warnings:
⚠️ Market Narrative فقط روایت پژوهشی می‌سازد؛ سیگنال خرید/فروش مستقل نیست.
⚠️ اگر event sourceها نویز HTML/marketing بدهند، v7 آن‌ها را فیلتر می‌کند اما همچنان باید source health بررسی شود.
⚠️ Narrative wording is hypothesis-only because evidence strength is insufficient.
==============================================================================================================