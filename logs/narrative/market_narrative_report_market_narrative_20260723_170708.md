==============================================================================================================
🧭 Freakto Market Narrative Engine v7.2.0
==============================================================================================================
Status                 : MARKET_NARRATIVE_WEAK_EVIDENCE
Run ID                 : market_narrative_20260723_170708
Symbol / TF            : BTC/USDT | 4h
Lookback Hours         : 168
Auto / Manual Events   : 16 / 2
Accepted / Noise       : 3 / 0

Market Narrative:
- Label                : MACRO_POLICY_DOMINANT
- Confidence           : LOW
- Direction            : MIXED_OR_NEUTRAL
- Dominant Theme       : MACRO_POLICY
- Net Direction Score  : -0.9324
- Event Risk           : HIGH
- Tech/Event Conflict  : LOW
- Summary              : Narrative=MACRO_POLICY_DOMINANT; direction=MIXED_OR_NEUTRAL; theme=MACRO_POLICY; net_score=-0.9324; risk=HIGH. محرک اصلی فعلی از sec_press_releases است: SEC Announces Roundtable on Preparations for 24-Hour Trading
- Evidence Strength    : 0.5042 (LOW)
- Claim Status         : WEAK_HYPOTHESIS
- Independent Sources  : 2
- Direction Agreement  : 0.5

Alternative Explanations:
- Competing theme: REGULATORY_RISK score=0.5561
- The move may be explained by broad market beta or liquidity rather than the named event.
- The observed event and price move may be correlated without a causal relationship.

Theme Scores:
- MACRO_POLICY: score=-1.4885 | drivers=1 | bull=0 | bear=1
- REGULATORY_RISK: score=0.5561 | drivers=2 | bull=1 | bear=1

Top Narrative Drivers:
- BULLISH | w=3.9761 | REGULATORY_RISK | sec_press_releases | SEC Announces Roundtable on Preparations for 24-Hour Trading
- BEARISH | w=-3.42 | REGULATORY_RISK | sec_press_releases | SEC Announces Departure of Principal Deputy Director of Enforcement Sam Waldon
- BEARISH | w=-1.4885 | MACRO_POLICY | federal_reserve_press | Agencies issue joint statement on handling of highly sensitive information during bank examinations

Recommendations:
→ automatic_event_collector_dashboard.py --compact باید قبل از market_narrative_dashboard.py اجرا شود.
→ اگر Narrative و Technical conflict بالا باشد، تصمیم فقط Research/Watchlist بماند.
→ برای ارتقا به Gate، narrative باید در Forward با outcomeهای بعدی validate شود.

Warnings:
⚠️ Market Narrative فقط روایت پژوهشی می‌سازد؛ سیگنال خرید/فروش مستقل نیست.
⚠️ اگر event sourceها نویز HTML/marketing بدهند، v7 آن‌ها را فیلتر می‌کند اما همچنان باید source health بررسی شود.
⚠️ Narrative wording is hypothesis-only because evidence strength is insufficient.
==============================================================================================================