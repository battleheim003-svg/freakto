
from __future__ import annotations

import argparse
from engine.root_cause_discovery import (
    format_root_cause_console,
    run_root_cause_discovery,
    save_root_cause_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Freakto v8 Root Cause Discovery dashboard")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="4h")
    parser.add_argument("--lookback-hours", type=int, default=168)
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()

    report = run_root_cause_discovery(symbol=args.symbol, timeframe=args.timeframe, lookback_hours=args.lookback_hours)
    print(format_root_cause_console(report, compact=args.compact))
    if not args.no_save:
        json_path, md_path, candidates_csv, obs = save_root_cause_report(report)
        print(f"🧬 Root cause JSON ذخیره شد: {json_path}")
        print(f"📝 Root cause report ذخیره شد: {md_path}")
        print(f"📊 Root cause candidates CSV ذخیره شد: {candidates_csv}")
        print(f"🧾 Root cause observations ledger ذخیره شد: {obs}")


if __name__ == "__main__":
    main()
