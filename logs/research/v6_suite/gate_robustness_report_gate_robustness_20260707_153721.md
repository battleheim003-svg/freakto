==============================================================================================================
🧠 Freakto Gate Robustness v6.0.0
==============================================================================================================
Status: ROBUSTNESS_BUILDING
Run ID: gate_robustness_20260707_153721
Baseline Net: samples=295 | avg=-0.3351% | win=29.15%

Top Robustness Results:
- QUALITY_VOLUME_HEDGE: LOW_SAMPLE | n=2 | net=0.4311% | stability=50.0% | robust=0.6745
- BNB_LONG_SCORE_GE_60: LOW_SAMPLE | n=11 | net=0.0179% | stability=50.0% | robust=0.0932
- SCORE_60_69: NET_NEGATIVE_AFTER_COST | n=90 | net=-0.2605% | stability=40.0% | robust=-0.2885
- DOGE_SHORT_WATCH: LOW_SAMPLE | n=25 | net=-0.111% | stability=20.0% | robust=-0.3866
- SCORE_GE_80: LOW_SAMPLE | n=20 | net=-0.4094% | stability=40.0% | robust=-0.4597
- ACTIONABLE_SCORE_GE_80: LOW_SAMPLE | n=18 | net=-0.4542% | stability=40.0% | robust=-0.5121
- WATCHLIST: NET_NEGATIVE_AFTER_COST | n=176 | net=-0.2722% | stability=20.0% | robust=-0.5314
- SHORT_ONLY: NET_NEGATIVE_AFTER_COST | n=145 | net=-0.2984% | stability=20.0% | robust=-0.5618
- VOLUME_SCORE_GE_10: NET_NEGATIVE_AFTER_COST | n=34 | net=-0.4245% | stability=20.0% | robust=-0.6892
- RISK_MEDIUM: NET_NEGATIVE_AFTER_COST | n=76 | net=-0.47% | stability=20.0% | robust=-0.7357
- XRP_SHORT_SCORE_GE_60: LOW_SAMPLE | n=15 | net=-0.4656% | stability=20.0% | robust=-0.7576
- HISTORICAL_EDGE_SCORE_GE_1: NET_NEGATIVE_AFTER_COST | n=40 | net=-0.3034% | stability=0.0% | robust=-0.8177

Blockers:
⛔ هیچ Gate بعد از cost و stability به ROBUST_RESEARCH_CANDIDATE نرسید.

Recommendations:
→ Gateهای فعلی بعد از جریمه هزینه و stability کافی نیستند؛ باید feature/gate جدید یا regime split بررسی شود.

Warnings:
⚠️ Multiple-testing penalty اینجا یک تخمین محافظه‌کارانه است؛ جایگزین قطعی PBO آکادمیک نیست.
⚠️ Embargo به‌صورت row-based اعمال شده تا با ساختار فعلی CSV سازگار بماند.
==============================================================================================================