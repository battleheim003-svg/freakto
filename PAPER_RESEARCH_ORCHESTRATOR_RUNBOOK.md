# Freakto Automated Research Paper Cycle

## هدف

این ابزار تمام عملیات دوره‌ای Paper Research را با یک اجرا هماهنگ می‌کند. هیچ سفارش واقعی، API سفارش‌گذاری یا تخصیص سرمایه واقعی در این مسیر وجود ندارد.

## اجرای دائمی با یک فایل

روی ویندوز فقط این فایل را اجرا کنید:

```bat
run_paper_research_auto.bat
```

برنامه بلافاصله یک چرخه اجرا می‌کند و سپس در زمان بسته‌شدن کندل‌های ۴ساعته UTC، با ۲ دقیقه تأخیر برای نهایی‌شدن کندل، چرخه بعدی را اجرا می‌کند.

برای توقف امن `Ctrl+C` بزنید. برنامه پس از پایان Step جاری متوقف می‌شود.

## ترتیب هر چرخه ۴ساعته

1. Readiness Preflight و بررسی Arm State
2. Arm خودکار Research در صورت آماده‌بودن
3. ارتقای خودکار به Strategy Paper فقط پس از عبور همه Gateهای Development و Fresh OOS
4. اجرای `monitor.py --once`
5. اجرای `decision_evaluator.py`
6. Scan تصمیم‌های جدید و ثبت Observationهای Cost-Gated
7. ارزیابی معاملات Paper باز
8. چاپ و ذخیره وضعیت Readiness

## نگهداری روزانه

هر ۶ چرخه، تقریباً روزی یک‌بار:

1. دیتای تاریخی BTC/ETH/SOL به‌صورت Incremental به‌روزرسانی می‌شود.
2. Fresh OOS با داده‌های جدید و Policy ثابت دوباره اجرا می‌شود.
3. Readiness دوباره محاسبه می‌شود.
4. فقط در صورت عبور همه شروط، حالت مجازی از Research به Strategy Paper ارتقا پیدا می‌کند.

## اجرای فقط یک چرخه

```bat
run_research_paper_cycle.bat
```

یا:

```bat
python -X utf8 paper_research_orchestrator.py --once
```

## اجرای فوری Maintenance

```bat
python -X utf8 paper_research_orchestrator.py --once --maintenance-now
```

## خروجی‌ها

```text
logs/paper_cycle/paper_cycle.log
logs/paper_cycle/heartbeat.json
logs/paper_cycle/last_cycle.json
logs/paper_cycle/cycle_history.jsonl
logs/paper_cycle/orchestrator_state.json
logs/paper_cycle/orchestrator.lock
```

`heartbeat.json` زمان چرخه بعدی را نشان می‌دهد. `last_cycle.json` نتیجه آخرین چرخه و Exit Code هر Step را نگه می‌دارد.

## رفتار Fail-Closed

- اگر Monitor شکست بخورد، Scan/Evaluation/Status برای ثبت وضعیت و حفظ Audit ادامه می‌یابد.
- Step شکست‌خورده Retry می‌شود و هرگز موفقیت جعلی ثبت نمی‌شود.
- اجرای هم‌زمان دو Orchestrator با Lock مسدود می‌شود.
- Strategy Paper فقط با `strategy_paper_ready=True` فعال می‌شود.
- هر Arm State دارای `allocation_pct=0`، `live_orders_enabled=false` و `real_capital_enabled=false` باقی می‌ماند.
- این ابزار هیچ مسیر Live یا ارسال سفارش ندارد.

## تنظیم زمان‌بندی

نمونه اجرای کندل یک‌ساعته با ۹۰ ثانیه تأخیر:

```bat
python -X utf8 paper_research_orchestrator.py --loop --timeframe-minutes 60 --settle-delay-seconds 90
```

برای غیرفعال‌کردن Maintenance روزانه:

```bat
python -X utf8 paper_research_orchestrator.py --loop --no-maintenance
```
