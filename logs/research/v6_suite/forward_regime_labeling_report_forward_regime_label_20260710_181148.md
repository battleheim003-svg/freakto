==============================================================================================================
🧬 Freakto Forward Regime Label Injection Patch v6.2.1
==============================================================================================================
Status                 : FORWARD_REGIME_LABELING_READY
Run ID                 : forward_regime_label_20260710_181148
Apply Changes          : True
Decision Rows          : 53
Known Before / After   : 53 / 53
Unknown Before / After : 0 / 0
Injected Decision Rows : 0
Preserved Direct Rows  : 53
Direct/Text/Proxy      : 20 / 33 / 0
Evaluation Rows        : 52
Patched Evaluations    : 0
Eval Known After       : 52

Decision Regime Counts:
- TRENDING_BULL: 45
- TRENDING_BEAR: 8

Evaluation Regime Counts:
- TRENDING_BULL: 44
- TRENDING_BEAR: 8

Backups:
- logs/decisions.csv.bak_v621_20260710_181148
- logs/decision_evaluations.csv.bak_v621_20260710_181148

Recommendations:
→ بعد از اجرای cycle جدید، regime_shadow_gate_dashboard.py --compact را دوباره بررسی کن.

Warnings:
⚠️ Regime injection فقط از داده‌های لحظه تصمیم استفاده می‌کند؛ outcome/return/target/stop استفاده نمی‌شود.
⚠️ برچسب‌های LOW_CONF_PROXY برای Research هستند و باید در Forward واقعی بیشتر validate شوند.
==============================================================================================================