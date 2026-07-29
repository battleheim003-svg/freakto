==============================================================================================================
🧬 Freakto Forward Regime Label Injection Patch v6.2.1
==============================================================================================================
Status                 : FORWARD_REGIME_LABELING_READY
Run ID                 : forward_regime_label_20260729_234656
Apply Changes          : False
Decision Rows          : 123
Known Before / After   : 61 / 61
Unknown Before / After : 62 / 62
Injected Decision Rows : 0
Preserved Direct Rows  : 61
Direct/Text/Proxy      : 28 / 33 / 0
Evaluation Rows        : 122
Patched Evaluations    : 0
Eval Known After       : 61

Decision Regime Counts:
- UNKNOWN: 62
- TRENDING_BULL: 52
- TRENDING_BEAR: 8
- SIDEWAYS: 1

Evaluation Regime Counts:
- UNKNOWN: 61
- TRENDING_BULL: 52
- TRENDING_BEAR: 8
- SIDEWAYS: 1

Recommendations:
→ هنوز 62 تصمیم Forward بدون regime قابل‌اعتماد مانده؛ اجرای‌های جدید بعد از v6.2.1 باید این عدد را کاهش دهد.
→ بعد از اجرای cycle جدید، regime_shadow_gate_dashboard.py --compact را دوباره بررسی کن.

Warnings:
⚠️ Regime injection فقط از داده‌های لحظه تصمیم استفاده می‌کند؛ outcome/return/target/stop استفاده نمی‌شود.
⚠️ برچسب‌های LOW_CONF_PROXY برای Research هستند و باید در Forward واقعی بیشتر validate شوند.
==============================================================================================================