"""Freakto Regime Performance Matrix Dashboard CLI v4.7.1"""

import argparse

from engine.regime_matrix import (
    format_regime_matrix_console,
    run_regime_matrix,
    save_regime_matrix,
)
from telegram_notifier import send_telegram_message


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Send regime matrix report to Telegram.")
    args = parser.parse_args()

    result = run_regime_matrix()
    text = format_regime_matrix_console(result)
    print(text)
    csv_path, report_path = save_regime_matrix(result)
    print(f"🧬 Regime matrix CSV ذخیره شد: {csv_path}")
    print(f"📝 Regime matrix report ذخیره شد: {report_path}")
    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
