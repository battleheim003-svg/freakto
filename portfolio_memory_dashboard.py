"""Freakto Portfolio Memory Dashboard CLI v5.0"""

import argparse

from engine.portfolio_memory import build_portfolio_memory, format_portfolio_memory_console, save_portfolio_memory
from telegram_notifier import send_telegram_message


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Send portfolio memory report to Telegram.")
    args = parser.parse_args()

    result = build_portfolio_memory()
    text = format_portfolio_memory_console(result)
    print(text)
    json_path, report_path = save_portfolio_memory(result)
    print(f"🧠 Portfolio memory JSON ذخیره شد: {json_path}")
    print(f"📝 Portfolio memory report ذخیره شد: {report_path}")
    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
