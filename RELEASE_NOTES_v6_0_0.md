# Freakto v6.0.0 — Research Robustness & Intelligence Suite

## خلاصه

این نسخه ۱۱ مسیر ارتقای پیشنهادی را در قالب یک Suite تحقیقاتی کامل اضافه می‌کند. هدف نسخه v6 کاهش Overfitting، واقعی‌تر کردن Backtest، تقویت Decision Layer، مشاهده‌پذیری بهتر، آمادگی سخت‌گیرانه‌تر و آماده‌سازی مسیر Paper/Micro Live است.

## فایل‌های جدید

- `engine/research_utils.py`
- `engine/research_upgrade_suite.py`
- `freakto_research_suite_dashboard.py`
- `gate_robustness_dashboard.py`
- `cost_adjusted_backtest_dashboard.py`
- `meta_labeling_dashboard.py`
- `ensemble_explainability_dashboard.py`
- `data_enrichment_dashboard.py`
- `regime_research_dashboard.py`
- `cross_exchange_validation_dashboard.py`
- `research_db_dashboard.py`
- `pipeline_health_dashboard.py`
- `statistical_readiness_dashboard.py`
- `position_sizing_lab_dashboard.py`
- `airdrop_shadow_dashboard.py`
- `RESEARCH_ROBUSTNESS_RUNBOOK.md`

## فایل‌های اصلاح‌شده

- `validation_suite_dashboard.py`
- `.github/workflows/freakto-forward-test.yml`
- `.github/workflows/freakto-health-check.yml`
- `README_NEXT_STEPS.md`

## ایمنی

- هیچ سفارش واقعی ارسال نمی‌شود.
- هیچ Paper Trade جدید ساخته نمی‌شود.
- Meta-labeling و position sizing فقط research/shadow هستند.
- Airdrop Shadow هیچ wallet connect یا امضا انجام نمی‌دهد.

## تست سریع

```cmd
python gate_robustness_dashboard.py --horizon 24h --min-samples 30
python cost_adjusted_backtest_dashboard.py
python meta_labeling_dashboard.py
python freakto_research_suite_dashboard.py
python validation_suite_dashboard.py --iterations 20 --trades 10
```
