from __future__ import annotations

import argparse

from engine.root_cause_forward_validation import (
    format_root_cause_forward_console,
    run_root_cause_forward_validation,
    save_root_cause_forward_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Freakto v8.1 Root Cause Forward Validation dashboard")
    parser.add_argument("--horizon", default="24h", choices=["4h", "12h", "24h"])
    parser.add_argument("--min-samples", type=int, default=10)
    parser.add_argument("--min-abs-return", type=float, default=0.0, help="Deadzone for flat market moves in percent.")
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()

    report = run_root_cause_forward_validation(
        horizon=args.horizon,
        min_samples=args.min_samples,
        min_abs_return_pct=args.min_abs_return,
    )
    print(format_root_cause_forward_console(report, compact=args.compact))
    if not args.no_save:
        json_path, md_path, summary_csv, rows_csv, obs = save_root_cause_forward_report(report)
        print(f"🧪 Root cause forward JSON ذخیره شد: {json_path}")
        print(f"📝 Root cause forward report ذخیره شد: {md_path}")
        print(f"📊 Root cause forward summary CSV ذخیره شد: {summary_csv}")
        print(f"📄 Root cause forward rows CSV ذخیره شد: {rows_csv}")
        print(f"🧾 Root cause forward observations ledger ذخیره شد: {obs}")


if __name__ == "__main__":
    main()
