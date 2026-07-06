# Freakto v4.7.0 — Validation Intelligence Suite

این نسخه سه اولویت اصلی اعتبارسنجی را یکجا اضافه می‌کند:

1. Edge Validation Engine
2. Regime Performance Matrix
3. Advanced Live Readiness Score

هدف v4.7 اضافه کردن سیگنال جدید نیست؛ هدف این است که Freakto بتواند با آمار نشان دهد آیا واقعاً Edge قابل دفاع دارد یا هنوز فقط در فاز Research/Paper است.

---

## 1) Edge Validation Engine

فایل‌ها:

- `engine/edge_validation.py`
- `edge_validation_dashboard.py`

دستور:

```bash
python edge_validation_dashboard.py
python edge_validation_dashboard.py --send
```

محاسبه می‌کند:

- Win Rate
- Expectancy
- Profit Factor
- Sharpe-like
- Sortino-like
- Max Drawdown
- Avg Win / Avg Loss
- Best / Worst Return
- Stop Hit Rate
- Target Hit Rates
- MFE / MAE

خروجی‌ها:

- `logs/edge_validation/edge_validation_*.json`
- `logs/edge_validation/edge_validation_report_*.md`

---

## 2) Regime Performance Matrix

فایل‌ها:

- `engine/regime_matrix.py`
- `regime_matrix_dashboard.py`

دستور:

```bash
python regime_matrix_dashboard.py
python regime_matrix_dashboard.py --send
```

بررسی می‌کند عملکرد موتور در هر رژیم بازار چگونه بوده است:

- TRENDING_BULL
- TRENDING_BEAR
- SIDEWAYS
- VOLATILE
- QUIET
- UNKNOWN

و برای هر ترکیب Regime / Side / Actionability محاسبه می‌کند:

- Samples
- Win Rate
- Avg 24h Return
- Profit Factor
- Stop Hit Rate
- Avg Score
- MFE / MAE
- Verdict

خروجی‌ها:

- `logs/regime_matrix/regime_matrix_*.csv`
- `logs/regime_matrix/regime_matrix_report_*.md`

نکته: از v4.7 به بعد `decision_logger.py` فیلدهای رژیم بازار را هم در `logs/decisions.csv` ذخیره می‌کند. لاگ‌های قدیمی ممکن است در Matrix با `UNKNOWN` دیده شوند.

---

## 3) Advanced Live Readiness Score

فایل‌ها:

- `engine/live_readiness_score.py`
- `live_readiness_score_dashboard.py`
- `live_readiness_report.py`

دستور:

```bash
python live_readiness_score_dashboard.py
python live_readiness_report.py
python live_readiness_score_dashboard.py --send
```

این امتیاز ترکیبی را می‌سازد:

- Data Sufficiency
- Decision Edge
- Paper Edge
- Regime Stability
- Validation Stability
- Operational Safety

خروجی‌ها:

- `logs/readiness/advanced_live_readiness_*.json`
- `logs/readiness/advanced_live_readiness_report_*.md`

سطوح خروجی:

- `RESEARCH_ONLY`
- `PAPER_TRADING_PHASE`
- `MICRO_LIVE_READY`

تا وقتی خروجی `MICRO_LIVE_READY` نشود، تست واقعی با پول نباید شروع شود.

---

## 4) Combined Validation Suite

فایل:

- `validation_suite_dashboard.py`

دستور:

```bash
python validation_suite_dashboard.py
python validation_suite_dashboard.py --send
```

این دستور هر سه بخش را یکجا اجرا می‌کند:

- Edge Validation
- Regime Matrix
- Advanced Live Readiness

و گزارش ترکیبی را ذخیره می‌کند:

- `logs/validation_suite/validation_suite_report_*.md`

---

## فایل‌های تغییرکرده/جدید

- `engine/edge_validation.py`
- `edge_validation_dashboard.py`
- `engine/regime_matrix.py`
- `regime_matrix_dashboard.py`
- `engine/live_readiness_score.py`
- `live_readiness_score_dashboard.py`
- `validation_suite_dashboard.py`
- `live_readiness_report.py`
- `decision_logger.py`
- `RELEASE_NOTES_v4_7_0.md`

---

## تست پیشنهادی

```bash
python decision_evaluator.py
python strategy_lab_dashboard.py
python walk_forward_dashboard.py
python edge_validation_dashboard.py
python regime_matrix_dashboard.py
python live_readiness_score_dashboard.py
python validation_suite_dashboard.py
```

برای تلگرام:

```bash
python validation_suite_dashboard.py --send
```
