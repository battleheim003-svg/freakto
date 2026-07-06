"""
history_db.py

SQLite storage برای ذخیره Snapshot هر تصمیم Freakto.
برای هر symbol + timeframe + candle_timestamp فقط یک Snapshot نگه داشته می‌شود.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone


DB_DIR = Path("history")
DB_FILE = DB_DIR / "freakto_history.db"


def _connect():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_FILE)


def init_history_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at_utc TEXT NOT NULL,
                candle_timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                provider TEXT,

                price REAL,
                side TEXT,
                score INTEGER,
                confidence_value INTEGER,
                confidence_label TEXT,
                risk_label TEXT,
                actionability TEXT,
                is_actionable INTEGER,

                trend_score INTEGER,
                momentum_score INTEGER,
                volume_score INTEGER,
                structure_score INTEGER,
                regime_score INTEGER,
                risk_penalty INTEGER,

                regime_label TEXT,
                regime_confidence INTEGER,
                regime_adjustment INTEGER,

                reasons TEXT,
                warnings TEXT,
                raw_json TEXT
            )
        """)

        conn.execute("""
            DELETE FROM snapshots
            WHERE id NOT IN (
                SELECT MAX(id)
                FROM snapshots
                GROUP BY symbol, timeframe, candle_timestamp
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_symbol_tf
            ON snapshots(symbol, timeframe)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp
            ON snapshots(candle_timestamp)
        """)

        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_snapshots_unique_candle
            ON snapshots(symbol, timeframe, candle_timestamp)
        """)


def _component_score(opportunity, name):
    for component in opportunity.components:
        if component.name == name:
            return component.points
    return 0


def _collect_reasons(opportunity):
    items = []
    for component in opportunity.components:
        items.extend(component.reasons)
    return items


def _collect_warnings(opportunity):
    items = []
    for component in opportunity.components:
        items.extend(component.warnings)
    return items


def _snapshot_exists(symbol, timeframe, candle_timestamp):
    with _connect() as conn:
        result = conn.execute(
            """
            SELECT id
            FROM snapshots
            WHERE symbol = ?
              AND timeframe = ?
              AND candle_timestamp = ?
            LIMIT 1
            """,
            (symbol, timeframe, str(candle_timestamp)),
        ).fetchone()

    return result is not None


def save_snapshot(opportunity, latest_timestamp, price, provider=None):
    init_history_db()

    if _snapshot_exists(
        symbol=opportunity.symbol,
        timeframe=opportunity.timeframe,
        candle_timestamp=latest_timestamp,
    ):
        print(
            "🧠 Snapshot تکراری بود و ذخیره نشد: "
            f"{opportunity.symbol} | {opportunity.timeframe} | {latest_timestamp}"
        )
        return False

    confidence = opportunity.confidence

    row = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "candle_timestamp": str(latest_timestamp),
        "symbol": opportunity.symbol,
        "timeframe": opportunity.timeframe,
        "provider": provider or "",

        "price": float(price),
        "side": opportunity.side,
        "score": int(opportunity.score),
        "confidence_value": int(confidence.value),
        "confidence_label": confidence.label,
        "risk_label": opportunity.risk_label,
        "actionability": opportunity.actionability_label,
        "is_actionable": 1 if opportunity.is_actionable else 0,

        "trend_score": _component_score(opportunity, "Trend"),
        "momentum_score": _component_score(opportunity, "Momentum"),
        "volume_score": _component_score(opportunity, "Volume"),
        "structure_score": _component_score(opportunity, "Structure"),
        "regime_score": _component_score(opportunity, "Regime Adjustment"),
        "risk_penalty": _component_score(opportunity, "Risk Penalty"),

        "regime_label": opportunity.raw.get("regime_label", ""),
        "regime_confidence": int(opportunity.raw.get("regime_confidence", 0) or 0),
        "regime_adjustment": int(opportunity.raw.get("regime_adjustment", 0) or 0),

        "reasons": json.dumps(_collect_reasons(opportunity), ensure_ascii=False),
        "warnings": json.dumps(_collect_warnings(opportunity), ensure_ascii=False),
        "raw_json": json.dumps(opportunity.raw, ensure_ascii=False),
    }

    columns = ", ".join(row.keys())
    placeholders = ", ".join(["?"] * len(row))

    with _connect() as conn:
        conn.execute(
            f"INSERT INTO snapshots ({columns}) VALUES ({placeholders})",
            list(row.values()),
        )

    print(f"🧠 Snapshot ذخیره شد: {DB_FILE}")
    return True