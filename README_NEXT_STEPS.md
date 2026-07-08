# Freakto Next Steps — v5.2

## وضعیت فعلی

پروژه وارد فاز Forward Test Collection شده و v5.2 امکان اجرای رایگان روی GitHub Actions را اضافه می‌کند.

## قدم بعدی عملی

1. پروژه را روی GitHub آپلود کن.
2. Secretهای Telegram را در GitHub Actions تنظیم کن.
3. Workflow را دستی یک بار اجرا کن.
4. مطمئن شو branch `data-logs` ساخته شده و لاگ‌ها در آن ذخیره می‌شوند.
5. اجازه بده workflow هر 4 ساعت اجرا شود.

## راهنمای کامل

فایل زیر را بخوان:

```text
GITHUB_ACTIONS_SETUP_FA.md
```

## هدف جمع‌آوری داده

```text
Complete evaluations >= 100
Closed paper trades >= 30
Regime-labeled samples >= 30
Forward days >= 30
```

تا وقتی این معیارها کامل نشده‌اند، پروژه همچنان نباید وارد پول واقعی شود.

## دستور دستی لوکال

```bash
python -X utf8 forward_test_dashboard.py --cycle --validate --continue-on-error --send
```

## اجرای خودکار رایگان

GitHub Actions workflow:

```text
.github/workflows/freakto-forward-test.yml
```

این workflow هر 4 ساعت اجرا می‌شود و لاگ‌ها را در branch `data-logs` ذخیره می‌کند.

---

## v5.2.1 — بعد از فعال شدن GitHub Actions

اگر `Freakto Forward Test Collector` روی GitHub سبز شده، قدم بعدی نصب v5.2.1 است.

این نسخه دو کار عملیاتی اضافه می‌کند:

```text
1. Health Check Workflow برای چک سبک وضعیت بدون اجرای چرخه کامل
2. GitHub Actions Health Summary برای دیدن وضعیت در صفحه Summary هر run
```

بعد از push کردن v5.2.1 به GitHub، در تب Actions باید دو workflow داشته باشی:

```text
Freakto Forward Test Collector
Freakto Health Check
```

Workflow اصلی هر ۴ ساعت دیتا جمع می‌کند. Health Check فقط وضعیت را از لاگ‌های ذخیره‌شده می‌خواند.

فعلاً هدف پروژه همچنان جمع‌آوری داده است، نه live trading:

```text
30 Forward Days
100 Complete Evaluations
30 Closed Paper Trades
30 Regime-labeled Samples
```

## v5.2.3 GitHub Actions Restore Hotfix
اگر در Health Check خطای زیر دیدی:

```text
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb6
```

نسخه v5.2.3 را نصب کن. این نسخه `scripts/github_actions_restore_logs.py` را اصلاح می‌کند تا خروجی باینری `git archive` به اشتباه به‌صورت متن UTF-8 decode نشود.

## v5.2.4 نکته عملیاتی GitHub Actions

اگر در Health Summary دیدی `Last Forward Run` وجود دارد اما `Forward Runs` یا `Forward Days` صفر هستند، نسخه v5.2.4 را نصب کن. این نسخه Health Summary را با schemaهای مختلف لاگ سازگار می‌کند و در صورت نیاز از `logs/forward_test_runs.csv` برای شمارش runها fallback می‌گیرد.

---

## v5.2.5 — GitHub Actions Health Counter Hotfix

اگر Health Check سبز است ولی هنوز `Forward Runs` را `0/0 successful` نشان می‌دهد، نسخه v5.2.5 را نصب کن و دوباره Health Check را اجرا کن.

بعد از نصب، انتظار می‌رود Health Summary از `logs/forward_test_runs.csv` شمارش کند و حداقل آخرین اجرای موفق را به‌درستی در Forward Runs و Forward Days نشان دهد.


## Freakto v5.3 — Historical Backfill & Backtest

بعد از پایدار شدن GitHub Actions، مسیر دوم تحقیق اضافه شد: Backtest تاریخی.

دستور وضعیت:

```cmd
python historical_backtest_dashboard.py --status
```

اجرای پیشنهادی اولیه:

```cmd
python historical_backtest_dashboard.py --symbols BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT,XRP/USDT,DOGE/USDT --limit 800 --step 6
```

خروجی‌ها در `logs/backtests/` و `logs/historical_backtest_evaluations.csv` ذخیره می‌شوند.

قانون مهم: `BACKTEST` جای `FORWARD_TEST` را نمی‌گیرد. Live یا Paper جدی فقط وقتی قابل بررسی است که Forward/Paper واقعی هم به حد کافی رسیده باشد.

## v5.3.1 - Backtest Diagnostics

بعد از اجرای Historical Backtest، برای فهمیدن علت Edge منفی اجرا کن:

```cmd
python backtest_diagnostics_dashboard.py
python backtest_diagnostics_dashboard.py --compact
python backtest_diagnostics_dashboard.py --send
```

این گزارش مشخص می‌کند کدام سمت، نماد، score bucket، holding period و target/stop path بهتر یا بدتر عمل کرده‌اند. خروجی فقط تحقیقاتی است و اجازه Paper/Live نمی‌دهد.

## v5.3.2 - Backtest Gate Simulator

بعد از Diagnostics، برای اینکه بفهمی آیا subset قابل تحقیق وجود دارد یا نه، Gate Simulator را اجرا کن:

```cmd
python backtest_gate_simulator_dashboard.py --compact
```

اجرای دقیق‌تر با حداقل sample:

```cmd
python backtest_gate_simulator_dashboard.py --compact --min-samples 30 --horizon 24h
```

و برای بررسی خروج 4h:

```cmd
python backtest_gate_simulator_dashboard.py --compact --min-samples 30 --horizon 4h
```

خروجی‌ها در این مسیر ذخیره می‌شوند:

```text
logs/backtests/gate_simulator/
```

قانون مهم: حتی اگر یک gate در Backtest مثبت شد، فقط `RESEARCH_CANDIDATE` است. برای Paper/Live باید در Forward Test و Paper Trades واقعی هم تأیید شود.


## v5.3.3 — Candidate Gate Shadow Validator

بعد از v5.3.2 چند Gate تحقیقاتی مثبت در Backtest پیدا شد. از v5.3.3 این Gateها وارد Shadow Mode شدند:

```text
VOLUME_SCORE_GE_10
RISK_MEDIUM
HISTORICAL_EDGE_SCORE_GE_1
STRUCTURE_SCORE_GE_10
SCORE_GE_80
DOGE_SHORT_WATCH
BNB_LONG_SCORE_GE_60
```

اجرای دستی:

```cmd
python shadow_gate_dashboard.py --compact
```

از این نسخه به بعد Forward Cycle و GitHub Actions به صورت خودکار Shadow Gate Validator را بعد از `decision_evaluator.py` اجرا می‌کنند.

هدف: تأیید یا رد Gateهای مثبت Backtest روی Forward Test واقعی، بدون Paper/Live.

---

# v6.0 — Research Robustness & Intelligence Suite

بعد از فعال شدن Backtest، Gate Simulator و Shadow Gate، نسخه v6 اضافه شد تا ۱۱ مسیر بهبود زیر را در حالت research-only اجرا کند:

```cmd
python freakto_research_suite_dashboard.py
```

مهم‌ترین خروجی‌ها:

```text
logs/research/v6_suite/
logs/research/freakto_research.db
logs/research_dashboard/index.html
```

قدم بعدی بعد از اجرای v6 این است که خروجی‌های زیر بررسی شوند:

```cmd
python gate_robustness_dashboard.py --horizon 24h --min-samples 30
python cost_adjusted_backtest_dashboard.py
python statistical_readiness_dashboard.py
python pipeline_health_dashboard.py
```

تا وقتی Strict Readiness و Shadow Gate Forward sample کافی نداشته باشند، پروژه همچنان RESEARCH_ONLY است.

---

# v6.1 — Regime-Split Gate Matrix

بعد از v6.0 مشخص شد که Regime خام به‌تنهایی Edge مثبت ندارد و Gateهای 4h/12h هم robust نیستند. v6.1 برای بررسی ترکیب‌های دقیق‌تر اضافه شد:

```text
Regime × Gate
Regime × Side
Regime × Symbol
Regime × Gate × Side
```

اجرای پیشنهادی:

```cmd
python regime_gate_matrix_dashboard.py --compact
```

اجرای دقیق‌تر:

```cmd
python regime_gate_matrix_dashboard.py --compact --horizon 24h --min-samples 10 --candidate-min-samples 30
```

اگر خواستی فقط Gateهای اصلی v6 بررسی شوند:

```cmd
python regime_gate_matrix_dashboard.py --compact --primary-only
```

خروجی‌ها در این مسیر ذخیره می‌شوند:

```text
logs/research/v6_suite/
```

قانون مهم: هر خروجی مثبت v6.1 فقط Shadow/Research candidate است. Paper/Live تا وقتی Forward sample، Strict Readiness و Shadow validation کافی نباشد ممنوع می‌ماند.
