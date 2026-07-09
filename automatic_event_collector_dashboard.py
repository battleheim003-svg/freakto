
"""Freakto v7.0.0 - Automatic Event Collector dashboard."""
import argparse

from engine.auto_event_collector import (
    VERSION,
    AUTO_EVENTS_FILE,
    build_event_source_registry,
    ensure_sources_example,
    format_auto_event_console,
    run_auto_event_collector,
    save_auto_event_report,
)
from telegram_notifier import send_telegram_message


def build_parser():
    p = argparse.ArgumentParser(description=f"Freakto Automatic Event Collector {VERSION}")
    p.add_argument("--compact", action="store_true")
    p.add_argument("--no-save", action="store_true")
    p.add_argument("--send", action="store_true")
    p.add_argument("--no-fetch", action="store_true", help="Do not call external sources; summarize current auto_events.csv only.")
    p.add_argument("--no-apply", action="store_true", help="Fetch and classify, but do not write data/auto_events.csv.")
    p.add_argument("--include-media", action="store_true", help="Include selected reputable media feeds; official sources stay prioritized.")
    p.add_argument("--hours", type=int, default=168)
    p.add_argument("--max-items", type=int, default=25)
    p.add_argument("--sources", action="store_true", help="Print source registry and exit.")
    return p


def main():
    args = build_parser().parse_args()
    ensure_sources_example()
    if args.sources:
        print("=" * 110)
        print(f"Freakto Automatic Event Source Registry {VERSION}")
        print("=" * 110)
        for s in build_event_source_registry(include_media=args.include_media):
            print(f"- {s.source_id} | {s.reliability_tier} | {s.source_type} | {s.category} | {s.url}")
            print(f"  {s.notes}")
        print(f"\nAuto event ledger: {AUTO_EVENTS_FILE}")
        print("=" * 110)
        return
    report = run_auto_event_collector(
        fetch_live=not args.no_fetch,
        apply_changes=not args.no_apply,
        lookback_hours=args.hours,
        max_items_per_source=args.max_items,
        include_media=args.include_media,
    )
    text = format_auto_event_console(report, compact=args.compact)
    print(text)
    if not args.no_save:
        json_path, md_path, health_csv = save_auto_event_report(report)
        print(f"🗞️ Auto event JSON ذخیره شد: {json_path}")
        print(f"📝 Auto event report ذخیره شد: {md_path}")
        print(f"📊 Auto event source health CSV ذخیره شد: {health_csv}")
        print(f"🧾 Auto event ledger: {AUTO_EVENTS_FILE}")
    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
