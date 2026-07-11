# Freakto v10.1.5 — Replay Evaluation Recorder

## Fix اصلی

نسخه v10 از ابتدا outcomeهای واقعی را در ستون‌های horizon-specific ذخیره می‌کرد، اما Prototypeهای Optimization دنبال نام‌های عمومی `return` و `net_return` بودند. به همین دلیل مقدارها `None` دیده می‌شدند.

## تغییرات

- افزودن canonical evaluation schema به `engine/market_replay.py`
- افزودن Backfill امن برای Replayهای موجود
- افزودن `exit_price`, `gross_return_pct`, `net_return_pct`, `win`, `outcome_label`
- اصلاح Schema Adapter بر اساس ستون‌های واقعی v10
- تحلیل واقعی Thresholdها با Train/Validation/Test
- محاسبه Win Rate، Avg Net، Profit Factor و Drawdown Proxy
- تشخیص Train-positive/Test-negative به‌عنوان Overfit
- Backup اجباری پیش از بازنویسی CSV موجود
- تست‌های Unit برای backfill، schema و metrics

## Safety

Research-only. هیچ Paper/Live یا Strategy Mutation انجام نمی‌شود.
