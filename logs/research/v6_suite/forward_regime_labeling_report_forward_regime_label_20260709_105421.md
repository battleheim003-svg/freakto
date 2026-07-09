==============================================================================================================
🧬 Freakto Forward Regime Label Injection Patch v6.2.1
==============================================================================================================
Status                 : FORWARD_REGIME_LABELING_READY
Run ID                 : forward_regime_label_20260709_105421
Apply Changes          : True
Decision Rows          : 48
Known Before / After   : 15 / 48
Unknown Before / After : 33 / 0
Injected Decision Rows : 33
Preserved Direct Rows  : 15
Direct/Text/Proxy      : 15 / 33 / 0
Evaluation Rows        : 46
Patched Evaluations    : 46
Eval Known After       : 46

Decision Regime Counts:
- TRENDING_BULL: 43
- TRENDING_BEAR: 5

Evaluation Regime Counts:
- TRENDING_BULL: 43
- TRENDING_BEAR: 3

Backups:
- logs/decisions.csv.bak_v621_20260709_105421
- logs/decision_evaluations.csv.bak_v621_20260709_105421

Recommendations:
→ 33 ردیف legacy با regime proxy/text پر شد؛ برای تصمیم نهایی فقط DIRECT_ENGINE و Forward جدید را جدی‌تر بگیر.
→ بعد از اجرای cycle جدید، regime_shadow_gate_dashboard.py --compact را دوباره بررسی کن.

Warnings:
⚠️ Regime injection فقط از داده‌های لحظه تصمیم استفاده می‌کند؛ outcome/return/target/stop استفاده نمی‌شود.
⚠️ برچسب‌های LOW_CONF_PROXY برای Research هستند و باید در Forward واقعی بیشتر validate شوند.
==============================================================================================================