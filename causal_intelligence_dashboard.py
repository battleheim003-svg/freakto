"""Freakto v6.5.0 - Causal/Event Intelligence dashboard."""
import argparse

from config import SYMBOL, TIMEFRAME
from engine.causal_intelligence import (
    VERSION,
    format_causal_console,
    run_causal_intelligence,
    save_causal_report,
    build_source_registry,
)
from telegram_notifier import send_telegram_message


def build_parser():
    p = argparse.ArgumentParser(description=f"Freakto Causal/Event Intelligence {VERSION}")
    p.add_argument("--symbol", default=SYMBOL)
    p.add_argument("--timeframe", default=TIMEFRAME)
    p.add_argument("--compact", action="store_true")
    p.add_argument("--no-save", action="store_true")
    p.add_argument("--send", action="store_true")
    p.add_argument("--no-live", action="store_true", help="Do not call external APIs; use internal/latest decision/manual context only.")
    p.add_argument("--no-sentiment", action="store_true", help="Skip lower-tier sentiment source.")
    p.add_argument("--sources", action="store_true", help="Print the trusted source registry and exit.")
    return p


def main():
    args = build_parser().parse_args()
    if args.sources:
        print("=" * 110)
        print(f"Freakto Causal Source Registry {VERSION}")
        print("=" * 110)
        for src in build_source_registry():
            print(f"- {src['source_id']} | {src['reliability_tier']} | key={src['requires_key']} | {src['purpose']}")
        print("=" * 110)
        return
    report = run_causal_intelligence(
        symbol=args.symbol,
        timeframe=args.timeframe,
        collect_live=not args.no_live,
        include_sentiment=not args.no_sentiment,
    )
    text = format_causal_console(report, compact=args.compact)
    print(text)
    if not args.no_save:
        json_path, md_path, source_csv, obs_csv = save_causal_report(report)
        print(f"🧠 Causal intelligence JSON ذخیره شد: {json_path}")
        print(f"📝 Causal intelligence report ذخیره شد: {md_path}")
        print(f"📊 Causal source health CSV ذخیره شد: {source_csv}")
        print(f"🧾 Causal observations ledger ذخیره شد: {obs_csv}")
    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
