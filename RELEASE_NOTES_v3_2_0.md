# Freakto v3.2.0 — Learning Config & Auto-Tuning Advisor

## هدف

نسخه 3.1 خروجی Self-Learning تولید می‌کرد، اما آن خروجی هنوز به یک تنظیمات قابل استفاده تبدیل نمی‌شد.
در v3.2 یک لایه امن بین «یادگیری» و «اعمال تغییر» اضافه شد.

## قابلیت‌های جدید

### Learning Config Advisor

فایل جدید:

```text
engine/learning_config.py
```

این موتور فایل زیر را می‌خواند:

```text
logs/learning/self_learning_recommendations.json
```

و بر اساس نمونه‌های COMPLETE، یک برنامه تنظیمات محافظه‌کارانه می‌سازد.

### Learning Config Dashboard

فایل جدید:

```text
learning_config_dashboard.py
```

اجرا:

```cmd
python learning_config_dashboard.py
```

بازسازی توصیه‌های Self-Learning و ساخت config advisory:

```cmd
python learning_config_dashboard.py --refresh
```

ساخت فایل staging برای نسخه‌های آینده:

```cmd
python learning_config_dashboard.py --stage
```

ارسال تلگرام:

```cmd
python learning_config_dashboard.py --send
```

## خروجی‌ها

```text
logs/learning/learning_config_advisory.json
logs/learning/learning_config_report.md
config/learning_overrides.json  # فقط با --stage
```

## سیاست ایمنی

در v3.2 هیچ وزن اجرایی به صورت خودکار تغییر نمی‌کند.
حتی اگر `--stage` اجرا شود، فایل `config/learning_overrides.json` فقط staging است و Decision Engine هنوز آن را اعمال نمی‌کند.

## مسیر بعدی

v3.3 می‌تواند Opt-in Runtime Learning Overrides را اضافه کند؛ یعنی فقط وقتی کاربر صریحاً فعال کند، موتور از این فایل تنظیمات استفاده کند.
