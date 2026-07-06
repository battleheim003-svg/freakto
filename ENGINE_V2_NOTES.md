# Freakto Opportunity Engine v2

این نسخه موتور Opportunity را ماژولار کرده است.

## فایل‌های جدید

```text
engine/
  common.py
  trend.py
  momentum.py
  volume.py
  structure.py
  risk.py
  score.py
```

## خروجی جدید

پیام تلگرام حالا Score Breakdown دارد:

```text
Trend: +28
Momentum: +21
Volume: +7
Structure: +0
Risk Penalty: -6
Final Score: 50/100
```

## اجرای پروژه

```bash
.venv\Scripts\activate
pip install -r requirements.txt
python monitor.py
```

## تنظیمات مهم در .env

```env
EXCHANGE_ID=okx
OPPORTUNITY_MIN_SCORE=70
SEND_NEUTRAL_REPORTS=false
```

اگر OKX جواب ندهد، پروژه خودکار KuCoin، Kraken و Bybit را امتحان می‌کند.
