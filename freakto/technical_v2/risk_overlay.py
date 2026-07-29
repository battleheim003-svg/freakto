"""Paper-only risk overlay; deliberately independent from analysis depth."""

from __future__ import annotations

from freakto.technical_v2.contracts import RiskAssessment


def assess_risk(
    risk_level: int,
    *,
    confidence: float,
    timeframe_agreement: float,
    geometry_rr: float,
    high_volatility: bool = False,
) -> RiskAssessment:
    level = max(0, min(100, int(risk_level)))
    threshold = 0.72 - level * 0.0032
    position_scale = 0.25 + level * 0.0075
    warnings = []
    if timeframe_agreement < 0.60:
        position_scale *= 0.65
        warnings.append("LOW_TIMEFRAME_AGREEMENT")
    if geometry_rr < 1.2:
        position_scale *= 0.50
        warnings.append("WEAK_COST_ADJUSTED_GEOMETRY")
    if high_volatility:
        position_scale *= 0.75
        warnings.append("HIGH_VOLATILITY")
    if confidence < threshold:
        warnings.append("BELOW_RISK_ADMISSION_THRESHOLD")
    return RiskAssessment(
        risk_level=level,
        position_scale=round(max(0.1, min(1.0, position_scale)), 4),
        maximum_open_positions=min(12, 2 + level // 10),
        admission_threshold=round(threshold, 4),
        warnings=tuple(warnings),
    )
