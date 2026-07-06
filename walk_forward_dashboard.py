"""Freakto Walk-Forward Validation CLI v4.7.1"""

import argparse
from telegram_notifier import send_telegram_message
from engine.walk_forward import run_walk_forward_validation, save_walk_forward_results, format_walk_forward_console


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Send report to Telegram.")
    args = parser.parse_args()

    results = run_walk_forward_validation()
    text = format_walk_forward_console(results)
    print(text)
    csv_path, report_path = save_walk_forward_results(results)
    print(f"🧭 Walk-forward results ذخیره شد: {csv_path}")
    print(f"📝 Walk-forward report ذخیره شد: {report_path}")
    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
