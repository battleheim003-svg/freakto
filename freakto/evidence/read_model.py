"""Derived integrity/readiness view. Never treats legacy CSV reports as evidence."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .ledger import canonical_cohort, default_ledger_root, import_quarantine


INVALIDATED_LEGACY_STATUS = "INVALIDATED_DATA_CONTRACT"


def evidence_summary(root: Path | None = None) -> dict[str, Any]:
    cohort = canonical_cohort(root)
    quarantine = import_quarantine(root)
    returns = [float(row["net_return_pct"]) for row in cohort]
    wins = [value for value in returns if value > 0]
    losses = [value for value in returns if value < 0]
    gross_loss = abs(sum(losses))
    symbols = sorted({str(row["symbol"]) for row in cohort})
    ledger = default_ledger_root(root) / "evidence.sqlite3"
    digest = hashlib.sha256(ledger.read_bytes()).hexdigest() if ledger.exists() else None
    blockers = ["LEGACY_FORWARD_EDGE_INVALIDATED", "CLEAN_FORWARD_BASELINE_REQUIRED"]
    if not cohort:
        blockers.append("NO_V2_TERMINAL_DIRECTIONAL_OUTCOMES")
    if quarantine:
        blockers.append("QUARANTINED_LEGACY_ROWS_PRESENT")
    return {
        "status": INVALIDATED_LEGACY_STATUS if not cohort else "V2_EVIDENCE_COLLECTING",
        "metric_version": "evidence-v2-net-of-cost",
        "legacy_edge_status": INVALIDATED_LEGACY_STATUS,
        "directional_terminal_count": len(cohort), "schema_valid_unique_count": len(cohort),
        "net_expectancy_pct": round(sum(returns) / len(returns), 8) if returns else None,
        "profit_factor": round(sum(wins) / gross_loss, 8) if gross_loss else None,
        "costs_applied": bool(cohort), "quarantined_rows": len(quarantine),
        "symbols_with_outcomes": symbols, "ledger_sha256": digest, "blockers": blockers,
    }


def coverage_funnel(symbols: list[str], root: Path | None = None) -> list[dict[str, Any]]:
    cohort = canonical_cohort(root)
    result = []
    for symbol in symbols:
        rows = [row for row in cohort if row["symbol"] == symbol]
        result.append({"symbol": symbol, "directional_evaluated": len(rows), "paper": 0, "blocker": "NO_DIRECTIONAL_V2_OUTCOME" if not rows else "PAPER_COLLECTION_PENDING"})
    return result
