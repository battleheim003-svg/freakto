
"""Freakto v6.5.0 - causal event ledger helper: manual + automatic."""
import argparse
from pathlib import Path
import shutil

from engine.causal_intelligence import VERSION, CAUSAL_EVENTS_FILE, CAUSAL_EVENTS_EXAMPLE, CAUSAL_AUTO_EVENTS_FILE, _ensure_manual_events_example
from engine.auto_event_collector import AUTO_EVENT_SOURCES_EXAMPLE, ensure_sources_example


def _show_file(path: Path, label: str, limit: int = 10):
    print("-" * 110)
    print(f"{label}: {path}")
    if not path.exists():
        print("فایل هنوز ساخته نشده است.")
        return
    try:
        for i, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines()[:limit], start=1):
            print(f"{i}: {line}")
    except Exception as error:
        print(f"⚠️ خواندن فایل شکست خورد: {type(error).__name__}: {error}")


def main():
    p = argparse.ArgumentParser(description=f"Freakto Causal Event Ledgers {VERSION}")
    p.add_argument("--init", action="store_true", help="Create data/manual_events.csv from the example if missing.")
    p.add_argument("--show", action="store_true", help="Show manual and automatic event ledgers.")
    p.add_argument("--show-auto", action="store_true", help="Only show auto_events.csv and auto source example.")
    args = p.parse_args()
    _ensure_manual_events_example(); ensure_sources_example()
    if args.init:
        CAUSAL_EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not CAUSAL_EVENTS_FILE.exists():
            shutil.copyfile(CAUSAL_EVENTS_EXAMPLE, CAUSAL_EVENTS_FILE)
            print(f"✅ manual_events.csv ساخته شد: {CAUSAL_EVENTS_FILE}")
        else:
            print(f"ℹ️ manual_events.csv از قبل وجود دارد: {CAUSAL_EVENTS_FILE}")
    print("=" * 110)
    print(f"Freakto Causal Event Ledgers {VERSION}")
    print("=" * 110)
    if not args.show_auto:
        print("Manual columns: timestamp_utc,symbol,event_type,source_name,source_url,impact,direction,confidence,description")
        print("Tip: manual_events فقط برای رویدادهای بزرگ/curated است؛ collector خودکار را برای خبرهای روزانه استفاده کن.")
        _show_file(CAUSAL_EVENTS_FILE if CAUSAL_EVENTS_FILE.exists() else CAUSAL_EVENTS_EXAMPLE, "Manual event ledger/example")
    print("Auto columns: event_id,timestamp_utc,symbol,event_type,source_id,source_name,source_tier,...")
    print("Tip: auto_events.csv را automatic_event_collector_dashboard.py می‌سازد؛ دستی ویرایش نکن مگر برای تعمیر اضطراری.")
    _show_file(CAUSAL_AUTO_EVENTS_FILE, "Automatic event ledger")
    _show_file(AUTO_EVENT_SOURCES_EXAMPLE, "Automatic source registry example", limit=6)
    print("=" * 110)


if __name__ == "__main__":
    main()
