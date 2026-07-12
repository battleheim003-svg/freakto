==============================================================================================================
🧬 Freakto Forward Regime Label Injection Patch v6.2.1
==============================================================================================================
Status                 : FORWARD_REGIME_LABELING_READY
Run ID                 : forward_regime_label_20260712_114838
Apply Changes          : True
Decision Rows          : 61
Known Before / After   : 61 / 61
Unknown Before / After : 0 / 0
Injected Decision Rows : 0
Preserved Direct Rows  : 61
Direct/Text/Proxy      : 28 / 33 / 0
Evaluation Rows        : 59
Patched Evaluations    : 0
Eval Known After       : 59

Decision Regime Counts:
- TRENDING_BULL: 52
- TRENDING_BEAR: 8
- SIDEWAYS: 1

Evaluation Regime Counts:
- TRENDING_BULL: 50
- TRENDING_BEAR: 8
- SIDEWAYS: 1

Backups:
- logs/decisions.csv.bak_v621_20260712_114838
- logs/decision_evaluations.csv.bak_v621_20260712_114838

Recommendations:
→ بعد از اجرای cycle جدید، regime_shadow_gate_dashboard.py --compact را دوباره بررسی کن.

Warnings:
⚠️ Regime injection فقط از داده‌های لحظه تصمیم استفاده می‌کند؛ outcome/return/target/stop استفاده نمی‌شود.
⚠️ برچسب‌های LOW_CONF_PROXY برای Research هستند و باید در Forward واقعی بیشتر validate شوند.
==============================================================================================================