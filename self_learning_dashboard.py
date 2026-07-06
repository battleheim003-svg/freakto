"""
self_learning_dashboard.py

Freakto Self-Learning Dashboard - v3.1.0

اجرا:
    python self_learning_dashboard.py
    python self_learning_dashboard.py --send

این اسکریپت decision_evaluations.csv و decisions.csv را می‌خواند و پیشنهادهای
یادگیری/بهینه‌سازی تولید می‌کند. هیچ تغییری را خودکار اعمال نمی‌کند.
"""

import argparse

from telegram_notifier import send_telegram_message
from engine.self_learning import (
    build_self_learning_report,
    format_self_learning_console,
    format_self_learning_telegram,
    save_self_learning_report,
    save_recommendations_json,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send self-learning summary to Telegram.",
    )
    args = parser.parse_args()

    report = build_self_learning_report()

    print(format_self_learning_console(report))

    report_path = save_self_learning_report(report)
    json_path = save_recommendations_json(report)

    print(f"🧠 Self-learning report ذخیره شد: {report_path}")
    print(f"🧾 Learning recommendations ذخیره شد: {json_path}")

    if args.send:
        ok = send_telegram_message(format_self_learning_telegram(report))
        if ok:
            print("✅ گزارش Self-Learning به تلگرام ارسال شد")
        else:
            print("⚠️ گزارش Self-Learning به تلگرام ارسال نشد")


if __name__ == "__main__":
    main()
