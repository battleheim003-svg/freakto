==============================================================================================================
🧬 Freakto Forward Regime Label Injection Patch v6.2.1
==============================================================================================================
Status                 : FORWARD_REGIME_LABELING_READY
Run ID                 : forward_regime_label_20260710_112931
Apply Changes          : False
Decision Rows          : 52
Known Before / After   : 52 / 52
Unknown Before / After : 0 / 0
Injected Decision Rows : 0
Preserved Direct Rows  : 52
Direct/Text/Proxy      : 19 / 33 / 0
Evaluation Rows        : 51
Patched Evaluations    : 0
Eval Known After       : 51

Decision Regime Counts:
- TRENDING_BULL: 44
- TRENDING_BEAR: 8

Evaluation Regime Counts:
- TRENDING_BULL: 43
- TRENDING_BEAR: 8

Recommendations:
→ بعد از اجرای cycle جدید، regime_shadow_gate_dashboard.py --compact را دوباره بررسی کن.

Warnings:
⚠️ Regime injection فقط از داده‌های لحظه تصمیم استفاده می‌کند؛ outcome/return/target/stop استفاده نمی‌شود.
⚠️ برچسب‌های LOW_CONF_PROXY برای Research هستند و باید در Forward واقعی بیشتر validate شوند.
==============================================================================================================