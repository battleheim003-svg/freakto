"""Regime-aware family ensemble that avoids indicator double counting."""

from __future__ import annotations

from collections import defaultdict

from freakto.technical_v2.contracts import FamilyScore, RegimeAssessment, SignalEvidence


def aggregate_families(
    evidence: tuple[SignalEvidence, ...], regime: RegimeAssessment
) -> tuple[tuple[FamilyScore, ...], float]:
    grouped: dict[str, list[SignalEvidence]] = defaultdict(list)
    for item in evidence:
        grouped[item.family].append(item)
    families = []
    for family, items in grouped.items():
        directions = [item.direction * max(0.15, item.strength) for item in items]
        score = sum(directions) / len(directions)
        sign = 1 if score >= 0 else -1
        agreement = sum(1 for item in items if item.direction * sign > 0) / len(items)
        families.append(
            FamilyScore(
                family=family,
                score=round(max(-1.0, min(1.0, score)), 4),
                weight=round(regime.family_weights.get(family, 1.0), 4),
                evidence_count=len(items),
                agreement=round(agreement, 4),
            )
        )
    total_weight = sum(item.weight for item in families) or 1.0
    aggregate = sum(item.score * item.weight for item in families) / total_weight
    return tuple(sorted(families, key=lambda item: item.family)), round(aggregate, 4)
