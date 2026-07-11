"""Anti-storytelling evidence quality assessment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


TIER_QUALITY = {
    "TIER_0_MANUAL_CURATED": 0.90,
    "TIER_1_OFFICIAL_EXCHANGE": 1.00,
    "TIER_1_OFFICIAL_EXCHANGE_NEWS": 1.00,
    "TIER_1_OFFICIAL_REGULATOR": 1.00,
    "TIER_1_OFFICIAL_PROTOCOL": 1.00,
    "TIER_1_OFFICIAL_MACRO": 1.00,
    "TIER_1_PROTOCOL_AGGREGATOR": 0.85,
    "TIER_2_MARKET_AGGREGATOR": 0.70,
    "TIER_2_OFFICIAL_COMPANY_BLOG": 0.70,
    "TIER_2_REPUTABLE_MEDIA": 0.75,
    "TIER_3_SENTIMENT": 0.35,
    "TIER_3_AGGREGATOR_OR_SENTIMENT": 0.35,
}


@dataclass(frozen=True)
class EvidenceAssessment:
    strength: float
    grade: str
    claim_status: str
    independent_source_count: int
    directional_agreement: float
    alternative_explanations: List[str]
    limitations: List[str]


def _direction(value: Any) -> int:
    text = str(value or "").upper()
    if text in {"BULLISH", "LONG", "UP", "POSITIVE", "TRENDING_BULL"}:
        return 1
    if text in {"BEARISH", "SHORT", "DOWN", "NEGATIVE", "TRENDING_BEAR"}:
        return -1
    return 0


def evidence_relevance(item: Dict[str, Any]) -> float:
    explicit = item.get("evidence_relevance")
    if explicit is not None:
        try:
            return max(0.0, min(1.0, float(explicit)))
        except (TypeError, ValueError):
            pass
    text = str(item.get("summary") or item.get("title") or "").lower()
    direct = ("bitcoin", "crypto", "digital asset", "stablecoin", "ethereum", "blockchain", "token")
    macro = ("interest rate", "monetary policy", "inflation", "fomc", "liquidity", "risk asset")
    if any(token in text for token in direct):
        return 1.0
    if any(token in text for token in macro):
        return 0.75
    return 0.35


def assess_evidence(
    evidence: Iterable[Dict[str, Any]],
    *,
    claimed_direction: str,
    proposed_alternatives: Iterable[str] = (),
) -> EvidenceAssessment:
    rows = [dict(item) for item in evidence]
    rows = [item for item in rows if str(item.get("status", "OK")).upper() == "OK"]
    source_ids = {
        str((item.get("fields") or {}).get("source_id") or item.get("source_id") or item.get("name") or "unknown")
        for item in rows
    }
    claimed = _direction(claimed_direction)
    directional = [item for item in rows if _direction(item.get("direction")) != 0]
    aligned = sum(1 for item in directional if claimed and _direction(item.get("direction")) == claimed)
    conflicting = sum(1 for item in directional if claimed and _direction(item.get("direction")) == -claimed)
    agreement = aligned / (aligned + conflicting) if aligned + conflicting else 0.5
    qualities = []
    for item in rows:
        tier = str(item.get("source_tier") or item.get("reliability_tier") or "").upper()
        qualities.append(TIER_QUALITY.get(tier, 0.40) * evidence_relevance(item))
    source_quality = sum(qualities) / len(qualities) if qualities else 0.0
    independence = min(1.0, len(source_ids) / 3.0)
    coverage = min(1.0, len(rows) / 5.0)
    contradiction_penalty = min(0.30, conflicting * 0.08)
    strength = max(0.0, min(1.0, 0.35 * source_quality + 0.25 * independence + 0.25 * agreement + 0.15 * coverage - contradiction_penalty))
    if strength >= 0.75 and len(source_ids) >= 3 and agreement >= 0.70:
        grade, claim_status = "STRONG", "SUPPORTED_HYPOTHESIS"
    elif strength >= 0.55 and len(source_ids) >= 2:
        grade, claim_status = "MEDIUM", "PLAUSIBLE_HYPOTHESIS"
    elif rows:
        grade, claim_status = "LOW", "WEAK_HYPOTHESIS"
    else:
        grade, claim_status = "INSUFFICIENT", "INSUFFICIENT_EVIDENCE"
    alternatives = []
    for value in proposed_alternatives:
        text = str(value or "").strip()
        if text and text not in alternatives:
            alternatives.append(text)
    for item in rows:
        if claimed and _direction(item.get("direction")) == -claimed:
            text = str(item.get("summary") or item.get("title") or item.get("source_id") or "conflicting evidence")
            candidate = f"Conflicting evidence: {text[:180]}"
            if candidate not in alternatives:
                alternatives.append(candidate)
    defaults = [
        "The move may be explained by broad market beta or liquidity rather than the named event.",
        "The observed event and price move may be correlated without a causal relationship.",
        "An unobserved macro, positioning, or exchange-specific factor may dominate.",
    ]
    for value in defaults:
        if len(alternatives) >= 3:
            break
        alternatives.append(value)
    limitations = []
    if len(source_ids) < 2:
        limitations.append("Fewer than two independent evidence sources.")
    if agreement < 0.70:
        limitations.append(f"Directional evidence agreement is only {agreement:.0%}.")
    if source_quality < 0.70:
        limitations.append("Average source reliability is below the high-quality threshold.")
    limitations.append("Evidence strength measures support, not causal identification.")
    return EvidenceAssessment(
        strength=round(strength, 4), grade=grade, claim_status=claim_status,
        independent_source_count=len(source_ids), directional_agreement=round(agreement, 4),
        alternative_explanations=alternatives[:6], limitations=limitations,
    )
