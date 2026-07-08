# Freakto v6.1 — Regime-Split Gate Matrix

این نسخه بعد از v6.0 ساخته شد تا Gateهای مثبت/مشکوک را به تفکیک رژیم بازار بررسی کند.

هدف اصلی:

```text
Regime × Gate
Regime × Side
Regime × Symbol
Regime × Gate × Side
```

این ماژول فقط research-only است و هیچ سفارش واقعی یا Paper Trade جدید ایجاد نمی‌کند.

## اجرای پیشنهادی

```cmd
python regime_gate_matrix_dashboard.py --compact
```

اجرای دقیق‌تر روی horizon اصلی 24h:

```cmd
python regime_gate_matrix_dashboard.py --compact --horizon 24h --min-samples 10 --candidate-min-samples 30
```

بررسی فقط Gateهای اصلی v6:

```cmd
python regime_gate_matrix_dashboard.py --compact --primary-only
```

ارسال به تلگرام:

```cmd
python regime_gate_matrix_dashboard.py --compact --send
```

## خروجی‌ها

```text
logs/research/v6_suite/regime_gate_matrix_<run_id>.json
logs/research/v6_suite/regime_gate_matrix_report_<run_id>.md
logs/research/v6_suite/regime_gate_matrix_results_<run_id>.csv
logs/research/v6_suite/regime_gate_side_matrix_results_<run_id>.csv
logs/research/v6_suite/regime_avoid_candidates_<run_id>.csv
logs/research/v6_suite/regime_shadow_proposals_<run_id>.json
```

## Verdictها

```text
REGIME_RESEARCH_CANDIDATE
POSITIVE_BUT_FRAGILE
POSITIVE_LOW_SAMPLE
NET_NEGATIVE_AFTER_COST
AVOID_CANDIDATE
LOW_SAMPLE
```

## قانون تصمیم‌گیری

حتی اگر یک ترکیب مثل `TRENDING_BULL × VOLUME_SCORE_GE_10` مثبت شد، فقط Shadow/Forward candidate است. برای Paper/Live باید:

```text
Forward samples >= 30
net expectancy مثبت
Target rate >= Stop rate
MFE/MAE >= 1
نتیجه فقط روی یک پنجره یا یک نماد تصادفی نباشد
Strict Readiness blocker نداشته باشد
```

## چرا v6.1 مهم است؟

خروجی v6.0 نشان داد Regime خام به‌تنهایی مثبت نیست و Gateهای 4h/12h هم robust نیستند. پس باید بفهمیم Gateهای 24h در کدام رژیم‌ها بهتر یا بدتر هستند.

## Safety

```text
Live Trading: ممنوع
Paper Trade جدید: ساخته نمی‌شود
Shadow/Research: مجاز
```
