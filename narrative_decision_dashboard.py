from __future__ import annotations

import argparse
from engine.narrative_decision_conflict import (
    format_narrative_decision_console,
    run_latest_decision_narrative_conflict,
    save_narrative_decision_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Freakto v7.1 Narrative/Decision Conflict Scoring dashboard")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="4h")
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()

    report = run_latest_decision_narrative_conflict(symbol=args.symbol, timeframe=args.timeframe)
    print(format_narrative_decision_console(report, compact=args.compact))
    if not args.no_save:
        json_path, md_path, obs = save_narrative_decision_report(report)
        print(f"🧭 Narrative/decision JSON ذخیره شد: {json_path}")
        print(f"📝 Narrative/decision report ذخیره شد: {md_path}")
        print(f"🧾 Narrative/decision observations ledger ذخیره شد: {obs}")


if __name__ == "__main__":
    main()
