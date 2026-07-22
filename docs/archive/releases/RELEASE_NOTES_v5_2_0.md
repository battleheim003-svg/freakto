# Freakto v5.2.0 — GitHub Actions Free Forward Collector

## هدف

این نسخه امکان اجرای رایگان Forward Test را با GitHub Actions اضافه می‌کند تا بدون VPS و با خاموش بودن سیستم شخصی، Freakto بتواند هر 4 ساعت داده جمع کند، گزارش تلگرام بفرستد و لاگ‌ها را نگه دارد.

## فایل‌های جدید

```text
.github/workflows/freakto-forward-test.yml
scripts/github_actions_restore_logs.py
scripts/github_actions_push_logs.py
GITHUB_ACTIONS_SETUP_FA.md
RELEASE_NOTES_v5_2_0.md
```

## رفتار جدید

Workflow به صورت زمان‌بندی‌شده و دستی اجرا می‌شود:

```text
schedule: هر 4 ساعت
workflow_dispatch: اجرای دستی از تب Actions
```

چرخه اجرا:

```text
restore logs from data-logs branch
forward_test_dashboard.py --cycle --validate --continue-on-error --send
validation_suite_dashboard.py
upload logs artifact
push logs to data-logs branch
```

## امنیت

- `.env` و secrets داخل repo ذخیره نمی‌شوند.
- Tokenها باید از GitHub Repository Secrets خوانده شوند.
- لاگ‌ها در branch جداگانه `data-logs` ذخیره می‌شوند.
- اسکریپت push logs فقط فایل‌های whitelist شده را کپی می‌کند.

## Secretهای پیشنهادی

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
COINALYZE_API_KEY optional
OPENAI_API_KEY optional
ANTHROPIC_API_KEY optional
```

## نکته مهم

این نسخه جایگزین VPS برای اجرای واقعی یا Micro Live نیست؛ فقط برای Forward Test Collection رایگان طراحی شده است.
