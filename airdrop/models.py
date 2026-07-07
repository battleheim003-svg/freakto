"""
Core data models for Freakto Airdrop Radar.

The radar intentionally stores evidence, warnings and score components so every
recommendation is explainable. It is not designed to auto-connect wallets,
auto-sign transactions, or auto-claim airdrops.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any
import hashlib
import json
import re


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_slug(value: str) -> str:
    text = (value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "unknown"


@dataclass
class ContractRef:
    address: str
    chain_id: str | None = None
    chain_name: str | None = None


@dataclass
class AirdropCandidate:
    name: str
    source: str
    source_url: str = ""
    slug: str = ""
    official_url: str = ""
    twitter_url: str = ""
    discord_url: str = ""
    docs_url: str = ""
    category: str = "unknown"
    chains: list[str] = field(default_factory=list)
    task_type: str = "unknown"
    token_status: str = "unknown"  # tokenless-likely, no-token-confirmed, has-token-or-unknown
    description: str = ""
    tvl_usd: float | None = None
    volume_usd: float | None = None
    fees_24h_usd: float | None = None
    revenue_24h_usd: float | None = None
    funding: str = ""
    investors: list[str] = field(default_factory=list)
    estimated_minutes: int | None = None
    estimated_cost_usd: float | None = None
    deadline: str = ""
    priority_hint: int = 0
    contracts: list[ContractRef] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)
    discovered_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        if not self.slug:
            self.slug = normalize_slug(self.name)
        self.chains = [str(c).strip() for c in self.chains if str(c).strip()]
        self.tags = [str(t).strip().lower() for t in self.tags if str(t).strip()]

    @property
    def identity(self) -> str:
        base = self.slug or normalize_slug(self.name)
        if self.official_url:
            base += "|" + self.official_url.lower().strip()
        return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["identity"] = self.identity
        return data


@dataclass
class ScoreComponent:
    name: str
    score: int
    max_score: int
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ScoredAirdrop:
    candidate: AirdropCandidate
    final_score: int
    level: str
    action: str
    components: list[ScoreComponent]
    positive_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    security_flags: list[str] = field(default_factory=list)
    scored_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate": self.candidate.to_dict(),
            "final_score": self.final_score,
            "level": self.level,
            "action": self.action,
            "components": [asdict(c) for c in self.components],
            "positive_reasons": self.positive_reasons,
            "warnings": self.warnings,
            "security_flags": self.security_flags,
            "scored_at": self.scored_at,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
