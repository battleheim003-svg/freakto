==============================================================================================================
🧬 Freakto Forward Regime Label Injection Patch v6.2.1
==============================================================================================================
Status                 : FORWARD_REGIME_LABELING_READY
Run ID                 : forward_regime_label_20260709_105437
Apply Changes          : True
Decision Rows          : 48
Known Before / After   : 48 / 48
Unknown Before / After : 0 / 0
Injected Decision Rows : 0
Preserved Direct Rows  : 48
Direct/Text/Proxy      : 15 / 33 / 0
Evaluation Rows        : 46
Patched Evaluations    : 0
Eval Known After       : 46

Decision Regime Counts:
- TRENDING_BULL: 43
- TRENDING_BEAR: 5

Evaluation Regime Counts:
- TRENDING_BULL: 43
- TRENDING_BEAR: 3

Backups:
- logs/decisions.csv.bak_v621_20260709_105437
- logs/decision_evaluations.csv.bak_v621_20260709_105437

Recommendations:
→ بعد از اجرای cycle جدید، regime_shadow_gate_dashboard.py --compact را دوباره بررسی کن.

Warnings:
⚠️ Regime injection فقط از داده‌های لحظه تصمیم استفاده می‌کند؛ outcome/return/target/stop استفاده نمی‌شود.
⚠️ برچسب‌های LOW_CONF_PROXY برای Research هستند و باید در Forward واقعی بیشتر validate شوند.
==============================================================================================================