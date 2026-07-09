"""Repair/migrate logs/decisions.csv to the current Freakto header.

Useful after upgrading from older releases whose decision log had fewer columns.
This script preserves common fields and rewrites the CSV with the v6.4.0-safe
header so pandas-based tools can read it again.
"""

from __future__ import annotations

import csv
from pathlib import Path

from engine.csv_utils import read_csv_dicts_lenient, rewrite_csv_with_header

LOG_FILE = Path("logs/decisions.csv")

CURRENT_HEADER = [
    "decision_id",
    "logged_at_utc",
    "candle_timestamp",
    "symbol",
    "timeframe",
    "price",
    "side",
    "score",
    "confidence_label",
    "risk_label",
    "actionability",
    "is_actionable",
    "entry_zone",
    "stop_zone",
    "targets",
    "trend_score",
    "trend_max",
    "momentum_score",
    "momentum_max",
    "volume_score",
    "volume_max",
    "structure_score",
    "structure_max",
    "risk_penalty",
    "risk_max",
    "regime_label",
    "regime_confidence",
    "regime_adjustment",
    "regime_source",
    "regime_label_quality",
    "trend_state",
    "volatility_state",
    "market_phase",
    "primary_cause",
    "cause_confidence",
    "catalyst_score",
    "event_risk",
    "technical_event_conflict",
    "causal_alignment",
    "causal_verdict",
    "causal_source_count",
    "causal_trusted_source_count",
    "causal_manual_event_count",
    "causal_top_sources",
    "causal_notes",
    "long_score",
    "short_score",
    "reasons",
    "warnings",
    "provider",
]


def main() -> None:
    print("=" * 110)
    print("🛠️ Freakto Decision Log Repair v6.4.0")
    print("=" * 110)

    if not LOG_FILE.exists():
        print(f"No decisions log found: {LOG_FILE}")
        return

    old_header, rows = read_csv_dicts_lenient(LOG_FILE)
    print(f"File       : {LOG_FILE}")
    print(f"Rows       : {len(rows)}")
    print(f"Old columns: {len(old_header)}")

    merged_header = list(CURRENT_HEADER)
    for name in old_header:
        if name and name not in merged_header:
            merged_header.append(name)

    backup = LOG_FILE.with_suffix(".csv.bak_v512")
    backup.write_bytes(LOG_FILE.read_bytes())
    rewrite_csv_with_header(LOG_FILE, merged_header, rows)

    print(f"Backup     : {backup}")
    print(f"New columns: {len(merged_header)}")
    print("OK: decisions.csv repaired/migrated with v6.4.0 regime + causal metadata columns.")
    print("=" * 110)


if __name__ == "__main__":
    main()
