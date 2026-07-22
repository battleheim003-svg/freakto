"""SQLite signal history store.

This module keeps a compact, query-friendly ledger of generated market signals.
It complements ``history_db.py``: snapshots preserve rich engine state, while
this table makes signal/risk-plan analysis easy across monitor and portfolio
scans.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.risk_reward import calculate_risk_reward


DB_DIR = Path("history")
DB_FILE = DB_DIR / "freakto_signals.db"


def _connect() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_FILE)


def init_signal_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at_utc TEXT NOT NULL,
                source TEXT NOT NULL,
                run_id TEXT,
                candle_timestamp TEXT,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                provider TEXT,
                price REAL,
                side TEXT,
                score INTEGER,
                confidence INTEGER,
                confidence_label TEXT,
                risk_label TEXT,
                actionability TEXT,
                recommendation TEXT,
                entry REAL,
                stop_loss REAL,
                stop_distance_pct REAL,
                take_profit_1 REAL,
                take_profit_2 REAL,
                take_profit_3 REAL,
                rr_1 REAL,
                rr_2 REAL,
                rr_3 REAL,
                raw_json TEXT,
                UNIQUE(source, symbol, timeframe, candle_timestamp, side, score)
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_signals_symbol_time
            ON signals(symbol, timeframe, candle_timestamp)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_signals_actionability
            ON signals(actionability, recommendation)
            """
        )


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        text = str(value).replace("`", "").replace(",", "").strip()
        if not text or text.lower() in {"nan", "none", "null"} or text in {"---", "-"}:
            return None
        return float(text)
    except Exception:
        return None


def _zone_midpoint(value: Any) -> float | None:
    text = str(value or "").replace("`", "").strip()
    if not text:
        return None
    values = [_safe_float(part) for part in text.split("-")]
    values = [value for value in values if value is not None]
    return sum(values) / len(values) if values else None


def _as_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {str(k): _as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_as_jsonable(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _insert_signal(row: dict[str, Any]) -> None:
    init_signal_db()
    fieldnames = list(row.keys())
    columns = ", ".join(fieldnames)
    placeholders = ", ".join(["?"] * len(fieldnames))
    updates = ", ".join([f"{name}=excluded.{name}" for name in fieldnames if name != "id"])
    with _connect() as conn:
        conn.execute(
            f"""
            INSERT INTO signals ({columns})
            VALUES ({placeholders})
            ON CONFLICT(source, symbol, timeframe, candle_timestamp, side, score)
            DO UPDATE SET {updates}
            """,
            [row[name] for name in fieldnames],
        )


def save_opportunity_signal(
    opportunity,
    *,
    price: float | None,
    candle_timestamp: Any,
    provider: str = "",
    source: str = "monitor",
    run_id: str = "",
) -> bool:
    rr = calculate_risk_reward(opportunity)
    targets = list(rr.targets or [])
    confidence = getattr(getattr(opportunity, "confidence", None), "value", None)
    row = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "run_id": run_id,
        "candle_timestamp": str(candle_timestamp or ""),
        "symbol": str(getattr(opportunity, "symbol", "")),
        "timeframe": str(getattr(opportunity, "timeframe", "")),
        "provider": provider or "",
        "price": _safe_float(price),
        "side": str(getattr(opportunity, "side", "")),
        "score": int(getattr(opportunity, "score", 0) or 0),
        "confidence": int(confidence or 0),
        "confidence_label": str(getattr(opportunity, "confidence_label", "")),
        "risk_label": str(getattr(opportunity, "risk_label", "")),
        "actionability": str(getattr(opportunity, "actionability_label", "")),
        "recommendation": "",
        "entry": rr.entry,
        "stop_loss": rr.stop,
        "stop_distance_pct": rr.stop_distance_pct,
        "take_profit_1": targets[0].price if len(targets) > 0 else None,
        "take_profit_2": targets[1].price if len(targets) > 1 else None,
        "take_profit_3": targets[2].price if len(targets) > 2 else None,
        "rr_1": targets[0].rr if len(targets) > 0 else None,
        "rr_2": targets[1].rr if len(targets) > 1 else None,
        "rr_3": targets[2].rr if len(targets) > 2 else None,
        "raw_json": json.dumps(_as_jsonable(getattr(opportunity, "raw", {})), ensure_ascii=False, default=str),
    }
    _insert_signal(row)
    return True


def save_portfolio_item_signal(item, *, source: str = "portfolio_scanner", run_id: str = "") -> bool:
    targets = list(getattr(item, "targets", []) or [])
    entry = _zone_midpoint(getattr(item, "entry_zone", ""))
    stop = _safe_float(getattr(item, "stop_zone", ""))
    risk_abs = abs(entry - stop) if entry is not None and stop is not None else None
    target_values = [_safe_float(value) for value in targets[:3]]
    target_values += [None] * (3 - len(target_values))
    side = str(getattr(item, "side", ""))

    def rr_for(target: float | None) -> float | None:
        if target is None or entry is None or risk_abs is None or risk_abs <= 0:
            return None
        reward = target - entry if side == "LONG" else entry - target
        return round(max(0.0, reward / risk_abs), 2)

    row = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "run_id": run_id,
        "candle_timestamp": str(getattr(item, "decision_timestamp", "") or ""),
        "symbol": str(getattr(item, "symbol", "")),
        "timeframe": str(getattr(item, "timeframe", "")),
        "provider": str(getattr(item, "provider", "") or ""),
        "price": _safe_float(getattr(item, "price", None)),
        "side": side,
        "score": int(getattr(item, "score", 0) or 0),
        "confidence": int(getattr(item, "confidence", 0) or 0),
        "confidence_label": str(getattr(item, "confidence_label", "") or ""),
        "risk_label": str(getattr(item, "risk_label", "") or ""),
        "actionability": str(getattr(item, "actionability", "") or ""),
        "recommendation": str(getattr(item, "recommendation", "") or ""),
        "entry": entry,
        "stop_loss": stop,
        "stop_distance_pct": round(abs(entry - stop) / entry * 100, 4) if entry and stop else None,
        "take_profit_1": target_values[0],
        "take_profit_2": target_values[1],
        "take_profit_3": target_values[2],
        "rr_1": rr_for(target_values[0]),
        "rr_2": rr_for(target_values[1]),
        "rr_3": rr_for(target_values[2]),
        "raw_json": json.dumps(_as_jsonable(item), ensure_ascii=False, default=str),
    }
    _insert_signal(row)
    return True
