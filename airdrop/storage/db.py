from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from airdrop.models import ScoredAirdrop


SCHEMA = """
CREATE TABLE IF NOT EXISTS airdrop_opportunities (
    identity TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT,
    source TEXT,
    level TEXT,
    final_score INTEGER,
    action TEXT,
    official_url TEXT,
    source_url TEXT,
    category TEXT,
    chains_json TEXT,
    candidate_json TEXT,
    scored_json TEXT,
    first_seen_at TEXT,
    last_seen_at TEXT,
    sent_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_airdrop_score ON airdrop_opportunities(final_score DESC);
CREATE INDEX IF NOT EXISTS idx_airdrop_level ON airdrop_opportunities(level);
"""


class AirdropDatabase:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self):
        return sqlite3.connect(self.path)

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def upsert_scored(self, scored: ScoredAirdrop) -> bool:
        """Insert/update item. Returns True if this is a new identity."""
        c = scored.candidate
        self.init()
        with self.connect() as conn:
            cur = conn.execute("SELECT identity FROM airdrop_opportunities WHERE identity = ?", (c.identity,))
            exists = cur.fetchone() is not None
            payload = (
                c.identity,
                c.name,
                c.slug,
                c.source,
                scored.level,
                scored.final_score,
                scored.action,
                c.official_url,
                c.source_url,
                c.category,
                json.dumps(c.chains, ensure_ascii=False),
                json.dumps(c.to_dict(), ensure_ascii=False),
                scored.to_json(),
                c.discovered_at,
                scored.scored_at,
            )
            if exists:
                conn.execute(
                    """
                    UPDATE airdrop_opportunities
                    SET name=?, slug=?, source=?, level=?, final_score=?, action=?, official_url=?,
                        source_url=?, category=?, chains_json=?, candidate_json=?, scored_json=?, last_seen_at=?
                    WHERE identity=?
                    """,
                    (
                        c.name,
                        c.slug,
                        c.source,
                        scored.level,
                        scored.final_score,
                        scored.action,
                        c.official_url,
                        c.source_url,
                        c.category,
                        json.dumps(c.chains, ensure_ascii=False),
                        json.dumps(c.to_dict(), ensure_ascii=False),
                        scored.to_json(),
                        scored.scored_at,
                        c.identity,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO airdrop_opportunities
                    (identity, name, slug, source, level, final_score, action, official_url, source_url,
                     category, chains_json, candidate_json, scored_json, first_seen_at, last_seen_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    payload,
                )
            return not exists

    def mark_sent(self, identity: str, sent_at: str) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE airdrop_opportunities SET sent_at=? WHERE identity=?", (sent_at, identity))

    def was_sent(self, identity: str) -> bool:
        self.init()
        with self.connect() as conn:
            cur = conn.execute("SELECT sent_at FROM airdrop_opportunities WHERE identity=?", (identity,))
            row = cur.fetchone()
            return bool(row and row[0])

    def top(self, limit: int = 20) -> list[dict]:
        self.init()
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM airdrop_opportunities ORDER BY final_score DESC, last_seen_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]
