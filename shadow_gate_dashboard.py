"""Freakto v6.2.0 - Regime Shadow Gate Activator CLI.

Runs the shadow validator for both:
- base Backtest/Gate Simulator candidates
- v6.1 Regime-Gate Matrix candidates activated in SHADOW_ONLY mode
"""

import argparse

from engine.shadow_gates import (
    VERSION,
    format_shadow_gate_console,
    run_shadow_gate_validation,
    save_shadow_gate_validation,
)
from telegram_notifier import send_telegram_message


def build_parser():
    parser = argparse.ArgumentParser(description=f"Freakto Regime Shadow Gate Activator {VERSION}")
    parser.add_argument("--horizon", choices=["4h", "12h", "24h"], default="24h", help="Forward return horizon for gate evaluation")
    parser.add_argument("--min-samples", type=int, default=30, help="Minimum complete Forward samples per gate before confirmation")
    parser.add_argument("--compact", action="store_true", help="Hide recent signal details")
    parser.add_argument("--no-save", action="store_true", help="Do not save reports")
    parser.add_argument("--send", action="store_true", help="Send shadow summary to Telegram")
    return parser


def main():
    args = build_parser().parse_args()
    report = run_shadow_gate_validation(horizon=args.horizon, min_samples=args.min_samples)
    text = format_shadow_gate_console(report, detail=not args.compact)
    print(text)

    if not args.no_save:
        json_path, report_path, metrics_csv, signals_csv = save_shadow_gate_validation(report)
        print(f"🧪 Shadow gate JSON ذخیره شد: {json_path}")
        print(f"📝 Shadow gate report ذخیره شد: {report_path}")
        print(f"📊 Shadow gate metrics ذخیره شد: {metrics_csv}")
        print(f"🧾 Shadow gate signals ذخیره شد: {signals_csv}")

    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
