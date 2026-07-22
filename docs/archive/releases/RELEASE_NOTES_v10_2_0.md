# Freakto v10.2.0 — Score Calibration & Feature Attribution Lab

## Added

- Score-band calibration روی Train/Validation/Test
- بررسی monotonicity و adjacent-band violations
- Feature attribution برای Trend, Momentum, Volume, Structure, Regime و Risk
- Thresholdهای Feature فقط با Train تعیین و بدون تغییر روی Validation/Test اجرا می‌شوند
- Pairwise feature-interaction search با محافظت در برابر Overfit
- تحلیل عملکرد جداگانه Symbol، Regime و Side
- خروجی JSON، Markdown و CSVهای قابل ممیزی
- تست‌های Synthetic برای Score مثبت، Score معکوس و فایل مفقود

## Safety

- Decision Engine تغییر نمی‌کند
- هیچ Config خودکار اعمال نمی‌شود
- Paper و Live فعال نمی‌شوند
- Candidate فقط برای Forward Shadow پیشنهاد می‌شود
