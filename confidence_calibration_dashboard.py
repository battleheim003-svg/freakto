"""Freakto Confidence Calibration Dashboard CLI v5.0"""

import argparse

from engine.confidence_calibration import run_confidence_calibration, format_confidence_calibration_console, save_confidence_calibration
from telegram_notifier import send_telegram_message


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Send confidence calibration report to Telegram.")
    args = parser.parse_args()

    result = run_confidence_calibration()
    text = format_confidence_calibration_console(result)
    print(text)
    json_path, report_path = save_confidence_calibration(result)
    print(f"🎯 Confidence calibration JSON ذخیره شد: {json_path}")
    print(f"📝 Confidence calibration report ذخیره شد: {report_path}")
    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
