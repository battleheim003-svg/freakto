==============================================================================================================
🧬 Freakto Forward Regime Label Injection Patch v6.2.1
==============================================================================================================
Status                 : FORWARD_REGIME_LABELING_READY
Run ID                 : forward_regime_label_20260709_092036
Apply Changes          : True
Decision Rows          : 32
Known Before / After   : 1 / 32
Unknown Before / After : 31 / 0
Injected Decision Rows : 31
Preserved Direct Rows  : 1
Direct/Text/Proxy      : 1 / 31 / 0
Evaluation Rows        : 30
Patched Evaluations    : 30
Eval Known After       : 30

Decision Regime Counts:
- TRENDING_BULL: 32

Evaluation Regime Counts:
- TRENDING_BULL: 30

Backups:
- logs\decisions.csv.bak_v621_20260709_092036
- logs\decision_evaluations.csv.bak_v621_20260709_092036

Recommendations:
→ 31 ردیف legacy با regime proxy/text پر شد؛ برای تصمیم نهایی فقط DIRECT_ENGINE و Forward جدید را جدی‌تر بگیر.
→ بعد از اجرای cycle جدید، regime_shadow_gate_dashboard.py --compact را دوباره بررسی کن.

Warnings:
⚠️ Regime injection فقط از داده‌های لحظه تصمیم استفاده می‌کند؛ outcome/return/target/stop استفاده نمی‌شود.
⚠️ برچسب‌های LOW_CONF_PROXY برای Research هستند و باید در Forward واقعی بیشتر validate شوند.
==============================================================================================================