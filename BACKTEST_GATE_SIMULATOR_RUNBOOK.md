# Freakto v5.3.2 — Backtest Gate Simulator Runbook

این ابزار برای پاسخ به یک سؤال مشخص ساخته شده است:

> آیا از خروجی Backtest تاریخی می‌توان یک subset یا gate مثبت و قابل تحقیق پیدا کرد؟

## اصل ایمنی

Gate Simulator فقط از فیلدهایی استفاده می‌کند که در لحظه تصمیم‌گیری قابل دانستن هستند:

```text
symbol
side
score
actionability
confidence_label
risk_label
regime_label
trend_score / momentum_score / volume_score / structure_score
historical_edge_score
long_score / short_score
```

فیلدهای آینده مثل `return_after_24h_pct`، `target_1_hit`، `stop_hit`، `mfe_pct` و `mae_pct` فقط برای ارزیابی استفاده می‌شوند و وارد شرط gate نمی‌شوند. این برای جلوگیری از lookahead bias ضروری است.

## پیش‌نیاز

اول باید Historical Backtest اجرا شده باشد:

```cmd
python historical_backtest_dashboard.py --symbols BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT,XRP/USDT,DOGE/USDT --limit 800 --step 6
```

بعد Diagnostics را می‌توانی اجرا کنی:

```cmd
python backtest_diagnostics_dashboard.py --compact
```

بعد Gate Simulator:

```cmd
python backtest_gate_simulator_dashboard.py --compact
```

## اجرای پیشنهادی

اجرای استاندارد با horizon بیست‌وچهار ساعته و حداقل ۳۰ sample:

```cmd
python backtest_gate_simulator_dashboard.py --compact --min-samples 30 --horizon 24h
```

برای بررسی خروج سریع‌تر ۴ ساعته:

```cmd
python backtest_gate_simulator_dashboard.py --compact --min-samples 30 --horizon 4h
```

برای ارسال تلگرام:

```cmd
python backtest_gate_simulator_dashboard.py --compact --send
```

## خروجی‌ها

```text
logs/backtests/gate_simulator/gate_simulation_<run_id>.json
logs/backtests/gate_simulator/gate_simulation_report_<run_id>.md
logs/backtests/gate_simulator/gate_simulation_results_<run_id>.csv
```

## معنی Verdictها

```text
RESEARCH_CANDIDATE
نمونه کافی دارد، میانگین مثبت است، Target >= Stop، MFE/MAE مناسب و win-rate قابل قبول است.

POSITIVE_BUT_NEEDS_REVIEW
نمونه کافی و میانگین مثبت دارد، اما یکی از معیارهای کیفیت کامل نیست.

POSITIVE_BUT_RISKY
میانگین مثبت است ولی Target/Stop یا کیفیت مسیر مشکل دارد.

SMALL_SAMPLE_POSITIVE
مثبت است ولی sample کمتر از حداقل است. این حالت جذاب است اما قابل اعتماد نیست.

NEAR_BREAKEVEN_WATCH
نزدیک صفر است و شاید با اصلاح exit/stop ارزش تحقیق داشته باشد.

REJECT_NEGATIVE_EDGE
میانگین منفی است و فعلاً نباید gate عملی شود.

REJECT_INSUFFICIENT_SAMPLE / REJECT_TOO_SMALL
نمونه کافی ندارد.
```

## قانون تصمیم

هیچ gate فقط با Backtest اجازه Paper/Live نمی‌دهد.

یک gate فقط وقتی ارزش ادامه تحقیق دارد که:

```text
sample کافی داشته باشد
avg return مثبت باشد
stop rate کنترل‌شده باشد
در Forward Test هم بهتر از baseline ظاهر شود
در Paper Trades واقعی هم تأیید شود
```

## قدم بعدی بعد از این گزارش

اگر `RESEARCH_CANDIDATE` پیدا شد، نسخه بعدی می‌تواند `Research Gate Config` بسازد تا آن gate در Forward/Paper به صورت محافظه‌کارانه فقط برای مشاهده اعمال شود.

اگر فقط `SMALL_SAMPLE_POSITIVE` پیدا شد، باید Backtest را با limit/period بیشتر یا نمادهای بیشتر گسترش دهیم.

اگر هیچ gate مثبتی پیدا نشد، باید به اصلاح موتور entry/exit، stop/target و actionability برگردیم.
