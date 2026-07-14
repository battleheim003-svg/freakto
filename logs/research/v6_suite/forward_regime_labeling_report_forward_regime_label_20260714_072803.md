==============================================================================================================
🧬 Freakto Forward Regime Label Injection Patch v6.2.1
==============================================================================================================
Status                 : FORWARD_REGIME_LABELING_READY
Run ID                 : forward_regime_label_20260714_072803
Apply Changes          : True
Decision Rows          : 68
Known Before / After   : 61 / 61
Unknown Before / After : 7 / 7
Injected Decision Rows : 0
Preserved Direct Rows  : 61
Direct/Text/Proxy      : 28 / 33 / 0
Evaluation Rows        : 67
Patched Evaluations    : 0
Eval Known After       : 61

Decision Regime Counts:
- TRENDING_BULL: 52
- TRENDING_BEAR: 8
- UNKNOWN: 7
- SIDEWAYS: 1

Evaluation Regime Counts:
- TRENDING_BULL: 52
- TRENDING_BEAR: 8
- UNKNOWN: 6
- SIDEWAYS: 1

Backups:
- logs/decisions.csv.bak_v621_20260714_072803
- logs/decision_evaluations.csv.bak_v621_20260714_072803

Recommendations:
→ هنوز 7 تصمیم Forward بدون regime قابل‌اعتماد مانده؛ اجرای‌های جدید بعد از v6.2.1 باید این عدد را کاهش دهد.
→ بعد از اجرای cycle جدید، regime_shadow_gate_dashboard.py --compact را دوباره بررسی کن.

Warnings:
⚠️ Regime injection فقط از داده‌های لحظه تصمیم استفاده می‌کند؛ outcome/return/target/stop استفاده نمی‌شود.
⚠️ برچسب‌های LOW_CONF_PROXY برای Research هستند و باید در Forward واقعی بیشتر validate شوند.
==============================================================================================================