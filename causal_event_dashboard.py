"""Freakto v6.4.0 - Manual causal event ledger helper."""
import argparse
from pathlib import Path
import shutil

from engine.causal_intelligence import VERSION, CAUSAL_EVENTS_FILE, CAUSAL_EVENTS_EXAMPLE, _ensure_manual_events_example


def main():
    p = argparse.ArgumentParser(description=f"Freakto Manual Causal Event Ledger {VERSION}")
    p.add_argument("--init", action="store_true", help="Create data/manual_events.csv from the example if missing.")
    p.add_argument("--show", action="store_true", help="Show the current manual event file path and first lines.")
    args = p.parse_args()
    _ensure_manual_events_example()
    if args.init:
        CAUSAL_EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not CAUSAL_EVENTS_FILE.exists():
            shutil.copyfile(CAUSAL_EVENTS_EXAMPLE, CAUSAL_EVENTS_FILE)
            print(f"✅ manual_events.csv ساخته شد: {CAUSAL_EVENTS_FILE}")
        else:
            print(f"ℹ️ manual_events.csv از قبل وجود دارد: {CAUSAL_EVENTS_FILE}")
    if args.show or not args.init:
        path = CAUSAL_EVENTS_FILE if CAUSAL_EVENTS_FILE.exists() else CAUSAL_EVENTS_EXAMPLE
        print("=" * 110)
        print(f"Freakto Manual Causal Event Ledger {VERSION}")
        print("=" * 110)
        print(f"Active file: {path}")
        print("Columns: timestamp_utc,symbol,event_type,source_name,source_url,impact,direction,confidence,description")
        print("Tip: فقط رویدادهای معتبر مثل Fed/SEC/Reuters/official project/issuer announcements را وارد کن.")
        print("-" * 110)
        try:
            for i, line in enumerate(path.read_text(encoding="utf-8").splitlines()[:8], start=1):
                print(f"{i}: {line}")
        except Exception as error:
            print(f"⚠️ خواندن فایل شکست خورد: {type(error).__name__}: {error}")
        print("=" * 110)


if __name__ == "__main__":
    main()
