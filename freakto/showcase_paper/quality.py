"""Outcome-aware admission controls for the isolated Showcase layer.

The gate consumes only trades that were already closed before a new signal is
considered.  It never mutates Decision Engine output and it is not official
Paper/Go-live evidence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from typing import Any, Iterable


@dataclass(frozen=True)
class QualityProfile:
    key: str
    label: str
    allowed_recommendations: tuple[str, ...]
    minimum_net_expected_value_pct: float
    minimum_cost_adjusted_reward_risk: float
    minimum_confluence_pct: int
    maximum_open_positions: int | None
    dynamic_window: int
    bucket_minimum_samples: int
    side_minimum_samples: int
    minimum_bucket_win_rate: float
    minimum_bucket_profit_factor: float
    minimum_side_win_rate: float
    minimum_side_profit_factor: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


PROFILES = {
    "VOLUME": QualityProfile(
        key="VOLUME", label="Volume / exploratory",
        allowed_recommendations=("ELITE", "ACTIONABLE", "WATCHLIST", "MONITOR", "IGNORE", "UNRATED"),
        minimum_net_expected_value_pct=0.0, minimum_cost_adjusted_reward_risk=0.0,
        minimum_confluence_pct=0, maximum_open_positions=None, dynamic_window=0,
        bucket_minimum_samples=0, side_minimum_samples=0,
        minimum_bucket_win_rate=0.0, minimum_bucket_profit_factor=0.0,
        minimum_side_win_rate=0.0, minimum_side_profit_factor=0.0,
    ),
    "BALANCED": QualityProfile(
        key="BALANCED", label="Balanced quality",
        allowed_recommendations=("ELITE", "ACTIONABLE", "WATCHLIST", "MONITOR"),
        minimum_net_expected_value_pct=0.20, minimum_cost_adjusted_reward_risk=1.0,
        minimum_confluence_pct=50, maximum_open_positions=7, dynamic_window=160,
        bucket_minimum_samples=14, side_minimum_samples=50,
        minimum_bucket_win_rate=0.25, minimum_bucket_profit_factor=0.50,
        minimum_side_win_rate=0.25, minimum_side_profit_factor=0.45,
    ),
    "WIN_RATE": QualityProfile(
        key="WIN_RATE", label="Win-rate focus",
        allowed_recommendations=("ELITE", "ACTIONABLE", "WATCHLIST"),
        minimum_net_expected_value_pct=0.35, minimum_cost_adjusted_reward_risk=1.10,
        minimum_confluence_pct=55, maximum_open_positions=4, dynamic_window=200,
        bucket_minimum_samples=10, side_minimum_samples=40,
        minimum_bucket_win_rate=0.32, minimum_bucket_profit_factor=0.80,
        minimum_side_win_rate=0.30, minimum_side_profit_factor=0.55,
    ),
}


def quality_profile(key: str | None) -> QualityProfile:
    normalized = str(key or "BALANCED").strip().upper()
    if normalized not in PROFILES:
        raise ValueError(f"Unknown Showcase quality profile: {key}")
    return PROFILES[normalized]


def runbook_alignment(*, quality_mode: str, risk_level: int, analysis_depth: int) -> dict[str, Any]:
    reasons = []
    if str(quality_mode).upper() != "WIN_RATE":
        reasons.append("QUALITY_MODE_NOT_WIN_RATE")
    if not 20 <= int(risk_level) <= 35:
        reasons.append("RISK_OUTSIDE_20_35")
    if int(analysis_depth) != 100:
        reasons.append("ANALYSIS_DEPTH_NOT_100")
    return {
        "runbook_aligned": not reasons,
        "quality_mode": str(quality_mode).upper(),
        "risk_level": int(risk_level),
        "analysis_depth": int(analysis_depth),
        "reasons": reasons,
    }


def _eligible_outcomes(trades: Iterable[dict[str, Any]], *, window: int) -> list[dict[str, Any]]:
    rows = [
        trade for trade in trades
        if trade.get("status") == "CLOSED"
        and trade.get("close_reason") in {"STOP", "TARGET", "TIME_EXIT", "SIGNAL_INVALIDATED", "BREAK_EVEN"}
        and str(trade.get("side", "")) in {"LONG", "SHORT"}
    ]
    return rows[-window:] if window > 0 else rows


def outcome_metrics(trades: Iterable[dict[str, Any]]) -> dict[str, float | int]:
    rows = list(trades)
    wins = [row for row in rows if float(row.get("pnl_usdt", 0) or 0) > 0]
    losses = [row for row in rows if float(row.get("pnl_usdt", 0) or 0) <= 0]
    gross_win = sum(float(row.get("pnl_usdt", 0) or 0) for row in wins)
    gross_loss = abs(sum(float(row.get("pnl_usdt", 0) or 0) for row in losses))
    count = len(rows)
    win_rate = len(wins) / count if count else 0.0
    # Wilson lower bound is reported for visibility; the gate itself uses both
    # raw win rate and PF so small buckets cannot look falsely certain.
    if count:
        z = 1.2815515655446004  # one-sided 90% bound
        denominator = 1 + z * z / count
        centre = win_rate + z * z / (2 * count)
        margin = z * sqrt((win_rate * (1 - win_rate) + z * z / (4 * count)) / count)
        lower_bound = max(0.0, (centre - margin) / denominator)
    else:
        lower_bound = 0.0
    return {
        "samples": count,
        "wins": len(wins),
        "win_rate": round(win_rate, 6),
        "win_rate_lower_bound_90": round(lower_bound, 6),
        "profit_factor": round(gross_win / gross_loss, 6) if gross_loss else (99.0 if gross_win else 0.0),
        "net_pnl_usdt": round(gross_win - gross_loss, 6),
    }


def _dynamic_reason(signal: dict[str, Any], history: list[dict[str, Any]], profile: QualityProfile) -> tuple[str | None, dict[str, Any]]:
    if profile.dynamic_window <= 0:
        return None, {}
    outcomes = _eligible_outcomes(history, window=profile.dynamic_window)
    symbol = str(signal.get("symbol", ""))
    side = str(signal.get("side", ""))
    bucket_rows = [row for row in outcomes if row.get("symbol") == symbol and row.get("side") == side]
    side_rows = [row for row in outcomes if row.get("side") == side]
    bucket = outcome_metrics(bucket_rows)
    side_metrics = outcome_metrics(side_rows)
    diagnostics = {
        "symbol_side": bucket,
        "side": side_metrics,
        "window": profile.dynamic_window,
        "maturity": {
            "bucket_samples": int(bucket["samples"]),
            "bucket_minimum_samples": profile.bucket_minimum_samples,
            "bucket_samples_needed": max(0, profile.bucket_minimum_samples - int(bucket["samples"])),
            "side_samples": int(side_metrics["samples"]),
            "side_minimum_samples": profile.side_minimum_samples,
            "side_samples_needed": max(0, profile.side_minimum_samples - int(side_metrics["samples"])),
        },
    }

    # A sufficiently healthy exact bucket may override a weak global side. This
    # keeps empirically strong exceptions (for example a specific LONG symbol)
    # without reopening every weak LONG candidate.
    bucket_mature = int(bucket["samples"]) >= profile.bucket_minimum_samples
    bucket_healthy = (
        bucket_mature
        and float(bucket["win_rate"]) >= profile.minimum_bucket_win_rate
        and float(bucket["profit_factor"]) >= profile.minimum_bucket_profit_factor
    )
    if bucket_mature and not bucket_healthy:
        return "QUALITY_SYMBOL_SIDE_QUARANTINE", diagnostics
    if bucket_healthy:
        return None, diagnostics

    side_mature = int(side_metrics["samples"]) >= profile.side_minimum_samples
    if side_mature and (
        float(side_metrics["win_rate"]) < profile.minimum_side_win_rate
        or float(side_metrics["profit_factor"]) < profile.minimum_side_profit_factor
    ):
        return "QUALITY_SIDE_QUARANTINE", diagnostics
    return None, diagnostics


def maturity_report(
    trades: Iterable[dict[str, Any]], *, profile_key: str = "WIN_RATE", session_baseline: int = 0,
) -> dict[str, Any]:
    profile = quality_profile(profile_key)
    rows = list(trades)
    outcomes = _eligible_outcomes(rows, window=profile.dynamic_window)
    side_rows = {side: [row for row in outcomes if row.get("side") == side] for side in ("LONG", "SHORT")}
    side = {
        key: {
            **outcome_metrics(values),
            "minimum_samples": profile.side_minimum_samples,
            "samples_needed": max(0, profile.side_minimum_samples - len(values)),
            "mature": len(values) >= profile.side_minimum_samples,
        }
        for key, values in side_rows.items()
    }
    organic_closed = _eligible_outcomes(
        [trade for trade in rows if trade.get("status") == "CLOSED"][max(0, int(session_baseline)):],
        window=0,
    )
    target = 50
    return {
        "profile": profile.key,
        "session": {
            "organic_closed_trades": len(organic_closed),
            "minimum_samples": target,
            "samples_needed": max(0, target - len(organic_closed)),
            "mature": len(organic_closed) >= target,
        },
        "side": side,
    }


def quality_admission_reason(
    signal: dict[str, Any], history: Iterable[dict[str, Any]], profile: QualityProfile,
) -> tuple[str | None, dict[str, Any]]:
    if signal.get("breadth_sufficient") is False and profile.key != "VOLUME":
        return "QUALITY_INSUFFICIENT_BREADTH", {}
    recommendation = str(signal.get("recommendation", "UNRATED") or "UNRATED").upper()
    if recommendation not in profile.allowed_recommendations:
        return "QUALITY_RECOMMENDATION_BLOCKED", {}
    confluence = signal.get("technical_confluence_pct")
    if confluence is not None and float(confluence) < profile.minimum_confluence_pct:
        return "QUALITY_CONFLUENCE_BELOW_POLICY", {}
    economics = dict(signal.get("economics") or {})
    if economics and float(economics.get("net_expected_value_pct", 0) or 0) < profile.minimum_net_expected_value_pct:
        return "QUALITY_NET_EV_BELOW_POLICY", {}
    geometry = dict(signal.get("trade_geometry") or {})
    if geometry and float(geometry.get("cost_adjusted_reward_risk", 0) or 0) < profile.minimum_cost_adjusted_reward_risk:
        return "QUALITY_REWARD_RISK_BELOW_POLICY", {}
    return _dynamic_reason(signal, list(history), profile)
