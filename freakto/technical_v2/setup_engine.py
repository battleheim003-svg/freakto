"""Regime-specific technical setup selection and lower-timeframe entry timing."""

from __future__ import annotations

from freakto.technical_v2.contracts import FamilyScore, RegimeAssessment, SetupAssessment


def select_setup(
    *,
    side: str,
    regime: RegimeAssessment,
    structure: dict[str, object],
    volume: dict[str, float | str],
    family_scores: tuple[FamilyScore, ...],
    timeframe_scores: dict[str, float],
    timeframe_agreement: float,
) -> SetupAssessment:
    scores = {item.family: item.score for item in family_scores}
    directional = 1 if side == "LONG" else -1
    event = str(structure.get("event", "RANGE_STRUCTURE"))
    relative_volume = float(volume.get("relative_volume", 0) or 0)
    candidates: list[tuple[str, float, list[str]]] = []
    if "TREND" in regime.label:
        strength = directional * (scores.get("trend", 0) * 0.45 + scores.get("momentum", 0) * 0.35) + timeframe_agreement * 0.2
        candidates.append(("TREND_PULLBACK", strength, ["trend_regime", "trend_momentum_alignment"]))
        continuation = directional * scores.get("momentum", 0) * 0.55 + relative_volume / 4 + timeframe_agreement * 0.2
        candidates.append(("MOMENTUM_CONTINUATION", continuation, ["momentum", "relative_volume"]))
    if "BOS" in event:
        strength = 0.45 + min(0.25, relative_volume / 8) + timeframe_agreement * 0.3
        candidates.append(("BREAKOUT_VOLUME", strength, [event, f"relative_volume:{relative_volume:.2f}"]))
    if "SWEEP" in event or "CHOCH" in event:
        strength = 0.45 + abs(scores.get("structure", 0)) * 0.35 + abs(scores.get("mean_reversion", 0)) * 0.2
        candidates.append(("LIQUIDITY_SWEEP_REVERSAL", strength, [event, "structure_reversal"]))
    if regime.label.startswith("RANGE"):
        strength = abs(scores.get("mean_reversion", 0)) * 0.6 + abs(scores.get("structure", 0)) * 0.2 + timeframe_agreement * 0.2
        candidates.append(("RANGE_MEAN_REVERSION", strength, ["range_regime", "mean_reversion"]))
    if "HIGH_VOL" in regime.label:
        strength = abs(scores.get("volatility", 0)) * 0.45 + abs(scores.get("momentum", 0)) * 0.35 + relative_volume / 10
        candidates.append(("VOLATILITY_EXPANSION", strength, ["high_volatility", "momentum_expansion"]))
    if not candidates:
        candidates.append(("NO_VALID_SETUP", 0.0, ["no_regime_specific_setup"]))
    name, strength, reasons = max(candidates, key=lambda item: item[1])
    entry_timeframe = "1m" if "1m" in timeframe_scores else "3m" if "3m" in timeframe_scores else "5m" if "5m" in timeframe_scores else next(iter(timeframe_scores))
    entry_score = timeframe_scores.get(entry_timeframe, 0.0)
    timing_aligned = entry_score * directional > 0
    strength = max(0.0, min(1.0, strength * (1.0 if timing_aligned else 0.65)))
    status = "ACTIONABLE" if name != "NO_VALID_SETUP" and strength >= 0.42 else "WATCH" if name != "NO_VALID_SETUP" and strength >= 0.25 else "REJECTED"
    if not timing_aligned:
        reasons.append("entry_timeframe_not_aligned")
    return SetupAssessment(
        name=name,
        status=status,
        direction=side,
        strength=round(strength, 4),
        entry_timeframe=entry_timeframe,
        context_timeframes=tuple(name for name in timeframe_scores if name != entry_timeframe),
        reasons=tuple(reasons),
    )
