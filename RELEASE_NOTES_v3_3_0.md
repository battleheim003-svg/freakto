# Freakto v3.3.0 — Safe Learning Override Loader

## هدف

در v3.2 فایل `config/learning_overrides.json` به‌صورت staging ساخته می‌شد، اما Decision Engine هنوز آن را نمی‌خواند.
در v3.3 یک لایه امن اضافه شد تا Decision Engine بتواند فایل override را بخواند، اما فقط در شرایط کنترل‌شده و محافظه‌کارانه اثر اعمال کند.

## قابلیت‌های اضافه‌شده

### 1. Safe Learning Override Loader

فایل جدید:

```text
engine/learning_overrides.py
```

این ماژول:

- `config/learning_overrides.json` را می‌خواند.
- اگر فایل وجود نداشته باشد، هیچ اثری نمی‌گذارد.
- اگر `enabled=false` یا `auto_apply=false` باشد، اعمال نمی‌کند.
- اگر تعداد `complete_evaluations` کمتر از 30 باشد، اعمال نمی‌کند.
- فقط کلیدهای امن allowlist شده را می‌پذیرد.
- مولتی‌پلایرها را به بازه محافظه‌کارانه 0.80 تا 1.20 محدود می‌کند.

### 2. Decision Engine Integration

فایل تغییرکرده:

```text
engine/decision.py
```

Decision Engine حالا قبل از Adaptive Adjustment، وضعیت Learning Override را بررسی می‌کند.
اگر فایل staging وجود داشته باشد، یک کامپوننت صفر امتیازی در Score Breakdown اضافه می‌شود:

```text
Learning Override: 0/10
```

این کامپوننت نشان می‌دهد Override فعال نشده، بلوکه شده، یا در صورت کافی بودن داده‌ها اعمال شده است.

### 3. Learning Override Status CLI

فایل جدید:

```text
learning_override_status.py
```

اجرا:

```cmd
python learning_override_status.py
```

خروجی نشان می‌دهد:

- فایل وجود دارد یا نه
- enabled / auto_apply چیست
- data_readiness چیست
- تعداد complete evaluations چقدر است
- آیا چیزی اعمال شده یا بلوکه شده است

### 4. Learning Config v3.3

فایل‌های تغییرکرده:

```text
engine/learning_config.py
learning_config_dashboard.py
```

فایل staging همچنان به‌صورت disabled ساخته می‌شود، اما توضیح آن با Safe Loader v3.3 هماهنگ شد.

## ایمنی

v3.3 هنوز خودکار وزن‌ها را تغییر نمی‌دهد مگر اینکه کاربر عمداً در `config/learning_overrides.json` مقدارهای زیر را فعال کند:

```json
{
  "enabled": true,
  "auto_apply": true
}
```

حتی در این حالت هم اگر نمونه کافی وجود نداشته باشد یا readiness امن نباشد، Decision Engine اعمال را بلوکه می‌کند.

## تست پیشنهادی

```cmd
python self_learning_dashboard.py
python learning_config_dashboard.py --stage
python learning_override_status.py
python monitor.py --once
```

در وضعیت فعلی با کمتر از 30 evaluation کامل، انتظار می‌رود Override اعمال نشود و فقط گزارش شود.
