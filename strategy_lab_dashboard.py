"""Freakto Strategy Lab CLI v4.7.1"""

import argparse
from telegram_notifier import send_telegram_message
from engine.strategy_lab import run_strategy_lab, save_strategy_results, format_strategy_lab_console


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Send report to Telegram.")
    args = parser.parse_args()

    results = run_strategy_lab()
    text = format_strategy_lab_console(results)
    print(text)
    csv_path, report_path = save_strategy_results(results)
    print(f"🧪 Strategy results ذخیره شد: {csv_path}")
    print(f"📝 Strategy report ذخیره شد: {report_path}")
    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
