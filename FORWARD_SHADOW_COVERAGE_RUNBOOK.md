# Freakto v6.3.1.1 — Bull Probe Evaluation Sync Patch

این ماژول برای مرحله بعد از v6.2.1 ساخته شده است.

## هدف

v6.2.1 نشان داد که `regime_label` درست وارد Forward logs شده، اما Forward فعلی بیشتر/کاملاً `TRENDING_BULL` است و Regime Bear gates طبیعی است که signal نگیرند. v6.3.1 این مسئله را رسمی تحلیل می‌کند.

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

## v6.3.1 Sync Fix

This patch fixes a reporting mismatch where `STRUCTURE_SCORE_GE_10` could show evaluated Shadow results while Bull probes still reported `NO_FORWARD_SAMPLE`. The Bull probe now falls back to `logs/shadow_gates/shadow_gate_signals.csv` when the joined `decision_evaluations.csv` view has no COMPLETE rows for the same probe.

This is still research-only and does not promote Bull probes to Paper/Live.
