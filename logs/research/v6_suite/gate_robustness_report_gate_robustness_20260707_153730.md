==============================================================================================================
🧠 Freakto Gate Robustness v6.0.0
==============================================================================================================
Status: ROBUSTNESS_BUILDING
Run ID: gate_robustness_20260707_153730
Baseline Net: samples=295 | avg=-0.5447% | win=33.9%

Top Robustness Results:
- QUALITY_VOLUME_HEDGE: LOW_SAMPLE | n=2 | net=0.5295% | stability=50.0% | robust=0.7729
- VOLUME_SCORE_GE_10: NET_NEGATIVE_AFTER_COST | n=34 | net=-0.4942% | stability=60.0% | robust=-0.3789
- DOGE_SHORT_WATCH: LOW_SAMPLE | n=25 | net=-0.1323% | stability=20.0% | robust=-0.4079
- XRP_SHORT_SCORE_GE_60: LOW_SAMPLE | n=15 | net=-0.4494% | stability=40.0% | robust=-0.5014
- WATCHLIST: NET_NEGATIVE_AFTER_COST | n=176 | net=-0.4853% | stability=40.0% | robust=-0.5046
- HISTORICAL_EDGE_SCORE_GE_1: NET_NEGATIVE_AFTER_COST | n=40 | net=-0.2845% | stability=20.0% | robust=-0.5588
- SHORT_ONLY: NET_NEGATIVE_AFTER_COST | n=145 | net=-0.5385% | stability=40.0% | robust=-0.5619
- QUALITY_STRUCTURE_RISK_MEDIUM: NET_NEGATIVE_AFTER_COST | n=41 | net=-0.5782% | stability=40.0% | robust=-0.6099
- SCORE_GE_80: LOW_SAMPLE | n=20 | net=-0.6521% | stability=40.0% | robust=-0.7024
- SCORE_60_69: NET_NEGATIVE_AFTER_COST | n=90 | net=-0.5078% | stability=20.0% | robust=-0.7758
- RISK_MEDIUM: NET_NEGATIVE_AFTER_COST | n=76 | net=-0.5408% | stability=20.0% | robust=-0.8065
- STRUCTURE_SCORE_GE_10: NET_NEGATIVE_AFTER_COST | n=86 | net=-0.674% | stability=20.0% | robust=-0.9402

Blockers:
⛔ هیچ Gate بعد از cost و stability به ROBUST_RESEARCH_CANDIDATE نرسید.

Recommendations:
→ Gateهای فعلی بعد از جریمه هزینه و stability کافی نیستند؛ باید feature/gate جدید یا regime split بررسی شود.

Warnings:
⚠️ Multiple-testing penalty اینجا یک تخمین محافظه‌کارانه است؛ جایگزین قطعی PBO آکادمیک نیست.
⚠️ Embargo به‌صورت row-based اعمال شده تا با ساختار فعلی CSV سازگار بماند.
==============================================================================================================