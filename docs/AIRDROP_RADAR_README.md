# Freakto Airdrop Radar

این ماژول کنار ربات ترید Freakto کار می‌کند و هدفش این نیست که فقط لیست ایردراپ‌ها را کپی کند. هدف این است که هر فرصت را با منطق زیر بررسی کند:

```text
کشف فرصت → حذف تکراری‌ها → اعتبارسنجی اولیه → امتیازدهی → ذخیره در دیتابیس → گزارش تلگرام
```

## اجرای سریع

```bash
pip install -r requirements.txt
python airdrop_radar.py --once --dry-run
```

برای ارسال به تلگرام:

```bash
python airdrop_radar.py --once --send
```

برای اجرای دائمی:

```bash
python airdrop_radar.py --loop --send
```

## تنظیمات `.env`

این‌ها را به فایل `.env` اضافه کن:

```env
AIRDROP_MIN_SCORE=65
AIRDROP_MAX_ITEMS_PER_RUN=8
AIRDROP_CHECK_INTERVAL_MINUTES=360
AIRDROP_USE_DEFILLAMA=true
AIRDROP_DEFILLAMA_MIN_TVL=1000000
AIRDROP_DEFILLAMA_MAX_ITEMS=200
AIRDROP_WATCHLIST_FILE=data/airdrop_watchlist.json
AIRDROP_DB_PATH=history/airdrop_radar.db
AIRDROP_RSS_FEEDS=
AIRDROP_DOMAIN_BLACKLIST=
GOPLUS_API_TOKEN=
```

## فایل watchlist دستی

فایل زیر را ویرایش کن:

```text
data/airdrop_watchlist.json
```

هر پروژه باید تا حد ممکن این اطلاعات را داشته باشد:

```json
{
  "name": "Project Name",
  "official_url": "https://project.xyz",
  "docs_url": "https://docs.project.xyz",
  "twitter_url": "https://x.com/project",
  "category": "DeFi",
  "chains": ["Ethereum", "Base"],
  "task_type": "protocol interaction",
  "token_status": "tokenless-likely",
  "tvl_usd": 10000000,
  "estimated_minutes": 25,
  "estimated_cost_usd": 4,
  "tags": ["tokenless", "points"]
}
```

## سطح‌بندی خروجی

| Level | Score | معنی |
|---|---:|---|
| 🟢 ELITE | 85+ | فرصت جدی با ریسک اولیه قابل قبول |
| 🟢 ACTIONABLE | 70-84 | ارزش اقدام دارد، بعد از چک نهایی لینک‌ها |
| 🟡 WATCHLIST | 55-69 | زیر نظر بماند، اقدام سنگین نکن |
| 🔵 MONITOR ONLY | 40-54 | فقط رصد شود |
| 🔴 AVOID | زیر 40 | ریسک/بازده مناسب نیست |

## نکته امنیتی مهم

این ربات عمداً این کارها را انجام نمی‌دهد:

```text
- private key نمی‌گیرد
- seed phrase نمی‌گیرد
- wallet وصل نمی‌کند
- تراکنش را خودکار sign نمی‌کند
- claim یا approve خودکار انجام نمی‌دهد
```

برای فارم‌کردن ایردراپ، همیشه از wallet تازه و کم‌موجودی استفاده کن.
