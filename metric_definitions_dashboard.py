"""Freakto Metric Definitions CLI v4.7.1"""

import argparse

from engine.metric_definitions import format_metric_definitions_console, save_metric_definitions_report
from telegram_notifier import send_telegram_message


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Send metric definitions to Telegram.")
    args = parser.parse_args()

    text = format_metric_definitions_console()
    print(text)
    report_path = save_metric_definitions_report()
    print(f"📘 Metric definitions report ذخیره شد: {report_path}")
    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
