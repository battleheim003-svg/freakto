from __future__ import annotations

import argparse

from engine.root_cause_sample_tracker import (
    format_root_cause_sample_console,
    run_root_cause_sample_tracker,
    save_root_cause_sample_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Freakto v8.2 Root Cause Sample Accumulator dashboard")
    parser.add_argument("--min-cells", type=int, default=10)
    parser.add_argument("--research-cells", type=int, default=30)
    parser.add_argument("--candidate-cells", type=int, default=90)
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()

    report = run_root_cause_sample_tracker(
        min_cells=args.min_cells,
        research_cells=args.research_cells,
        candidate_cells=args.candidate_cells,
    )
    print(format_root_cause_sample_console(report, compact=args.compact))
    if not args.no_save:
        json_path, md_path, buckets_csv, obs = save_root_cause_sample_report(report)
        print(f"🧫 Root cause sample JSON ذخیره شد: {json_path}")
        print(f"📝 Root cause sample report ذخیره شد: {md_path}")
        print(f"📊 Root cause sample buckets CSV ذخیره شد: {buckets_csv}")
        print(f"🧾 Root cause sample observations ledger ذخیره شد: {obs}")


if __name__ == "__main__":
    main()
