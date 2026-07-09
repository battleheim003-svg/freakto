# Freakto v6.3.0 — Forward Shadow Coverage & Bull Regime Probe

این ماژول برای مرحله بعد از v6.2.1 ساخته شده است.

## هدف

v6.2.1 نشان داد که `regime_label` درست وارد Forward logs شده، اما Forward فعلی بیشتر/کاملاً `TRENDING_BULL` است و Regime Bear gates طبیعی است که signal نگیرند. v6.3 این مسئله را رسمی تحلیل می‌کند.

## چه چیزی را بررسی می‌کند؟

- پوشش Regime در Forward decisions
- پوشش Shadow Gateها به تفکیک gate و dominant regime
- دلیل صفر بودن Regime Bear gates
- probeهای مخصوص Bull regime بدون ارتقا به candidate
- تضاد احتمالی بین Forward کم‌نمونه و Backtest

## دستورها

```cmd
python forward_shadow_coverage_dashboard.py --compact
python forward_shadow_coverage_dashboard.py
python forward_shadow_coverage_dashboard.py --send
```

## خروجی‌ها

```text
logs/research/v6_suite/forward_shadow_coverage_*.json
logs/research/v6_suite/forward_shadow_coverage_report_*.md
logs/research/v6_suite/forward_bull_probes_*.csv
logs/research/v6_suite/forward_shadow_gate_coverage_*.csv
```

## Safety

این ماژول فقط گزارش تحقیقاتی می‌سازد:

```text
Live Trading: NO
Paper Trade: NO
Shadow/Research: YES
```

## تفسیر خروجی

اگر `NO_BEAR_FORWARD_COVERAGE_YET` دیدی، یعنی Regime Bear gates سالم‌اند ولی هنوز داده Forward نزولی وجود ندارد.

اگر `FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT` دیدی، یعنی Forward کم‌نمونه خوب دیده شده اما Backtest آن را تأیید نمی‌کند؛ در این حالت نباید gate جدید فعال شود.
