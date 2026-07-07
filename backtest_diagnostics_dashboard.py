"""Freakto v5.3.1 - Backtest Diagnostics CLI."""

import argparse

from engine.backtest_diagnostics import (
    format_diagnostics_console,
    run_backtest_diagnostics,
    save_backtest_diagnostics,
)
from telegram_notifier import send_telegram_message


def build_parser():
    parser = argparse.ArgumentParser(description="Freakto Backtest Diagnostics & Edge Breakdown v5.3.1")
    parser.add_argument("--send", action="store_true", help="Send diagnostics summary to Telegram")
    parser.add_argument("--compact", action="store_true", help="Show fewer breakdown sections")
    parser.add_argument("--no-save", action="store_true", help="Do not save JSON/MD reports")
    return parser


def main():
    args = build_parser().parse_args()
    diag = run_backtest_diagnostics()
    text = format_diagnostics_console(diag, detail=not args.compact)
    print(text)

    if not args.no_save:
        json_path, report_path = save_backtest_diagnostics(diag)
        print(f"🧪 Backtest diagnostics JSON ذخیره شد: {json_path}")
        print(f"📝 Backtest diagnostics report ذخیره شد: {report_path}")

    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
