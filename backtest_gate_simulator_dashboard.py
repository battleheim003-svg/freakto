"""Freakto v5.3.2 - Backtest Gate Simulator CLI."""

import argparse

from engine.backtest_gate_simulator import (
    format_gate_simulation_console,
    run_gate_simulation,
    save_gate_simulation,
)
from telegram_notifier import send_telegram_message


def build_parser():
    parser = argparse.ArgumentParser(description="Freakto Backtest Gate Simulator v5.3.2")
    parser.add_argument("--horizon", choices=["4h", "12h", "24h"], default="24h", help="Return horizon used to judge edge")
    parser.add_argument("--min-samples", type=int, default=30, help="Minimum samples required for a full research candidate")
    parser.add_argument("--top", type=int, default=12, help="Number of top gates to show")
    parser.add_argument("--compact", action="store_true", help="Show fewer family breakdown sections")
    parser.add_argument("--include-zero-sample", action="store_true", help="Include gates with zero matching samples in saved results")
    parser.add_argument("--no-save", action="store_true", help="Do not save JSON/MD/CSV reports")
    parser.add_argument("--send", action="store_true", help="Send gate simulation summary to Telegram")
    return parser


def main():
    args = build_parser().parse_args()
    report = run_gate_simulation(
        horizon=args.horizon,
        min_samples=args.min_samples,
        include_zero_sample=args.include_zero_sample,
    )
    text = format_gate_simulation_console(report, detail=not args.compact, top=args.top)
    print(text)

    if not args.no_save:
        json_path, report_path, csv_path = save_gate_simulation(report)
        print(f"🧪 Gate simulation JSON ذخیره شد: {json_path}")
        print(f"📝 Gate simulation report ذخیره شد: {report_path}")
        print(f"📊 Gate simulation CSV ذخیره شد: {csv_path}")

    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
