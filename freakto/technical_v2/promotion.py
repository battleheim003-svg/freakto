"""Fail-closed automated champion/challenger recommendation."""

from __future__ import annotations


def promotion_recommendation(
    champion: dict[str, object],
    challenger: dict[str, object],
    validation: dict[str, object],
    *,
    minimum_samples: int = 200,
) -> dict[str, object]:
    blockers = []
    if int(challenger.get("samples", 0) or 0) < minimum_samples:
        blockers.append("INSUFFICIENT_CHALLENGER_SAMPLES")
    if validation.get("status") != "PASSED":
        blockers.append("WALK_FORWARD_NOT_PASSED")
    challenger_ev = float(challenger.get("expectancy_pct", 0) or 0)
    champion_ev = float(champion.get("expectancy_pct", 0) or 0)
    if challenger_ev <= champion_ev:
        blockers.append("NO_EXPECTANCY_IMPROVEMENT")
    if float(challenger.get("maximum_drawdown_pct", 0) or 0) > float(champion.get("maximum_drawdown_pct", 100) or 100):
        blockers.append("DRAWDOWN_REGRESSION")
    return {"status": "PROMOTE_TO_SHADOW" if not blockers else "KEEP_RESEARCH", "blockers": blockers, "live_eligible": False}
