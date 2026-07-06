# Freakto v5.2.1 — GitHub Actions Operations Patch

این نسخه بعد از موفق شدن اولین اجرای GitHub Actions ساخته شد تا نگهداری Forward Collector ساده‌تر و قابل‌بررسی‌تر شود.

## Added

- `.github/workflows/freakto-health-check.yml`
  - اجرای سبک برای چک کردن وضعیت Forward Test بدون اجرای چرخه کامل بازار.
  - قابل اجرای دستی از تب Actions.
  - اجرای روزانه برای health/status report.

- `scripts/github_actions_health_summary.py`
  - ساخت خلاصه Markdown در GitHub Actions Summary.
  - خواندن `logs/forward_test_runs.csv` و آخرین `forward_test_status_*.json`.
  - ذخیره خروجی در `logs/github_actions/github_actions_health_summary.md`.
  - خروجی CI-friendly و بدون دسترسی به `.env` یا secrets.

## Changed

- `.github/workflows/freakto-forward-test.yml`
  - اضافه شدن `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` برای سازگاری بهتر با مهاجرت Node در GitHub Actions.
  - اضافه شدن مرحله `Build GitHub Actions health summary` بعد از اجرای Forward Cycle.
  - Artifactها حالا health summary را هم شامل می‌شوند.

- `GITHUB_ACTIONS_SETUP_FA.md`
  - اضافه شدن بخش «بعد از اولین اجرای موفق چه کار کنم؟».
  - اضافه شدن توضیح Health Check Workflow.
  - اضافه شدن چک‌لیست روزانه/هفتگی.

- `README_NEXT_STEPS.md`
  - مسیر بعدی بعد از فعال شدن GitHub Actions روشن‌تر شد.

## Safety

- این نسخه هیچ live trading یا order execution اضافه نمی‌کند.
- health workflow فقط status می‌گیرد و چرخه معاملاتی/دیتایی را اجرا نمی‌کند.
- secrets همچنان فقط از GitHub Secrets خوانده می‌شوند و وارد branch `data-logs` نمی‌شوند.
