"""Freakto v6.3 - Forward Shadow Coverage & Bull Regime Probe dashboard."""
import argparse

from engine.forward_shadow_coverage import (
    VERSION,
    format_forward_shadow_coverage_console,
    run_forward_shadow_coverage,
    save_forward_shadow_coverage,
)
from telegram_notifier import send_telegram_message


def build_parser():
    p = argparse.ArgumentParser(description=f"Freakto Forward Shadow Coverage & Bull Regime Probe {VERSION}")
    p.add_argument("--horizon", choices=["4h", "12h", "24h"], default="24h")
    p.add_argument("--min-samples", type=int, default=30)
    p.add_argument("--compact", action="store_true")
    p.add_argument("--no-save", action="store_true")
    p.add_argument("--send", action="store_true")
    return p


def main():
    args = build_parser().parse_args()
    report = run_forward_shadow_coverage(horizon=args.horizon, min_samples=args.min_samples)
    text = format_forward_shadow_coverage_console(report, compact=args.compact)
    print(text)
    if not args.no_save:
        json_path, md_path, bull_csv, gate_csv = save_forward_shadow_coverage(report)
        print(f"🔎 Forward shadow coverage JSON ذخیره شد: {json_path}")
        print(f"📝 Forward shadow coverage report ذخیره شد: {md_path}")
        print(f"📊 Bull probe CSV ذخیره شد: {bull_csv}")
        print(f"📊 Shadow gate coverage CSV ذخیره شد: {gate_csv}")
    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
