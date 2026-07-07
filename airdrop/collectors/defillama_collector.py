from __future__ import annotations

from airdrop.collectors.base import BaseCollector
from airdrop.http_client import HttpClient
from airdrop.models import AirdropCandidate


class DefiLlamaTokenlessCollector(BaseCollector):
    """Collect tokenless-likely DeFi protocols from DefiLlama's free API.

    DefiLlama's public /protocols endpoint is not an airdrop guarantee. We use
    it as a traction source and filter for projects that look tokenless or have
    no clear token symbol. Final scoring keeps this uncertainty visible.
    """

    name = "defillama_protocols"
    API_URL = "https://api.llama.fi/protocols"

    def __init__(
        self,
        min_tvl_usd: float = 1_000_000,
        max_items: int = 200,
        timeout: int = 20,
    ):
        self.min_tvl_usd = min_tvl_usd
        self.max_items = max_items
        self.client = HttpClient(timeout=timeout)

    def collect(self) -> list[AirdropCandidate]:
        data = self.client.get_json(self.API_URL)
        if not isinstance(data, list):
            return []

        candidates: list[AirdropCandidate] = []
        for item in data:
            tvl = _to_float(item.get("tvl"))
            if tvl is None or tvl < self.min_tvl_usd:
                continue

            symbol = str(item.get("symbol") or "").strip()
            token_status = _infer_token_status(symbol, item)
            if token_status == "has-token-or-unknown":
                # Still skip most known-token protocols. This collector is for
                # airdrop discovery, not generic DeFi monitoring.
                continue

            name = item.get("name") or item.get("slug") or "Unknown"
            candidates.append(
                AirdropCandidate(
                    name=name,
                    slug=item.get("slug", ""),
                    source=self.name,
                    source_url=f"https://defillama.com/protocol/{item.get('slug')}" if item.get("slug") else "https://defillama.com/airdrops",
                    official_url=item.get("url") or "",
                    twitter_url=_twitter_url(item.get("twitter")),
                    category=item.get("category") or "DeFi",
                    chains=item.get("chains") or [],
                    task_type="protocol interaction",
                    token_status=token_status,
                    description=item.get("description") or "Tokenless-likely protocol discovered from DefiLlama protocol data.",
                    tvl_usd=tvl,
                    raw=item,
                    tags=["defillama", "tokenless", "protocol"],
                )
            )
            if len(candidates) >= self.max_items:
                break
        return candidates


def _to_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _infer_token_status(symbol: str, item: dict) -> str:
    lowered = symbol.lower().strip()
    if lowered in {"", "-", "none", "n/a", "null"}:
        return "tokenless-likely"
    if item.get("mcap") in (None, 0, "0") and lowered in {"tbd", "points"}:
        return "tokenless-likely"
    return "has-token-or-unknown"


def _twitter_url(value: str | None) -> str:
    if not value:
        return ""
    text = str(value).strip()
    if text.startswith("http"):
        return text
    return "https://x.com/" + text.lstrip("@")
