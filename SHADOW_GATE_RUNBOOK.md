# Freakto v5.3.3 — Candidate Gate Shadow Validator Runbook

این نسخه Gateهایی را که در Backtest مثبت دیده شدند وارد حالت **Shadow Mode** می‌کند.

Shadow Mode یعنی:

- هیچ معامله واقعی باز نمی‌شود.
- هیچ Paper Trade جدیدی ثبت نمی‌شود.
- فقط تصمیم‌های Forward آینده برچسب می‌خورند که کدام Gate را پاس کرده‌اند.
- بعد از اینکه `decision_evaluator.py` نتیجه تصمیم‌ها را کامل کرد، عملکرد هر Gate محاسبه می‌شود.

## Gateهای تحت نظر

Gateهای اصلی Backtest candidate:

1. `VOLUME_SCORE_GE_10`
2. `RISK_MEDIUM`
3. `HISTORICAL_EDGE_SCORE_GE_1`

Gateهای watch/review:

4. `STRUCTURE_SCORE_GE_10`
5. `SCORE_GE_80`
6. `DOGE_SHORT_WATCH`
7. `BNB_LONG_SCORE_GE_60`

## اجرای دستی

```cmd
python shadow_gate_dashboard.py --compact
```

با horizon چهار ساعته:

```cmd
python shadow_gate_dashboard.py --compact --horizon 4h
```

با ارسال تلگرام:

```cmd
python shadow_gate_dashboard.py --compact --send
```

## اجرای خودکار

از v5.3.3 به بعد، `forward_test_dashboard.py --cycle` بعد از `decision_evaluator.py` این مرحله را هم اجرا می‌کند:

```cmd
python -X utf8 shadow_gate_dashboard.py --compact
```

یعنی GitHub Actions هم به‌صورت خودکار در هر چرخه Forward این گزارش را تولید می‌کند.

## خروجی‌ها

```text
logs/shadow_gates/shadow_gate_signals.csv
logs/shadow_gates/shadow_gate_status_<run_id>.json
logs/shadow_gates/shadow_gate_report_<run_id>.md
logs/shadow_gates/shadow_gate_metrics_<run_id>.csv
logs/shadow_gates/shadow_gate_runs.csv
```

## معیار تأیید

هیچ Gate فقط با Backtest تأیید نمی‌شود. برای اینکه یک Gate از Shadow به مرحله بعد نزدیک شود، باید در Forward هم این شرایط را بگیرد:

```text
حداقل 30 نمونه Forward کامل برای همان Gate
Avg Return مثبت
Win Rate حداقل 50%
Target 1 Hit Rate >= Stop Rate
MFE/MAE >= 1
```

حتی بعد از این هم فقط می‌شود درباره Paper محدود فکر کرد، نه Live.

## چرا این مهم است؟

v5.3.2 نشان داد baseline کلی منفی است، اما چند Gate تاریخی مثبت‌اند. v5.3.3 بررسی می‌کند این Gateها در آینده واقعی هم جواب می‌دهند یا فقط روی گذشته خوب دیده شده‌اند.

---

## v6.2 Update — Regime Shadow Gate Activator

از v6.2 به بعد، Shadow Gate فقط gateهای پایه v5.3.2/v6.0 را رصد نمی‌کند؛ چهار gate جدید از v6.1 هم فعال شده‌اند:

```text
REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10
REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT
REGIME_TRENDING_BEAR__RISK_MEDIUM
REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT
```

برای دیدن نمای focused:

```cmd
python regime_shadow_gate_dashboard.py --compact
```

این gateها فقط Shadow هستند و هیچ اثری روی Paper/Live ندارند.
