"""Append-only prediction snapshots and observed airdrop outcomes."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUTCOME_STATUSES = {
    "PENDING",
    "CLAIMED",
    "LISTED",
    "NO_AIRDROP",
    "EXPIRED",
    "RUG",
}
RESOLVED_STATUSES = OUTCOME_STATUSES - {"PENDING"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS prediction_snapshots (
    prediction_id TEXT PRIMARY KEY,
    identity TEXT NOT NULL,
    name TEXT NOT NULL,
    predicted_at TEXT NOT NULL,
    score INTEGER NOT NULL CHECK(score BETWEEN 0 AND 100),
    level TEXT NOT NULL,
    scored_json TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    UNIQUE(identity, predicted_at)
);

CREATE TABLE IF NOT EXISTS outcome_observations (
    observation_id TEXT PRIMARY KEY,
    identity TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    status TEXT NOT NULL,
    eligible INTEGER,
    claimed INTEGER,
    gross_reward_usd REAL,
    cost_usd REAL NOT NULL DEFAULT 0,
    source_ref TEXT NOT NULL,
    notes TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_prediction_identity_time
ON prediction_snapshots(identity, predicted_at);
CREATE INDEX IF NOT EXISTS idx_outcome_identity_time
ON outcome_observations(identity, observed_at);
"""


def _utc(value: str | datetime) -> datetime:
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(
        str(value).replace("Z", "+00:00")
    )
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(value: str | datetime) -> str:
    return _utc(value).replace(microsecond=0).isoformat()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _stable_id(*parts: Any) -> str:
    raw = "|".join(str(value) for value in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


@dataclass(frozen=True)
class PredictionSnapshot:
    identity: str
    name: str
    predicted_at: str
    score: int
    level: str
    scored_json: str

    @property
    def prediction_id(self) -> str:
        return _stable_id(self.identity, _iso(self.predicted_at), self.score, self.level)


@dataclass(frozen=True)
class OutcomeObservation:
    identity: str
    observed_at: str
    status: str
    source_ref: str
    eligible: bool | None = None
    claimed: bool | None = None
    gross_reward_usd: float | None = None
    cost_usd: float = 0.0
    notes: str = ""

    @property
    def observation_id(self) -> str:
        return _stable_id(
            self.identity,
            _iso(self.observed_at),
            self.status.upper(),
            self.source_ref,
        )


class OutcomeTracker:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def init(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def record_prediction(self, snapshot: PredictionSnapshot) -> bool:
        identity = str(snapshot.identity).strip()
        if not identity:
            raise ValueError("Prediction identity is required.")
        score = int(snapshot.score)
        if not 0 <= score <= 100:
            raise ValueError("Prediction score must be between 0 and 100.")
        predicted_at = _iso(snapshot.predicted_at)
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO prediction_snapshots
                (prediction_id, identity, name, predicted_at, score, level, scored_json, imported_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot.prediction_id,
                    identity,
                    str(snapshot.name),
                    predicted_at,
                    score,
                    str(snapshot.level),
                    str(snapshot.scored_json),
                    _now(),
                ),
            )
            return cursor.rowcount == 1

    def sync_opportunity_database(self, source_path: str | Path) -> int:
        source = Path(source_path)
        if not source.is_file():
            raise FileNotFoundError(source)
        imported = 0
        with sqlite3.connect(source) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                "SELECT identity, name, final_score, level, scored_json, last_seen_at "
                "FROM airdrop_opportunities"
            ).fetchall()
        for row in rows:
            payload = json.loads(row["scored_json"] or "{}")
            predicted_at = payload.get("scored_at") or row["last_seen_at"]
            if not predicted_at:
                continue
            snapshot = PredictionSnapshot(
                identity=str(row["identity"]),
                name=str(row["name"]),
                predicted_at=str(predicted_at),
                score=int(row["final_score"]),
                level=str(row["level"]),
                scored_json=str(row["scored_json"]),
            )
            imported += int(self.record_prediction(snapshot))
        return imported

    def record_outcome(self, observation: OutcomeObservation) -> bool:
        identity = str(observation.identity).strip()
        status = str(observation.status).strip().upper()
        if not identity:
            raise ValueError("Outcome identity is required.")
        if status not in OUTCOME_STATUSES:
            raise ValueError(f"Unsupported outcome status: {status}")
        observed_at = _iso(observation.observed_at)
        source_ref = str(observation.source_ref).strip()
        if not source_ref:
            raise ValueError("Every outcome observation requires an auditable source_ref.")
        cost = float(observation.cost_usd)
        if cost < 0:
            raise ValueError("Outcome cost cannot be negative.")
        reward = (
            None
            if observation.gross_reward_usd is None
            else float(observation.gross_reward_usd)
        )
        if reward is not None and reward < 0:
            raise ValueError("Gross reward cannot be negative.")
        if status in RESOLVED_STATUSES and observation.eligible is None:
            raise ValueError("Resolved outcomes require an explicit eligible value.")

        with self.connect() as connection:
            prediction = connection.execute(
                """
                SELECT predicted_at FROM prediction_snapshots
                WHERE identity=? ORDER BY predicted_at ASC LIMIT 1
                """,
                (identity,),
            ).fetchone()
            if prediction is None:
                raise ValueError("Outcome cannot be recorded before a prediction snapshot exists.")
            if _utc(observed_at) <= _utc(prediction["predicted_at"]):
                raise ValueError("Outcome observation must be later than the first prediction.")
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO outcome_observations
                (observation_id, identity, observed_at, status, eligible, claimed,
                 gross_reward_usd, cost_usd, source_ref, notes, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    observation.observation_id,
                    identity,
                    observed_at,
                    status,
                    _optional_bool(observation.eligible),
                    _optional_bool(observation.claimed),
                    reward,
                    cost,
                    source_ref,
                    str(observation.notes),
                    _now(),
                ),
            )
            return cursor.rowcount == 1


def _optional_bool(value: bool | None) -> int | None:
    return None if value is None else int(bool(value))
