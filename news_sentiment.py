"""
دریافت آخرین اخبار کریپتو و امتیازدهی احساسات (Sentiment) با استفاده از API اوپن‌ای‌آی.

منبع خبر: فیدهای RSS رایگان CoinDesk و CoinTelegraph (بدون نیاز به کلید API؛
سرویس‌های خبری قبلی مثل CryptoCompare الان نیاز به احراز هویت دارند).

تحلیل احساسات: OpenAI Chat Completions API (نیاز به OPENAI_API_KEY در config.py).

نکته‌ی مهم: این ماژول فقط اخبار «الان» را می‌گیرد؛ آرشیو تاریخی معتبری برای
اخبار وجود ندارد. پس نمی‌توان با این چند سال به عقب بک‌تست کرد. راه‌حل:
از همین امروز با live_data_logger.py هر بار که چک می‌شود، امتیاز احساسات
را ذخیره می‌کنیم تا بعد از چند هفته/ماه، تاریخچه‌ی کافی برای تحلیل آماری
واقعی داشته باشیم.
"""

import json
import xml.etree.ElementTree as ET

import requests

from config import OPENAI_API_KEY, OPENAI_MODEL

RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
]
OPENAI_API_URL = "https://api.gapgpt.app/v1/chat/completions"


def _parse_rss(xml_text: str, max_items: int = 10) -> list:
    """پارس ساده‌ی RSS با کتابخونه‌ی استاندارد پایتون (بدون نیاز به کتابخونه‌ی اضافه)."""
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items

    for item in root.findall(".//item")[:max_items]:
        title_el = item.find("title")
        pub_el = item.find("pubDate")
        if title_el is not None and title_el.text:
            items.append({
                "title": title_el.text.strip(),
                "published_on": pub_el.text.strip() if pub_el is not None and pub_el.text else None,
            })
    return items


def fetch_latest_news(max_items_per_feed: int = 10) -> list:
    """دریافت آخرین عناوین خبری از چند فید RSS رایگان کریپتو."""
    all_items = []
    for url in RSS_FEEDS:
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            items = _parse_rss(resp.text, max_items=max_items_per_feed)
            all_items.extend(items)
        except requests.RequestException as e:
            print(f"خطا در دریافت RSS از {url}: {e}")
    return all_items


def score_sentiment_with_openai(headlines: list) -> dict:
    """
    عناوین خبری را به مدل OpenAI می‌دهد و یک امتیاز کلی احساسات بین -1 (خیلی منفی)
    تا +1 (خیلی مثبت) به همراه توضیح کوتاه می‌گیرد.
    """
    if not headlines:
        return {"score": 0.0, "summary": "خبری یافت نشد."}

    headlines_text = "\n".join(f"- {h['title']}" for h in headlines)

    prompt = (
        "You are a financial news sentiment analyzer for the crypto market (Bitcoin/BTC). "
        "Given the following recent headlines, respond ONLY with a JSON object in this exact "
        "format, nothing else, no markdown fences:\n"
        '{"score": <float between -1.0 and 1.0>, "summary": "<one short sentence in English '
        'explaining the overall sentiment and why>"}\n\n'
        "score meaning: -1.0 = extremely bearish/fearful news, 0.0 = neutral/mixed, "
        "1.0 = extremely bullish/optimistic news.\n\n"
        f"Headlines:\n{headlines_text}"
    )

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0,
    }

    resp = requests.post(OPENAI_API_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    result = resp.json()

    text = result["choices"][0]["message"]["content"].strip()

    try:
        parsed = json.loads(text)
        return {"score": float(parsed["score"]), "summary": parsed.get("summary", "")}
    except (json.JSONDecodeError, KeyError, ValueError, IndexError) as e:
        print(f"خطا در پردازش پاسخ مدل: {e}\nپاسخ خام: {text}")
        return {"score": 0.0, "summary": "خطا در تحلیل - امتیاز خنثی در نظر گرفته شد."}


def get_current_sentiment() -> dict:
    """تابع اصلی: اخبار را می‌گیرد و امتیاز احساسات فعلی را برمی‌گرداند."""
    headlines = fetch_latest_news()
    result = score_sentiment_with_openai(headlines)
    result["headline_count"] = len(headlines)
    return result


if __name__ == "__main__":
    sentiment = get_current_sentiment()
    print(f"امتیاز احساسات فعلی: {sentiment['score']:.2f}")
    print(f"خلاصه: {sentiment['summary']}")
    print(f"تعداد عناوین بررسی‌شده: {sentiment['headline_count']}")