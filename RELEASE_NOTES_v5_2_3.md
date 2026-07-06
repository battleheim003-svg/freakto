# Freakto v5.2.3 — GitHub Actions Restore Decode Hotfix

## هدف
رفع خطای Health Check در GitHub Actions هنگام restore کردن لاگ‌ها از branch `data-logs`.

## مشکل
در نسخه قبلی، اسکریپت `scripts/github_actions_restore_logs.py` یک بار `git archive` را با `text=True` اجرا می‌کرد. خروجی `git archive` باینری tar است و نباید مثل UTF-8 decode شود. این باعث خطایی مثل زیر می‌شد:

```text
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb6
```

## اصلاح
- حذف اجرای متنی `git archive`
- اضافه شدن probe امن با `git ls-tree`
- اجرای `git archive` فقط در حالت باینری
- decode کردن stderr فقط با `errors="replace"`

## فایل اصلاح‌شده

```text
scripts/github_actions_restore_logs.py
```

## بعد از نصب
1. فایل‌های update را روی repo لوکال کپی کن.
2. Commit و Push کن.
3. دوباره `Freakto Health Check` را با `send_telegram=false` اجرا کن.
4. مرحله `Restore previous Freakto logs` باید سبز شود.
