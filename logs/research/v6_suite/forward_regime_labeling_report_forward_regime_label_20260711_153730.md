==============================================================================================================
🧬 Freakto Forward Regime Label Injection Patch v6.2.1
==============================================================================================================
Status                 : FORWARD_REGIME_LABELING_READY
Run ID                 : forward_regime_label_20260711_153730
Apply Changes          : True
Decision Rows          : 57
Known Before / After   : 57 / 57
Unknown Before / After : 0 / 0
Injected Decision Rows : 0
Preserved Direct Rows  : 57
Direct/Text/Proxy      : 24 / 33 / 0
Evaluation Rows        : 56
Patched Evaluations    : 0
Eval Known After       : 56

Decision Regime Counts:
- TRENDING_BULL: 48
- TRENDING_BEAR: 8
- SIDEWAYS: 1

Evaluation Regime Counts:
- TRENDING_BULL: 47
- TRENDING_BEAR: 8
- SIDEWAYS: 1

Backups:
- logs/decisions.csv.bak_v621_20260711_153730
- logs/decision_evaluations.csv.bak_v621_20260711_153730

Recommendations:
→ بعد از اجرای cycle جدید، regime_shadow_gate_dashboard.py --compact را دوباره بررسی کن.

Warnings:
⚠️ Regime injection فقط از داده‌های لحظه تصمیم استفاده می‌کند؛ outcome/return/target/stop استفاده نمی‌شود.
⚠️ برچسب‌های LOW_CONF_PROXY برای Research هستند و باید در Forward واقعی بیشتر validate شوند.
==============================================================================================================