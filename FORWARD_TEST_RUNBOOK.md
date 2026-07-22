# Freakto Forward Test Runbook — v5.1.1

> Canonical read-only status: `freakto report forward`. See
> [`docs/OPERATIONS.md`](docs/OPERATIONS.md). Legacy cycle commands below remain
> specialist compatibility paths and are governed by required CI policies.

این Runbook برای اجرای امن چرخه Forward Test در ویندوز است. این چرخه هیچ سفارش واقعی ارسال نمی‌کند.

## وضعیت فعلی

```cmd
python forward_test_dashboard.py --status
```

## دیدن برنامه اجرا

```cmd
python forward_test_dashboard.py --plan
```

## اجرای چرخه Forward Test

```cmd
python forward_test_dashboard.py --cycle --validate --continue-on-error
```

برای ارسال گزارش به Telegram:

```cmd
python forward_test_dashboard.py --cycle --validate --continue-on-error --send
```

## رفع مشکل Unicode در Windows

از v5.1.1، Forward Test Runner همه child processها را با UTF-8 اجرا می‌کند:

- `python -X utf8 ...`
- `PYTHONUTF8=1`
- `PYTHONIOENCODING=utf-8`

اگر از فایل batch استفاده می‌کنی، batchهای جدید را بساز:

```cmd
python forward_test_dashboard.py --write-bat
```

سپس:

```cmd
run_forward_test_cycle.bat
```

## هدف داده‌ای

- حداقل 100 ارزیابی کامل
- حداقل 30 Paper Trade بسته‌شده
- حداقل 30 نمونه دارای regime_label
- حداقل 30 روز Forward Test

تا وقتی Live Readiness خروجی `MICRO_LIVE_READY` ندهد، ورود با پول واقعی ممنوع است.


## v5.1.2 Decision Log Repair

If `decision_evaluator.py` fails with a pandas CSV parser error after `monitor.py --once`, run:

```cmd
python decision_log_repair.py
python decision_evaluator.py
```

The Forward Test cycle now runs the repair step automatically before evaluation.


## v5.3.3 Shadow Gate Step

از v5.3.3 چرخه Forward Test بعد از `decision_evaluator.py` این مرحله optional را اجرا می‌کند:

```cmd
python -X utf8 shadow_gate_dashboard.py --compact
```

این مرحله فقط Gateهای تحقیقاتی را روی تصمیم‌های Forward علامت‌گذاری می‌کند و هیچ Paper/Live ایجاد نمی‌کند. خروجی‌های آن در مسیر زیر ذخیره می‌شوند:

```text
logs/shadow_gates/
```

---

## v6.2 Regime Shadow Gate Activator داخل Forward Cycle

از v6.2 به بعد، مرحله `shadow_gate_validator` علاوه بر gateهای پایه، gateهای Regime-specific را هم رصد می‌کند:

```text
REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10
REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT
REGIME_TRENDING_BEAR__RISK_MEDIUM
REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT
```

برای تست دستی:

```cmd
python forward_test_dashboard.py --cycle --validate --continue-on-error
python shadow_gate_dashboard.py --compact
python regime_shadow_gate_dashboard.py --compact
```

این مرحله هیچ Paper/Live ایجاد نمی‌کند.

---

## v6.2.1 — Forward Regime Label Injection در Cycle

از v6.2.1 چرخه Forward این مرحله را قبل از `decision_evaluator` اجرا می‌کند:

```text
forward_regime_label_injection
Command: python -X utf8 forward_regime_label_dashboard.py --compact
```

این مرحله ستون‌های زیر را در لاگ‌های Forward تضمین می‌کند:

```text
regime_label, regime_confidence, regime_source, regime_label_quality,
trend_state, volatility_state, market_phase
```

تست دستی:

```cmd
python forward_regime_label_dashboard.py --compact
python forward_test_dashboard.py --plan
```

## v6.3 Forward Shadow Coverage Probe

در plan چرخه Forward، مرحله زیر اضافه شده است:

```text
forward_shadow_coverage_probe
Command: python -X utf8 forward_shadow_coverage_dashboard.py --compact
```

این مرحله فقط گزارش coverage می‌سازد و هیچ Paper/Live فعال نمی‌کند.


## v6.3.1 Bull Probe Evaluation Sync Patch

`forward_shadow_coverage_dashboard.py` now syncs Bull probe evaluation counts from the Shadow Ledger when decision evaluation rows are not marked COMPLETE yet. This is reporting-only and research-only.


## v6.4 causal_intelligence_probe

در چرخه Forward، task جدید `causal_intelligence_probe` اضافه شده است:

```cmd
python causal_intelligence_dashboard.py --compact
```

این task منابع بیرونی معتبر و manual_events را جمع‌آوری می‌کند و فقط report/log می‌سازد.


## v6.5.0 — Automatic Event Collector

این نسخه قبل از Causal Intelligence یک مرحله جدید اضافه می‌کند:

```cmd
python automatic_event_collector_dashboard.py --compact
```

خروجی اصلی آن `data/auto_events.csv` است. این فایل از منابع رسمی/معتبر ساخته می‌شود و Causal Intelligence آن را در کنار `manual_events.csv` می‌خواند. این لایه فقط Research است و Paper/Live فعال نمی‌کند.


## v6.5.1 Source Resilience Patch

Automatic Event Collector حالا برای sourceهای رسمی چند fallback دارد. بعد از آپدیت، این تست‌ها را اجرا کن:

```cmd
python automatic_event_collector_dashboard.py --sources
python automatic_event_collector_dashboard.py --compact
python causal_intelligence_dashboard.py --compact
```

اگر Binance/Coinbase/SEC Litigation باز هم fail شدند، چرخه Forward نباید متوقف شود؛ Source Health را بررسی کن و فقط در صورت fail دائمی patch بعدی لازم است.


## v7.0 — Market Narrative step

- `automatic_event_collector_dashboard.py --compact` اکنون noiseهای product/navigation را فیلتر می‌کند.
- `market_narrative_dashboard.py --compact` روایت بازار را از eventهای تمیز، causal context و driverهای اصلی می‌سازد.
- این لایه فقط Research-only است و هیچ Paper/Live ایجاد نمی‌کند.

## v7.1 — Narrative/Decision Conflict Scoring

مرحله جدید:

```cmd
python narrative_decision_dashboard.py --compact
```

این مرحله بررسی می‌کند روایت بازار با تصمیم فعلی هم‌جهت است یا نه و این فیلدها را برای Research/Forward اضافه می‌کند:

- `narrative_alignment`
- `narrative_conflict_score`
- `narrative_adjustment`
- `narrative_adjusted_score`
- `narrative_action_override`
- `narrative_decision_verdict`

این لایه هیچ Paper/Live/Order واقعی فعال نمی‌کند.



## v8 Root Cause step

در چرخه Forward مرحله زیر بعد از narrative_decision_conflict_probe اجرا می‌شود:

```text
root_cause_discovery_probe
Command: python -X utf8 root_cause_dashboard.py --compact
```

این مرحله Paper/Live فعال نمی‌کند.

---

## v8.1 Root Cause Forward Validation در Forward Cycle

از v8.1 به بعد، بعد از `decision_evaluator` مرحله زیر اجرا می‌شود:

```cmd
python root_cause_forward_validation_dashboard.py --compact
```

این مرحله از `logs/decision_evaluations.csv` استفاده می‌کند و hit-rate علت‌ها را در افق‌های 4h، 12h و 24h می‌سنجد.

هیچ سفارش واقعی و هیچ Paper Trade جدیدی ایجاد نمی‌شود.

---

## v8.1.1 Root Cause Bridge Note

`decision_evaluator.py` اکنون اگر آخرین Root Cause report با `decision_id` تصمیم جاری match شود، فیلدهای `root_cause_*` را به `decision_evaluations.csv` منتقل می‌کند. این باعث می‌شود `root_cause_forward_validation_dashboard.py` بتواند sampleهای واقعی بسازد.

---

## v8.2 Root Cause Sample Tracker

Forward Plan از v8.2 شامل این مرحله است:

```text
root_cause_sample_tracker
Command: python -X utf8 root_cause_sample_dashboard.py --compact
```

این مرحله باید بعد از `root_cause_forward_validation_probe` اجرا شود. وظیفه آن پایش بلوغ sampleها است، نه تولید سیگنال.

ترتیب پیشنهادی:

```text
root_cause_discovery_probe
decision_evaluator
root_cause_forward_validation_probe
root_cause_sample_tracker
```


## v9 Evidence Graph Probe

Forward plan اکنون شامل `evidence_graph_probe` است:

```cmd
python evidence_graph_dashboard.py --compact
```

این مرحله باید بعد از root cause sample tracker اجرا شود و هیچ Paper/Live فعال نمی‌کند.
