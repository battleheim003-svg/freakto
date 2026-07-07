from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from airdrop.collectors.base import BaseCollector
from airdrop.models import AirdropCandidate, ContractRef


class ConfiguredWatchlistCollector(BaseCollector):
    """Load curated or manually reviewed opportunities from JSON.

    This keeps the radar useful even when a public source changes its API. Add
    projects here after manual review; the scoring engine will still rank them
    with the same logic as automated collectors.
    """

    name = "configured_watchlist"

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def collect(self) -> list[AirdropCandidate]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        items: list[dict[str, Any]] = payload.get("items", payload if isinstance(payload, list) else [])
        candidates: list[AirdropCandidate] = []
        for item in items:
            contracts = [
                ContractRef(
                    address=str(c.get("address", "")),
                    chain_id=str(c.get("chain_id", "")) or None,
                    chain_name=str(c.get("chain_name", "")) or None,
                )
                for c in item.get("contracts", [])
                if c.get("address")
            ]
            candidates.append(
                AirdropCandidate(
                    name=item.get("name", "Unknown"),
                    slug=item.get("slug", ""),
                    source=item.get("source", self.name),
                    source_url=item.get("source_url", ""),
                    official_url=item.get("official_url", ""),
                    twitter_url=item.get("twitter_url", ""),
                    discord_url=item.get("discord_url", ""),
                    docs_url=item.get("docs_url", ""),
                    category=item.get("category", "unknown"),
                    chains=item.get("chains", []),
                    task_type=item.get("task_type", "unknown"),
                    token_status=item.get("token_status", "unknown"),
                    description=item.get("description", ""),
                    tvl_usd=_to_float(item.get("tvl_usd")),
                    volume_usd=_to_float(item.get("volume_usd")),
                    fees_24h_usd=_to_float(item.get("fees_24h_usd")),
                    revenue_24h_usd=_to_float(item.get("revenue_24h_usd")),
                    funding=item.get("funding", ""),
                    investors=item.get("investors", []),
                    estimated_minutes=_to_int(item.get("estimated_minutes")),
                    estimated_cost_usd=_to_float(item.get("estimated_cost_usd")),
                    deadline=item.get("deadline", ""),
                    priority_hint=_to_int(item.get("priority_hint")) or 0,
                    contracts=contracts,
                    tags=item.get("tags", []),
                    raw=item,
                )
            )
        return candidates


def _to_float(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
