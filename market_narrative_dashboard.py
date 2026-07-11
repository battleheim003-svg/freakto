"""Freakto v7.0.0 - Market Narrative dashboard."""
import argparse
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from config import SYMBOL, TIMEFRAME
from engine.market_narrative import (
    VERSION,
    format_market_narrative_console,
    run_market_narrative,
    save_market_narrative_report,
)
from telegram_notifier import send_telegram_message


def build_parser():
    p = argparse.ArgumentParser(description=f"Freakto Market Narrative Engine {VERSION}")
    p.add_argument("--symbol", default=SYMBOL)
    p.add_argument("--timeframe", default=TIMEFRAME)
    p.add_argument("--hours", type=int, default=168)
    p.add_argument("--compact", action="store_true")
    p.add_argument("--no-save", action="store_true")
    p.add_argument("--send", action="store_true")
    return p


def main():
    args = build_parser().parse_args()
    report = run_market_narrative(symbol=args.symbol, timeframe=args.timeframe, lookback_hours=args.hours)
    text = format_market_narrative_console(report, compact=args.compact)
    print(text)
    if not args.no_save:
        json_path, md_path, drivers_csv, obs_csv = save_market_narrative_report(report)
        print(f"🧭 Market narrative JSON ذخیره شد: {json_path}")
        print(f"📝 Market narrative report ذخیره شد: {md_path}")
        print(f"📊 Market narrative drivers CSV ذخیره شد: {drivers_csv}")
        print(f"🧾 Market narrative observations ledger ذخیره شد: {obs_csv}")
    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
