"""Append-only forward ledger for research rankings and later outcomes."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA = """
CREATE TABLE IF NOT EXISTS ranking_observations (
    observation_id TEXT PRIMARY KEY,
    period_utc TEXT NOT NULL,
    symbol TEXT NOT NULL,
    asset_class TEXT NOT NULL,
    research_selection INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    recorded_utc TEXT NOT NULL,
    UNIQUE(period_utc, symbol)
);

CREATE TABLE IF NOT EXISTS realized_outcomes (
    outcome_id TEXT PRIMARY KEY,
    period_utc TEXT NOT NULL,
    symbol TEXT NOT NULL,
    outcome_observed_utc TEXT NOT NULL,
    realized_gross_return_bps REAL NOT NULL,
    realized_cost_bps REAL NOT NULL,
    source_ref TEXT NOT NULL,
    recorded_utc TEXT NOT NULL,
    UNIQUE(period_utc, symbol, outcome_observed_utc)
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _id(*values: Any) -> str:
    return hashlib.sha256("|".join(map(str, values)).encode("utf-8")).hexdigest()[:24]


def _utc(value: Any) -> str:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat()


class CrossAssetForwardTracker:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def record_rankings(self, rows: Iterable[dict[str, Any]]) -> int:
        inserted = 0
        with self.connect() as connection:
            for row in rows:
                period = _utc(row["period_utc"])
                symbol = str(row["symbol"]).upper()
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO ranking_observations
                    (observation_id, period_utc, symbol, asset_class,
                     research_selection, payload_json, recorded_utc)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        _id(period, symbol),
                        period,
                        symbol,
                        str(row["asset_class"]).lower(),
                        int(bool(row.get("research_selection"))),
                        json.dumps(row, ensure_ascii=False, sort_keys=True),
                        _now(),
                    ),
                )
                inserted += int(cursor.rowcount == 1)
        return inserted

    def record_outcome(
        self,
        *,
        period_utc: Any,
        symbol: str,
        outcome_observed_utc: Any,
        realized_gross_return_bps: float,
        realized_cost_bps: float,
        source_ref: str,
    ) -> bool:
        period = _utc(period_utc)
        observed = _utc(outcome_observed_utc)
        if observed <= period:
            raise ValueError("Forward outcome must be observed after its ranking period.")
        if float(realized_cost_bps) < 0:
            raise ValueError("Realized cost cannot be negative.")
        if not str(source_ref).strip():
            raise ValueError("Forward outcome requires source_ref.")
        canonical_symbol = str(symbol).upper()
        with self.connect() as connection:
            exists = connection.execute(
                "SELECT 1 FROM ranking_observations WHERE period_utc=? AND symbol=?",
                (period, canonical_symbol),
            ).fetchone()
            if exists is None:
                raise ValueError("Cannot record an outcome without a prior ranking observation.")
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO realized_outcomes
                (outcome_id, period_utc, symbol, outcome_observed_utc,
                 realized_gross_return_bps, realized_cost_bps, source_ref, recorded_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _id(period, canonical_symbol, observed),
                    period,
                    canonical_symbol,
                    observed,
                    float(realized_gross_return_bps),
                    float(realized_cost_bps),
                    str(source_ref),
                    _now(),
                ),
            )
            return cursor.rowcount == 1
