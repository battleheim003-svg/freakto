# Freakto v6.0 — Research Robustness & Intelligence Suite

این نسخه ۱۱ مسیر بهبود را به شکل research-only وارد Freakto می‌کند. هیچ بخش این نسخه سفارش واقعی ارسال نمی‌کند و Paper Trade جدید نمی‌سازد.

## اجرای همه بخش‌ها

```cmd
python freakto_research_suite_dashboard.py
```

ارسال خلاصه به تلگرام:

```cmd
python freakto_research_suite_dashboard.py --send
```

## داشبوردهای جداگانه

```cmd
python gate_robustness_dashboard.py --horizon 24h --min-samples 30
python cost_adjusted_backtest_dashboard.py --fee-bps 10 --slippage-bps 5
python meta_labeling_dashboard.py --horizon 24h
python ensemble_explainability_dashboard.py
python data_enrichment_dashboard.py
python regime_research_dashboard.py
python cross_exchange_validation_dashboard.py
python research_db_dashboard.py
python pipeline_health_dashboard.py
python statistical_readiness_dashboard.py
python position_sizing_lab_dashboard.py
python airdrop_shadow_dashboard.py
```

## خروجی‌ها

```text
logs/research/v6_suite/*.json
logs/research/v6_suite/*.md
logs/research/freakto_research.db
logs/research_dashboard/index.html
```

## ۱۱ بخش پیاده‌سازی‌شده

1. Gate Robustness / Walk-forward / Multiple-testing penalty / Embargo proxy
2. Cost-adjusted Backtest با Fee و Slippage
3. Meta-labeling Research Layer
4. Ensemble و Explainability برای score و componentها
5. Data Enrichment Readiness برای on-chain/derivatives/microstructure
6. Regime Research رسمی‌تر
7. Cross-exchange validation بر اساس provider
8. SQLite Research DB
9. Static HTML Dashboard و Pipeline Health Monitoring
10. Strict Statistical Readiness شامل CI، t-stat، regime coverage و BTC beta check
11. Position Sizing Lab و Airdrop Shadow Research

## محدودیت مهم

خروجی‌های v6 برای تصمیم live کافی نیستند. هر gate یا مدل باید بعد از Backtest، در Shadow/Forward نمونه کافی بگیرد.

---

## v6.1 — Regime-Split Gate Matrix

برای بررسی اینکه Gateهای مثبت فقط در بعضی Regimeها Edge دارند یا نه:

```cmd
python regime_gate_matrix_dashboard.py --compact
python regime_gate_matrix_dashboard.py --compact --primary-only
```

این بخش خروجی‌های زیر را می‌سازد:

```text
logs/research/v6_suite/regime_gate_matrix_*.json
logs/research/v6_suite/regime_gate_matrix_results_*.csv
logs/research/v6_suite/regime_gate_side_matrix_results_*.csv
logs/research/v6_suite/regime_avoid_candidates_*.csv
logs/research/v6_suite/regime_shadow_proposals_*.json
```

v6.1 به `freakto_research_suite_dashboard.py` و `validation_suite_dashboard.py` هم وصل شده است.

---

## v6.2 — Regime Shadow Gate Activator

بعد از اینکه v6.1 ترکیب‌های Regime/Gate را پیدا کرد، v6.2 آن‌ها را در Shadow Forward فعال می‌کند. این بخش داخل Research Suite با نام زیر دیده می‌شود:

```text
regime_shadow_gates
```

دستورهای اصلی:

```cmd
python shadow_gate_dashboard.py --compact
python regime_shadow_gate_dashboard.py --compact
python freakto_research_suite_dashboard.py
```

---

## v6.2.1 — Forward Regime Labeling در Research Suite

Research Suite از v6.2.1 بخش جدیدی دارد:

```text
forward_regime_labeling
```

این بخش به‌صورت dry-run نشان می‌دهد چند decision/evaluation دارای regime قابل‌استفاده هستند و چند ردیف هنوز UNKNOWN مانده‌اند.

## v6.3 Forward Shadow Coverage

ماژول جدید `forward_shadow_coverage_dashboard.py` به Research Suite اضافه شد. این ماژول coverage تصمیم‌های Forward، Shadow Gateها و Bull regime probes را با Backtest مقایسه می‌کند.


## v6.3.1 Bull Probe Evaluation Sync Patch

`forward_shadow_coverage_dashboard.py` now syncs Bull probe evaluation counts from the Shadow Ledger when decision evaluation rows are not marked COMPLETE yet. This is reporting-only and research-only.


## v6.4 Causal/Event Intelligence

Causal Intelligence به Research Suite اضافه شد تا primary_cause، catalyst_score، event_risk، technical_event_conflict و causal_verdict را کنار تصمیم‌ها ذخیره کند. این داده‌ها بعداً برای Conflict Lab و cause/outcome evaluation استفاده می‌شوند.


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


## v7.0 — Narrative research layer

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



## v8 Root Cause Discovery

Root Cause Discovery به Research Suite اضافه شد و باید قبل از هر گونه فعال‌سازی gate با forward outcomeها اعتبارسنجی شود.
