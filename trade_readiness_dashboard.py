"""Freakto Trade Readiness Gate CLI v4.7.1"""

import argparse
from telegram_notifier import send_telegram_message
from engine.trade_readiness import (
    assess_global_live_readiness,
    format_readiness_report,
    load_global_readiness_stats,
    save_readiness_report,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Send report to Telegram.")
    args = parser.parse_args()

    stats = load_global_readiness_stats()
    decision = assess_global_live_readiness(stats)
    text = format_readiness_report(decision, stats)
    print(text)
    path = save_readiness_report(text)
    print(f"🚦 Trade readiness report ذخیره شد: {path}")
    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
