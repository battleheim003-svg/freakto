"""Fail-closed import of legacy decision CSVs into Ledger v2."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .ledger import DecisionLedger, EvidenceContractError, sha256_json


def migrate_decisions_csv(path: Path, root: Path | None = None) -> dict[str, int | str]:
    ledger = DecisionLedger(root)
    imported = duplicate = quarantined = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"decision_id", "candle_timestamp", "symbol", "timeframe", "side", "price", "targets"}
        header = set(reader.fieldnames or [])
        missing = sorted(required - header)
        if missing:
            raise EvidenceContractError(f"legacy header incompatible: missing {', '.join(missing)}")
        for number, row in enumerate(reader, start=2):
            try:
                targets_text = str(row.get("targets") or "[]")
                import json
                targets = json.loads(targets_text)
                if not isinstance(targets, list):
                    raise ValueError("targets is not a list")
                # This explicitly detects the reported shifted confidence labels.
                if any(str(value).strip().lower() in {"low", "medium", "high"} for value in targets):
                    raise ValueError("schema drift: confidence label found in targets")
                record: dict[str, Any] = {
                    "decision_id": row["decision_id"], "created_utc": row.get("logged_at_utc"),
                    "candle_timestamp_utc": row["candle_timestamp"], "symbol": row["symbol"],
                    "timeframe": row["timeframe"], "side": row["side"], "entry_price": row["price"],
                    "stop_price": row.get("stop_zone"), "targets": targets, "features": row,
                    "source_sha256": sha256_json(row), "code_sha256": "LEGACY_IMPORT",
                }
                if ledger.append(record):
                    imported += 1
                else:
                    duplicate += 1
            except (ValueError, TypeError, EvidenceContractError) as exc:
                ledger.quarantine(str(path), number, str(exc), row)
                quarantined += 1
    return {"source": str(path), "imported": imported, "duplicates": duplicate, "quarantined": quarantined}
