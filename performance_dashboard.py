"""
performance_dashboard.py

Freakto Performance & Learning Dashboard - v3.0.0

اجرا:
    python performance_dashboard.py
    python performance_dashboard.py --send

این اسکریپت لاگ‌های Freakto را می‌خواند و یک گزارش عملکرد Markdown می‌سازد.
"""

import argparse

from telegram_notifier import send_telegram_message
from engine.performance import (
    build_performance_report,
    format_performance_console,
    format_performance_telegram,
    save_performance_report,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send performance summary to Telegram.",
    )
    args = parser.parse_args()

    report = build_performance_report()

    print(format_performance_console(report))

    path = save_performance_report(report)
    print(f"📈 Performance report ذخیره شد: {path}")

    if args.send:
        ok = send_telegram_message(format_performance_telegram(report))
        if ok:
            print("✅ گزارش عملکرد به تلگرام ارسال شد")
        else:
            print("⚠️ گزارش عملکرد به تلگرام ارسال نشد")


if __name__ == "__main__":
    main()
