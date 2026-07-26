"""Composition service for the isolated Technical Engine v2 challenger."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd

from freakto.technical_v2.contracts import SignalEvidence, TechnicalDecision
from freakto.technical_v2.data_quality import aggregate_quality, assess_data_quality
from freakto.technical_v2.economics import assess_economics
from freakto.technical_v2.ensemble import aggregate_families
from freakto.technical_v2.execution_simulator import estimate_execution
from freakto.technical_v2.features import clamp, extract_evidence, validate_frame
from freakto.technical_v2.futures_microstructure import microstructure_evidence
from freakto.technical_v2.market_structure import analyse_market_structure
from freakto.technical_v2.multi_timeframe import assess_timeframes
from freakto.technical_v2.portfolio_risk import assess_portfolio
from freakto.technical_v2.regime import assess_regime
from freakto.technical_v2.risk_overlay import assess_risk
from freakto.technical_v2.segmented_calibration import segmented_calibration
from freakto.technical_v2.setup_engine import select_setup
from freakto.technical_v2.trade_geometry import build_trade_geometry
from freakto.technical_v2.volume_analysis import analyse_volume


def analysis_profile(depth: int) -> dict[str, object]:
    parsed = max(0, min(100, int(depth)))
    if parsed <= 25:
        label, timeframes = "FOCUSED", ("5m",)
    elif parsed <= 55:
        label, timeframes = "MULTI_SIGNAL", ("1m", "5m", "15m")
    elif parsed <= 80:
        label, timeframes = "DEEP_CONFLUENCE", ("1m", "5m", "15m", "1h")
    else:
        label, timeframes = "PROFESSIONAL_MTF", ("1m", "5m", "15m", "1h", "4h")
    return {"depth": parsed, "label": label, "timeframes": timeframes}


class TechnicalEngineV2:
    def __init__(self, *, analysis_depth: int = 100, risk_level: int = 35):
        self.analysis_depth = max(0, min(100, int(analysis_depth)))
        self.risk_level = max(0, min(100, int(risk_level)))

    def analyse(
        self,
        symbol: str,
        frames: Mapping[str, pd.DataFrame],
        *,
        timestamp: str,
        calibration_observations: Sequence[tuple[float, bool]] = (),
        segmented_observations: Sequence[dict[str, object]] = (),
        microstructure_data: Mapping[str, float] | None = None,
        portfolio_positions: Sequence[dict[str, object]] = (),
        require_fresh: bool = False,
        reference_closes: Mapping[str, float] | None = None,
    ) -> TechnicalDecision:
        if not frames:
            raise ValueError("Technical Engine v2 requires at least one causal frame")
        base_name = "5m" if "5m" in frames else next(iter(frames))
        base = validate_frame(frames[base_name])
        quality_reports = {
            name: assess_data_quality(
                frame,
                timeframe=name,
                require_fresh=require_fresh,
                reference_close=(reference_closes or {}).get(name),
            )
            for name, frame in frames.items()
        }
        data_quality = aggregate_quality(quality_reports)
        regime = assess_regime(base)
        evidence = list(extract_evidence(base, timeframe=base_name, depth=self.analysis_depth))
        structure = analyse_market_structure(base)
        volume = analyse_volume(base)
        evidence.extend(
            [
                SignalEvidence(
                    "MARKET_STRUCTURE", "structure", float(base["close"].iloc[-1]),
                    float(structure["direction"]), abs(float(structure["direction"])), base_name,
                    str(structure["event"]),
                ),
                SignalEvidence(
                    "VWAP_LIQUIDITY", "volume", float(volume["vwap_distance"]),
                    clamp(float(volume["vwap_distance"]) * 250),
                    clamp(abs(float(volume["vwap_distance"])) * 250, 0, 1), base_name,
                    str(volume["quality"]),
                ),
            ]
        )
        micro_evidence, micro_status = microstructure_evidence(microstructure_data, timeframe=base_name)
        evidence.extend(micro_evidence)
        family_scores, family_aggregate = aggregate_families(tuple(evidence), regime)
        timeframe_scores, timeframe_aggregate, agreement, counter_trend = assess_timeframes(
            frames, depth=self.analysis_depth
        )
        aggregate = clamp(family_aggregate * 0.65 + timeframe_aggregate * 0.35)
        side = "LONG" if aggregate >= 0 else "SHORT"
        confidence = min(0.99, max(0.01, 0.45 + abs(aggregate) * 0.38 + agreement * 0.17))
        geometry = build_trade_geometry(base, side)
        setup = select_setup(
            side=side,
            regime=regime,
            structure=structure,
            volume=volume,
            family_scores=family_scores,
            timeframe_scores=timeframe_scores,
            timeframe_agreement=agreement,
        )
        execution = estimate_execution(
            geometry.entry,
            side,
            volatility_percentile=regime.volatility_percentile,
            relative_volume=float(volume.get("relative_volume", 1) or 1),
        )
        funding_bps = abs(float((microstructure_data or {}).get("funding_rate_pct", 0))) * 100
        economics = assess_economics(confidence, geometry, execution, funding_bps=funding_bps)
        portfolio = assess_portfolio(symbol, side, portfolio_positions)
        risk = assess_risk(
            self.risk_level,
            confidence=confidence,
            timeframe_agreement=agreement,
            geometry_rr=geometry.cost_adjusted_reward_risk,
            high_volatility="HIGH_VOL" in regime.label,
        )
        legacy_segmented = [
            {"probability": probability, "outcome": outcome}
            for probability, outcome in calibration_observations
        ]
        calibration, calibration_segment = segmented_calibration(
            list(segmented_observations) or legacy_segmented,
            {"symbol": symbol, "setup": setup.name, "regime": regime.label, "side": side, "timeframe": setup.entry_timeframe},
        )
        warnings = list(risk.warnings)
        if counter_trend:
            warnings.append("LOWER_TIMEFRAME_COUNTER_TREND")
        if calibration.status != "CALIBRATED":
            warnings.append(calibration.status)
        if data_quality.status != "PASS":
            warnings.extend(data_quality.reasons)
        warnings.extend(execution.warnings)
        warnings.extend(portfolio.warnings)
        warnings.extend(str(item) for item in micro_status.get("warnings", []))
        strength = abs(aggregate)
        recommendation = "ELITE" if strength >= 0.62 and agreement >= 0.70 else "ACTIONABLE" if strength >= 0.38 else "WATCHLIST" if strength >= 0.20 else "MONITOR"
        if data_quality.status == "FAIL" or economics.status == "NEGATIVE" or setup.status == "REJECTED" or portfolio.status == "BLOCK":
            recommendation = "MONITOR"
        leaders = sorted(family_scores, key=lambda item: abs(item.score * item.weight), reverse=True)[:3]
        reasons = tuple(
            [f"{item.family}:{item.score:+.2f}" for item in leaders]
            + [f"setup:{setup.name}", f"net_ev:{economics.net_expected_value_pct:+.3f}%", f"regime:{regime.label}", f"mtf_agreement:{agreement:.0%}", f"calibration:{calibration_segment}"]
        )
        return TechnicalDecision(
            symbol=symbol,
            side=side,
            timestamp=str(timestamp),
            raw_score=round(aggregate, 4),
            confidence=round(confidence, 4),
            recommendation=recommendation,
            regime=regime,
            family_scores=family_scores,
            evidence=tuple(evidence),
            timeframe_scores=timeframe_scores,
            timeframe_agreement=agreement,
            geometry=geometry,
            risk=risk,
            calibration=calibration,
            data_quality=data_quality,
            setup=setup,
            economics=economics,
            execution=execution,
            portfolio=portfolio,
            reasons=reasons,
            warnings=tuple(dict.fromkeys(warnings)),
        )
