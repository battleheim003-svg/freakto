# خروجی نهایی: Freakto Airdrop Radar

## فایل‌های اصلی اضافه‌شده

```text
airdrop_radar.py                       اجرای ماژول ایردراپ از خط فرمان
airdrop/                               پکیج اصلی Airdrop Radar
  collectors/                          دریافت داده از watchlist، DefiLlama و RSS
  scoring/                             امتیازدهی اعتبار، پتانسیل پاداش، traction، هزینه/زمان، امنیت، timing
  security/                            چک دامنه و GoPlus اختیاری
  storage/                             دیتابیس SQLite برای فرصت‌ها
data/airdrop_watchlist.json            watchlist دستی قابل ویرایش
docs/AIRDROP_RADAR_README.md           راهنمای استفاده کامل
.env.example                           نمونه امن تنظیمات بدون secret
```

## دستورهای مهم

تست بدون ارسال تلگرام:

```bash
python airdrop_radar.py --once --dry-run
```

ارسال به تلگرام:

```bash
python airdrop_radar.py --once --send
```

اجرای دائمی:

```bash
python airdrop_radar.py --loop --send
```

## نکته امنیتی

فایل `.env` واقعی تو عمداً در خروجی clean قرار داده نشده، چون داخل آن توکن تلگرام و API key وجود داشت. از `.env.example` کپی بگیر و روی سیستم خودت مقدارها را وارد کن.
