==============================================================================================================
🧬 Freakto Forward Regime Label Injection Patch v6.2.1
==============================================================================================================
Status                 : FORWARD_REGIME_LABELING_READY
Run ID                 : forward_regime_label_20260710_233822
Apply Changes          : False
Decision Rows          : 54
Known Before / After   : 54 / 54
Unknown Before / After : 0 / 0
Injected Decision Rows : 0
Preserved Direct Rows  : 54
Direct/Text/Proxy      : 21 / 33 / 0
Evaluation Rows        : 53
Patched Evaluations    : 0
Eval Known After       : 53

Decision Regime Counts:
- TRENDING_BULL: 45
- TRENDING_BEAR: 8
- SIDEWAYS: 1

Evaluation Regime Counts:
- TRENDING_BULL: 45
- TRENDING_BEAR: 8

Recommendations:
→ بعد از اجرای cycle جدید، regime_shadow_gate_dashboard.py --compact را دوباره بررسی کن.

Warnings:
⚠️ Regime injection فقط از داده‌های لحظه تصمیم استفاده می‌کند؛ outcome/return/target/stop استفاده نمی‌شود.
⚠️ برچسب‌های LOW_CONF_PROXY برای Research هستند و باید در Forward واقعی بیشتر validate شوند.
==============================================================================================================