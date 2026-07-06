"""
تست سریع و مستقل اتصال به API اوپن‌ای‌آی - جدا از بقیه‌ی پروژه.
اگر این هم خطا داد، مشکل قطعاً از کلید/حساب OpenAI است، نه از کد پروژه.
"""

import requests
from config import OPENAI_API_KEY, OPENAI_MODEL

print(f"کلید استفاده‌شده (۸ کاراکتر اول): {OPENAI_API_KEY[:8]}...")
print(f"مدل: {OPENAI_MODEL}\n")

headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json",
}
payload = {
    "model": OPENAI_MODEL,
    "messages": [{"role": "user", "content": "فقط بگو: سلام، اتصال موفق بود."}],
}

try:
    resp = requests.post("https://api.gapgpt.app/v1/chat/completions", headers=headers, json=payload, timeout=20)
    print(f"کد وضعیت پاسخ: {resp.status_code}")
    print(f"متن کامل پاسخ:\n{resp.text}")
except Exception as e:
    print(f"خطای اتصال: {e}")
