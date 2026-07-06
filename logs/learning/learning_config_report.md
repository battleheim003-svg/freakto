# Freakto Learning Config Advisory v3.3

Created UTC: 2026-07-05T15:15:46.835349+00:00

## Summary
- Recommendation source version: 3.1.0
- Sample size: 25 | Complete evaluations: 17
- Data readiness: OBSERVE_ONLY

## Warnings
- ⚠️ نمونه‌های COMPLETE کمتر از 30 است؛ هیچ تغییر اجرایی پیشنهاد نمی‌شود، فقط مانیتورینگ.

## Proposed Actions
### learning.auto_apply
- Current: `False`
- Proposed: `False`
- Confidence: `HIGH`
- Mode: `LOCKED`
- Source: Safety Policy
- Reason: اعمال خودکار وزن‌ها تا قبل از رسیدن به نمونه‌های کافی غیرفعال می‌ماند.

### learning.min_complete_evaluations_for_auto_tuning
- Current: `30`
- Proposed: `30`
- Confidence: `HIGH`
- Mode: `REFERENCE`
- Source: Data Readiness
- Reason: تا قبل از حداقل 30 ارزیابی کامل، فقط پیشنهاد تولید می‌شود و وزن اجرایی تغییر نمی‌کند.

### component_multipliers.volume
- Current: `1.0`
- Proposed: `1.0`
- Confidence: `LOW`
- Mode: `OBSERVE_ONLY`
- Source: Component Weight: Volume | QUESTIONABLE
- Reason: Volume در داده فعلی مشکوک است، اما نمونه COMPLETE هنوز برای کاهش وزن کافی نیست. Evidence: High Volume Avg24=0.74% vs Low Avg24=1.77%

### component_multipliers.structure
- Current: `1.0`
- Proposed: `1.0`
- Confidence: `LOW`
- Mode: `OBSERVE_ONLY`
- Source: Component Weight: Structure | QUESTIONABLE
- Reason: Structure در داده فعلی مشکوک است، اما نمونه COMPLETE هنوز برای کاهش وزن کافی نیست. Evidence: High Structure Avg24=0.88% vs Low Avg24=1.81%

## Safety
- Auto-Apply is OFF in v3.2.
- This file is advisory/staging only. Decision Engine will not read these overrides yet.
- Future versions may support opt-in application after enough COMPLETE evaluations are collected.
