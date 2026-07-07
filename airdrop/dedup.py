from __future__ import annotations

from urllib.parse import urlparse

from airdrop.models import AirdropCandidate, normalize_slug


def deduplicate(candidates: list[AirdropCandidate]) -> list[AirdropCandidate]:
    merged: dict[str, AirdropCandidate] = {}
    for candidate in candidates:
        key = _dedupe_key(candidate)
        if key not in merged:
            merged[key] = candidate
            continue
        merged[key] = _merge(merged[key], candidate)
    return list(merged.values())


def _dedupe_key(c: AirdropCandidate) -> str:
    domain = _domain(c.official_url)
    if domain:
        return domain
    return normalize_slug(c.name)


def _domain(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url if "://" in url else "https://" + url)
    host = (parsed.hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def _merge(a: AirdropCandidate, b: AirdropCandidate) -> AirdropCandidate:
    a.source = "+".join(sorted(set(a.source.split("+") + b.source.split("+"))))
    a.source_url = a.source_url or b.source_url
    a.official_url = a.official_url or b.official_url
    a.twitter_url = a.twitter_url or b.twitter_url
    a.discord_url = a.discord_url or b.discord_url
    a.docs_url = a.docs_url or b.docs_url
    a.category = a.category if a.category != "unknown" else b.category
    a.chains = sorted(set(a.chains + b.chains))
    a.tags = sorted(set(a.tags + b.tags + ["multi-source"]))
    a.description = a.description or b.description
    a.tvl_usd = max(x for x in [a.tvl_usd, b.tvl_usd] if x is not None) if any(x is not None for x in [a.tvl_usd, b.tvl_usd]) else None
    a.volume_usd = max(x for x in [a.volume_usd, b.volume_usd] if x is not None) if any(x is not None for x in [a.volume_usd, b.volume_usd]) else None
    a.fees_24h_usd = max(x for x in [a.fees_24h_usd, b.fees_24h_usd] if x is not None) if any(x is not None for x in [a.fees_24h_usd, b.fees_24h_usd]) else None
    a.funding = a.funding or b.funding
    a.investors = sorted(set(a.investors + b.investors))
    a.estimated_minutes = a.estimated_minutes or b.estimated_minutes
    a.estimated_cost_usd = a.estimated_cost_usd if a.estimated_cost_usd is not None else b.estimated_cost_usd
    a.priority_hint += b.priority_hint
    a.contracts.extend(b.contracts)
    a.raw.setdefault("merged", []).append(b.to_dict())
    return a
