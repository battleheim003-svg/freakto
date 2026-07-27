"""SQLite-backed Decision/Outcome Ledger v2.

The database is the source of truth; CSV/JSON reports are derived only.  Each
write is transactional, schema-versioned, and idempotent by decision id.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

DECISION_SCHEMA_VERSION = 2
OUTCOME_SCHEMA_VERSION = 2
VALID_SIDES = {"LONG", "SHORT", "NEUTRAL"}
TERMINAL_STATUSES = {"TARGET", "STOP", "EXPIRED"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_ledger_root(root: Path | None = None) -> Path:
    base = Path(root or ".")
    return base / ".freakto-runtime" / "evidence-v2"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class EvidenceContractError(ValueError):
    """Raised when an evidence row violates the v2 data contract."""


class _Ledger:
    table_name: str
    schema_version: int

    def __init__(self, root: Path | None = None):
        self.root = default_ledger_root(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "evidence.sqlite3"
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS quarantine (
                    quarantine_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    row_number INTEGER,
                    reason TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    created_utc TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS evidence_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_utc TEXT NOT NULL
                );
                """
            )

    def set_meta(self, key: str, value: Any) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT INTO evidence_meta(key,value,updated_utc) VALUES(?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_utc=excluded.updated_utc",
                (key, canonical_json(value), utc_now()),
            )

    def quarantine(self, source: str, row_number: int | None, reason: str, payload: Any) -> None:
        text = canonical_json(payload)
        with self._connect() as db:
            db.execute(
                "INSERT INTO quarantine(source,row_number,reason,payload_json,payload_sha256,created_utc) VALUES(?,?,?,?,?,?)",
                (source, row_number, reason, text, hashlib.sha256(text.encode("utf-8")).hexdigest(), utc_now()),
            )

    def rows(self) -> list[dict[str, Any]]:
        with self._connect() as db:
            return [dict(row) for row in db.execute(f"SELECT * FROM {self.table_name} ORDER BY created_utc, decision_id")]


class DecisionLedger(_Ledger):
    table_name = "decisions_v2"
    schema_version = DECISION_SCHEMA_VERSION

    def _initialize(self) -> None:
        super()._initialize()
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS decisions_v2 (
                    decision_id TEXT PRIMARY KEY,
                    schema_version INTEGER NOT NULL,
                    created_utc TEXT NOT NULL,
                    candle_timestamp_utc TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    side TEXT NOT NULL CHECK(side IN ('LONG','SHORT','NEUTRAL')),
                    entry_price REAL NOT NULL CHECK(entry_price > 0),
                    stop_price REAL,
                    targets_json TEXT NOT NULL,
                    feature_snapshot_sha256 TEXT NOT NULL,
                    source_sha256 TEXT NOT NULL,
                    code_sha256 TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                """
            )

    def append(self, record: dict[str, Any]) -> bool:
        required = ("decision_id", "candle_timestamp_utc", "symbol", "timeframe", "side", "entry_price")
        missing = [key for key in required if not record.get(key)]
        if missing:
            raise EvidenceContractError(f"decision missing required fields: {', '.join(missing)}")
        side = str(record["side"]).upper()
        if side not in VALID_SIDES:
            raise EvidenceContractError(f"unsupported decision side: {side}")
        try:
            entry_price = float(record["entry_price"])
        except (TypeError, ValueError) as exc:
            raise EvidenceContractError("entry_price must be numeric") from exc
        if entry_price <= 0:
            raise EvidenceContractError("entry_price must be positive")
        targets = record.get("targets", [])
        if not isinstance(targets, list):
            raise EvidenceContractError("targets must be a list")
        payload = dict(record)
        payload["side"] = side
        payload["entry_price"] = entry_price
        payload["schema_version"] = self.schema_version
        source_hash = str(payload.get("source_sha256") or sha256_json(payload))
        feature_hash = str(payload.get("feature_snapshot_sha256") or sha256_json(payload.get("features", {})))
        code_hash = str(payload.get("code_sha256") or "UNKNOWN")
        values = (
            str(payload["decision_id"]), self.schema_version, str(payload.get("created_utc") or utc_now()),
            str(payload["candle_timestamp_utc"]), str(payload["symbol"]), str(payload["timeframe"]), side,
            entry_price, payload.get("stop_price"), canonical_json(targets), feature_hash, source_hash, code_hash,
            canonical_json(payload),
        )
        with self._connect() as db:
            result = db.execute(
                "INSERT OR IGNORE INTO decisions_v2 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values
            )
        return bool(result.rowcount)


class OutcomeLedger(_Ledger):
    table_name = "outcomes_v2"
    schema_version = OUTCOME_SCHEMA_VERSION

    def _initialize(self) -> None:
        super()._initialize()
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS outcomes_v2 (
                    decision_id TEXT PRIMARY KEY REFERENCES decisions_v2(decision_id),
                    schema_version INTEGER NOT NULL,
                    created_utc TEXT NOT NULL,
                    evaluator_version TEXT NOT NULL,
                    terminal_status TEXT NOT NULL CHECK(terminal_status IN ('TARGET','STOP','EXPIRED')),
                    terminal_candle_timestamp_utc TEXT NOT NULL,
                    terminal_offset INTEGER NOT NULL CHECK(terminal_offset > 0),
                    entry_price REAL NOT NULL,
                    exit_price REAL NOT NULL,
                    gross_return_pct REAL NOT NULL,
                    cost_pct REAL NOT NULL CHECK(cost_pct >= 0),
                    net_return_pct REAL NOT NULL,
                    intrabar_ambiguity INTEGER NOT NULL DEFAULT 0,
                    payload_json TEXT NOT NULL
                );
                """
            )

    def upsert(self, record: dict[str, Any]) -> None:
        required = ("decision_id", "evaluator_version", "terminal_status", "terminal_candle_timestamp_utc", "terminal_offset", "entry_price", "exit_price", "gross_return_pct", "cost_pct", "net_return_pct")
        missing = [key for key in required if record.get(key) is None or record.get(key) == ""]
        if missing:
            raise EvidenceContractError(f"outcome missing required fields: {', '.join(missing)}")
        status = str(record["terminal_status"]).upper()
        if status not in TERMINAL_STATUSES:
            raise EvidenceContractError(f"outcome not terminal: {status}")
        payload = dict(record)
        payload["terminal_status"] = status
        payload["schema_version"] = self.schema_version
        values = (
            str(payload["decision_id"]), self.schema_version, str(payload.get("created_utc") or utc_now()),
            str(payload["evaluator_version"]), status, str(payload["terminal_candle_timestamp_utc"]),
            int(payload["terminal_offset"]), float(payload["entry_price"]), float(payload["exit_price"]),
            float(payload["gross_return_pct"]), float(payload["cost_pct"]), float(payload["net_return_pct"]),
            int(bool(payload.get("intrabar_ambiguity", False))), canonical_json(payload),
        )
        with self._connect() as db:
            db.execute(
                "INSERT INTO outcomes_v2 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(decision_id) DO UPDATE SET schema_version=excluded.schema_version, created_utc=excluded.created_utc, evaluator_version=excluded.evaluator_version, terminal_status=excluded.terminal_status, terminal_candle_timestamp_utc=excluded.terminal_candle_timestamp_utc, terminal_offset=excluded.terminal_offset, entry_price=excluded.entry_price, exit_price=excluded.exit_price, gross_return_pct=excluded.gross_return_pct, cost_pct=excluded.cost_pct, net_return_pct=excluded.net_return_pct, intrabar_ambiguity=excluded.intrabar_ambiguity, payload_json=excluded.payload_json",
                values,
            )


def canonical_cohort(root: Path | None = None) -> list[dict[str, Any]]:
    """Only schema-valid, unique, directional, terminal, after-cost outcomes."""
    # Initialize both tables before querying. A Decision-only migration is a
    # valid intermediate state and must report an empty cohort, never crash.
    DecisionLedger(root)
    OutcomeLedger(root)
    root_path = default_ledger_root(root)
    path = root_path / "evidence.sqlite3"
    if not path.exists():
        return []
    with sqlite3.connect(path) as db:
        db.row_factory = sqlite3.Row
        query = """
        SELECT d.*, o.terminal_status, o.terminal_candle_timestamp_utc, o.terminal_offset,
               o.exit_price, o.gross_return_pct, o.cost_pct, o.net_return_pct, o.intrabar_ambiguity,
               o.evaluator_version
        FROM decisions_v2 d JOIN outcomes_v2 o ON d.decision_id=o.decision_id
        WHERE d.schema_version=? AND o.schema_version=? AND d.side IN ('LONG','SHORT')
        ORDER BY d.candle_timestamp_utc, d.decision_id
        """
        return [dict(row) for row in db.execute(query, (DECISION_SCHEMA_VERSION, OUTCOME_SCHEMA_VERSION))]


def import_quarantine(root: Path | None = None) -> list[dict[str, Any]]:
    path = default_ledger_root(root) / "evidence.sqlite3"
    if not path.exists():
        return []
    with sqlite3.connect(path) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute("SELECT * FROM quarantine ORDER BY quarantine_id")]


def decision_lineage(decision_id: str, root: Path | None = None) -> dict[str, Any] | None:
    path = default_ledger_root(root) / "evidence.sqlite3"
    if not path.exists():
        return None
    with sqlite3.connect(path) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(
            "SELECT d.*, o.evaluator_version, o.terminal_status, o.terminal_candle_timestamp_utc, "
            "o.terminal_offset, o.gross_return_pct, o.cost_pct, o.net_return_pct, o.intrabar_ambiguity "
            "FROM decisions_v2 d LEFT JOIN outcomes_v2 o ON d.decision_id=o.decision_id WHERE d.decision_id=?",
            (decision_id,),
        ).fetchone()
        return dict(row) if row else None
