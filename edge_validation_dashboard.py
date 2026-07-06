"""Freakto Edge Validation Dashboard CLI v4.7.0"""

import argparse

from engine.edge_validation import (
    format_edge_validation_console,
    run_edge_validation,
    save_edge_validation,
)
from telegram_notifier import send_telegram_message


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Send edge validation report to Telegram.")
    args = parser.parse_args()

    result = run_edge_validation()
    text = format_edge_validation_console(result)
    print(text)
    json_path, report_path = save_edge_validation(result)
    print(f"📐 Edge validation JSON ذخیره شد: {json_path}")
    print(f"📝 Edge validation report ذخیره شد: {report_path}")
    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
