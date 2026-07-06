# Freakto v4.7.1 — Metric Definition Clarity Patch

## هدف

در v4.7 سه لایه Validation اضافه شد، اما دو عدد ظاهراً متناقض دیده می‌شد:

- Strategy Lab: `Win Rate = 64.71%`
- Edge Validation: `Win Rate = 100.00%`

این الزاماً خطا نبود؛ دو تعریف متفاوت استفاده می‌شد. v4.7.1 این ابهام را حذف می‌کند.

## تعریف‌های جدید

- **Directional Win Rate**: درصد ارزیابی‌هایی که بازده ارزیابی‌شده آن‌ها مثبت است.
- **Target 1 Hit Rate**: درصد ارزیابی‌هایی که `target_1_hit=True` دارند.
- **Paper Trade Win Rate**: درصد معاملات فرضی بسته‌شده که R مثبت یا نتیجه WIN دارند.

## فایل‌های اضافه‌شده

- `engine/metric_definitions.py`
- `metric_definitions_dashboard.py`

## فایل‌های اصلاح‌شده

- `engine/edge_validation.py`
- `engine/strategy_lab.py`
- `engine/walk_forward.py`
- `engine/regime_matrix.py`
- `engine/live_readiness_score.py`
- `engine/trade_readiness.py`
- `validation_suite_dashboard.py`
- داشبوردهای مرتبط

## دستورهای تست

```cmd
python metric_definitions_dashboard.py
python strategy_lab_dashboard.py
python walk_forward_dashboard.py
python edge_validation_dashboard.py
python regime_matrix_dashboard.py
python live_readiness_score_dashboard.py
python validation_suite_dashboard.py
```
