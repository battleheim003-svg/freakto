==============================================================================================================
🧬 Freakto Forward Regime Label Injection Patch v6.2.1
==============================================================================================================
Status                 : FORWARD_REGIME_LABELING_READY
Run ID                 : forward_regime_label_20260711_113551
Apply Changes          : True
Decision Rows          : 56
Known Before / After   : 56 / 56
Unknown Before / After : 0 / 0
Injected Decision Rows : 0
Preserved Direct Rows  : 56
Direct/Text/Proxy      : 23 / 33 / 0
Evaluation Rows        : 55
Patched Evaluations    : 0
Eval Known After       : 55

Decision Regime Counts:
- TRENDING_BULL: 47
- TRENDING_BEAR: 8
- SIDEWAYS: 1

Evaluation Regime Counts:
- TRENDING_BULL: 46
- TRENDING_BEAR: 8
- SIDEWAYS: 1

Backups:
- logs/decisions.csv.bak_v621_20260711_113551
- logs/decision_evaluations.csv.bak_v621_20260711_113551

Recommendations:
→ بعد از اجرای cycle جدید، regime_shadow_gate_dashboard.py --compact را دوباره بررسی کن.

Warnings:
⚠️ Regime injection فقط از داده‌های لحظه تصمیم استفاده می‌کند؛ outcome/return/target/stop استفاده نمی‌شود.
⚠️ برچسب‌های LOW_CONF_PROXY برای Research هستند و باید در Forward واقعی بیشتر validate شوند.
==============================================================================================================