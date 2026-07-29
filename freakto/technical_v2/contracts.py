"""Stable, serialisable contracts for the isolated Technical Engine v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SignalEvidence:
    name: str
    family: str
    value: float
    direction: float
    strength: float
    timeframe: str = "base"
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FamilyScore:
    family: str
    score: float
    weight: float
    evidence_count: int
    agreement: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RegimeAssessment:
    label: str
    trend: float
    volatility_percentile: float
    confidence: float
    family_weights: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TradeGeometry:
    entry: float
    stop: float
    target: float
    invalidation: float
    stop_distance_pct: float
    reward_risk: float
    cost_adjusted_reward_risk: float
    expiry_bars: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RiskAssessment:
    risk_level: int
    position_scale: float
    maximum_open_positions: int
    admission_threshold: float
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["warnings"] = list(self.warnings)
        return payload


@dataclass(frozen=True)
class CalibrationSummary:
    status: str = "UNCALIBRATED"
    samples: int = 0
    empirical_win_rate: float | None = None
    brier_score: float | None = None
    expected_calibration_error: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DataQualityAssessment:
    status: str
    score: float
    rows: int
    latest_timestamp: str | None
    freshness_seconds: float | None
    missing_candles: int
    duplicate_timestamps: int
    outlier_candles: int
    source_divergence_bps: float | None = None
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["reasons"] = list(self.reasons)
        return payload


@dataclass(frozen=True)
class SetupAssessment:
    name: str
    status: str
    direction: str
    strength: float
    entry_timeframe: str
    context_timeframes: tuple[str, ...]
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["context_timeframes"] = list(self.context_timeframes)
        payload["reasons"] = list(self.reasons)
        return payload


@dataclass(frozen=True)
class EconomicsAssessment:
    win_probability: float
    gross_expected_value_pct: float
    total_cost_pct: float
    net_expected_value_pct: float
    break_even_probability: float
    status: str
    cost_breakdown: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExecutionAssessment:
    entry_price: float
    effective_entry_price: float
    spread_bps: float
    slippage_bps: float
    latency_bps: float
    fill_ratio: float
    estimated_round_trip_cost_pct: float
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["warnings"] = list(self.warnings)
        return payload


@dataclass(frozen=True)
class PortfolioAssessment:
    status: str
    gross_exposure_usdt: float
    same_side_positions: int
    correlated_positions: int
    concentration: float
    size_multiplier: float
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["warnings"] = list(self.warnings)
        return payload


@dataclass(frozen=True)
class TechnicalDecision:
    symbol: str
    side: str
    timestamp: str
    raw_score: float
    confidence: float
    recommendation: str
    regime: RegimeAssessment
    family_scores: tuple[FamilyScore, ...]
    evidence: tuple[SignalEvidence, ...]
    timeframe_scores: dict[str, float]
    timeframe_agreement: float
    geometry: TradeGeometry
    risk: RiskAssessment
    calibration: CalibrationSummary = field(default_factory=CalibrationSummary)
    data_quality: DataQualityAssessment | None = None
    setup: SetupAssessment | None = None
    economics: EconomicsAssessment | None = None
    execution: ExecutionAssessment | None = None
    portfolio: PortfolioAssessment | None = None
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    engine_version: str = "technical-v2.1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "side": self.side,
            "timestamp": self.timestamp,
            "raw_score": self.raw_score,
            "confidence": self.confidence,
            "recommendation": self.recommendation,
            "regime": self.regime.to_dict(),
            "family_scores": [item.to_dict() for item in self.family_scores],
            "evidence": [item.to_dict() for item in self.evidence],
            "timeframe_scores": dict(self.timeframe_scores),
            "timeframe_agreement": self.timeframe_agreement,
            "geometry": self.geometry.to_dict(),
            "risk": self.risk.to_dict(),
            "calibration": self.calibration.to_dict(),
            "data_quality": self.data_quality.to_dict() if self.data_quality else None,
            "setup": self.setup.to_dict() if self.setup else None,
            "economics": self.economics.to_dict() if self.economics else None,
            "execution": self.execution.to_dict() if self.execution else None,
            "portfolio": self.portfolio.to_dict() if self.portfolio else None,
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
            "engine_version": self.engine_version,
        }
