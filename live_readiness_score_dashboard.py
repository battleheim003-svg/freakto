"""Freakto Advanced Live Readiness Score CLI v4.7.1"""

import argparse

from engine.live_readiness_score import (
    assess_advanced_live_readiness,
    format_advanced_readiness_console,
    save_advanced_readiness,
)
from telegram_notifier import send_telegram_message


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Send advanced live readiness score to Telegram.")
    args = parser.parse_args()

    result = assess_advanced_live_readiness()
    text = format_advanced_readiness_console(result)
    print(text)
    json_path, report_path = save_advanced_readiness(result)
    print(f"🚦 Advanced readiness JSON ذخیره شد: {json_path}")
    print(f"📝 Advanced readiness report ذخیره شد: {report_path}")
    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
