"""Risk-admission policy for the isolated Showcase Paper lab.

The policy never changes Decision Engine output.  It only decides which
directional observations the non-evidence Showcase layer may simulate.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RiskPolicy:
    level: int
    key: str
    minimum_score: int
    minimum_confidence: int
    allowed_recommendations: tuple[str, ...]
    maximum_open_positions: int
    notional_usdt: float
    stop_loss_pct: float
    take_profit_pct: float
    reentry_cooldown_minutes: int
    analysis_depth: str
    technical_indicators: tuple[str, ...]
    minimum_confluence_pct: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SessionPreset:
    key: str
    risk_level: int
    daily_trade_limit: int
    scan_interval_seconds: int
    maximum_holding_minutes: int
    leverage: float
    market_mode: str
    analysis_depth: int = 100

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


SESSION_PRESETS = {
    "PRECISION": SessionPreset("PRECISION", 0, 0, 300, 60, 1.0, "LIVE_PUBLIC"),
    "BALANCED": SessionPreset("BALANCED", 35, 0, 60, 20, 1.0, "LIVE_PUBLIC"),
    "RAPID_TEST": SessionPreset("RAPID_TEST", 100, 0, 15, 5, 1.0, "ACCELERATED_REPLAY"),
}


TECHNICAL_STACK = (
    "EMA_4_10",
    "PRICE_MOMENTUM",
    "RSI_14",
    "EMA_10_21",
    "MACD_12_26_9",
    "BOLLINGER_POSITION",
    "ROC_5",
    "STOCHASTIC_14",
    "VOLUME_CONFIRMATION",
    "BREAKOUT_20",
    "CANDLE_STRUCTURE",
    "ATR_REGIME",
)


def session_preset(key: str) -> SessionPreset:
    normalized = str(key or "BALANCED").strip().upper()
    if normalized not in SESSION_PRESETS:
        raise ValueError(f"Unknown Showcase session preset: {key}")
    return SESSION_PRESETS[normalized]


def risk_policy(level: int | float) -> RiskPolicy:
    parsed = max(0, min(100, int(round(float(level)))))
    if parsed <= 20:
        key = "PRECISION"
        allowed = ("ELITE", "ACTIONABLE")
        indicator_count = 3
        depth = "FOCUSED"
    elif parsed <= 55:
        key = "CAUTIOUS"
        allowed = ("ELITE", "ACTIONABLE", "WATCHLIST")
        indicator_count = 6
        depth = "MULTI_SIGNAL"
    elif parsed <= 80:
        key = "ACTIVE_TEST"
        allowed = ("ELITE", "ACTIONABLE", "WATCHLIST", "MONITOR")
        indicator_count = 10
        depth = "DEEP_CONFLUENCE"
    else:
        key = "EXPLORATORY"
        allowed = ("ELITE", "ACTIONABLE", "WATCHLIST", "MONITOR", "IGNORE", "UNRATED")
        indicator_count = len(TECHNICAL_STACK)
        depth = "FULL_TECHNICAL_STACK"

    # Higher tolerance widens admission while keeping bounded virtual exposure.
    return RiskPolicy(
        level=parsed,
        key=key,
        minimum_score=round(78 - parsed * 0.38),
        minimum_confidence=round(72 - parsed * 0.32),
        allowed_recommendations=allowed,
        maximum_open_positions=min(12, 3 + parsed // 10),
        notional_usdt=round(100 + parsed * 1.5, 2),
        stop_loss_pct=round(0.45 + parsed * 0.0045, 3),
        take_profit_pct=round(0.70 + parsed * 0.005, 3),
        reentry_cooldown_minutes=max(0, round(15 - parsed * 0.22)),
        analysis_depth=depth,
        technical_indicators=TECHNICAL_STACK[:indicator_count],
        minimum_confluence_pct=max(45, round(65 - parsed * 0.2)),
    )


def admission_reason(signal: dict[str, object], policy: RiskPolicy) -> str | None:
    side = str(signal.get("side", "NEUTRAL")).upper()
    if side not in {"LONG", "SHORT"}:
        return "NOT_DIRECTIONAL"
    if int(signal.get("score", 0) or 0) < policy.minimum_score:
        return "SCORE_BELOW_POLICY"
    if int(signal.get("confidence", 0) or 0) < policy.minimum_confidence:
        return "CONFIDENCE_BELOW_POLICY"
    recommendation = str(signal.get("recommendation", "UNRATED") or "UNRATED").upper()
    if recommendation not in policy.allowed_recommendations:
        return "RECOMMENDATION_BLOCKED"
    confluence = signal.get("technical_confluence_pct")
    if confluence is not None and float(confluence) < policy.minimum_confluence_pct:
        return "TECHNICAL_CONFLUENCE_BELOW_POLICY"
    return None
