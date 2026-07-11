"""Portfolio-level decision and correlation-aware shadow allocation."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

import numpy as np
import pandas as pd


VERSION = "portfolio-decision-v1"


@dataclass
class AssetAllocation:
    symbol: str
    side: str
    allocation_pct: float
    shadow_allocation_pct: float
    historical_win_probability: float
    expected_r: float
    annualized_volatility: float
    correlation_penalty: float
    reason: str


@dataclass
class PortfolioDecision:
    version: str
    status: str
    risk_level: str
    gross_allocation_pct: float
    cash_allocation_pct: float
    average_pairwise_correlation: float
    max_pairwise_correlation: float
    correlation_status: str
    allocations: List[AssetAllocation] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _returns(item: Any) -> pd.Series:
    values = pd.to_numeric(pd.Series(list(getattr(item, "return_history", []) or [])), errors="coerce").dropna()
    return values.tail(180).reset_index(drop=True)


def _correlation_matrix(items: List[Any]) -> pd.DataFrame:
    columns: Dict[str, pd.Series] = {}
    for item in items:
        series = _returns(item)
        if len(series) >= 20:
            columns[str(item.symbol)] = series
    if len(columns) < 2:
        return pd.DataFrame()
    return pd.DataFrame(columns).corr(min_periods=20)


def _pairwise_stats(matrix: pd.DataFrame) -> tuple[float, float]:
    if matrix.empty or len(matrix) < 2:
        return 0.0, 0.0
    values = matrix.to_numpy(dtype=float)
    upper = values[np.triu_indices_from(values, k=1)]
    upper = upper[np.isfinite(upper)]
    return (float(np.mean(upper)), float(np.max(upper))) if len(upper) else (0.0, 0.0)


def build_portfolio_decision(items: Iterable[Any], *, max_gross_allocation_pct: float = 75.0) -> PortfolioDecision:
    shadow_candidates = [
        item for item in items
        if getattr(item, "side", "") in {"LONG", "SHORT"}
        and getattr(item, "recommendation", "") in {"ELITE", "ACTIONABLE", "WATCHLIST", "MONITOR"}
    ]
    capital_candidates = {
        item.symbol for item in shadow_candidates
        if getattr(item, "recommendation", "") in {"ELITE", "ACTIONABLE", "WATCHLIST"}
    }
    matrix = _correlation_matrix(shadow_candidates)
    average_corr, max_corr = _pairwise_stats(matrix)
    correlation_status = "HIGH" if max_corr >= 0.75 else "MEDIUM" if max_corr >= 0.45 else "LOW"
    raw_shadow: Dict[str, float] = {}
    raw_live: Dict[str, float] = {}
    metrics: Dict[str, tuple[float, float]] = {}
    for item in shadow_candidates:
        returns = _returns(item)
        volatility = float(returns.std(ddof=1) * math.sqrt(365 * 6)) if len(returns) >= 20 else 1.0
        volatility = max(0.05, volatility)
        if not matrix.empty and item.symbol in matrix:
            peers = matrix[item.symbol].drop(labels=[item.symbol], errors="ignore").clip(lower=0).dropna()
            correlation_penalty = 1.0 / (1.0 + (float(peers.mean()) if len(peers) else 0.0))
        else:
            correlation_penalty = 0.75
        quality = max(0.01, float(getattr(item, "opportunity_score", 0.0) or 0.0) / 100.0)
        raw_shadow[item.symbol] = quality * correlation_penalty / volatility
        probability = float(getattr(item, "historical_win_probability", 0.0) or 0.0)
        expected_r = float(getattr(item, "expected_r", 0.0) or 0.0)
        usable = bool(getattr(item, "calibration_usable", False))
        raw_live[item.symbol] = max(0.0, expected_r) * max(0.0, probability - 0.5) * correlation_penalty / volatility if usable and item.symbol in capital_candidates else 0.0
        metrics[item.symbol] = (volatility, correlation_penalty)

    shadow_total = sum(raw_shadow.values())
    live_total = sum(raw_live.values())
    allocations: List[AssetAllocation] = []
    gross_limit = max(0.0, min(100.0, float(max_gross_allocation_pct)))
    for item in shadow_candidates:
        shadow = raw_shadow[item.symbol] / shadow_total * gross_limit if shadow_total else 0.0
        allocation = raw_live[item.symbol] / live_total * gross_limit if live_total else 0.0
        volatility, penalty = metrics[item.symbol]
        if allocation > 0:
            reason = "validated positive calibrated edge"
        elif item.symbol not in capital_candidates:
            reason = "shadow only: asset recommendation is MONITOR"
        else:
            reason = "shadow only: calibrated edge is not validated positive"
        allocations.append(AssetAllocation(
            symbol=item.symbol, side=item.side,
            allocation_pct=round(allocation, 2), shadow_allocation_pct=round(shadow, 2),
            historical_win_probability=round(float(getattr(item, "historical_win_probability", 0.0) or 0.0), 4),
            expected_r=round(float(getattr(item, "expected_r", 0.0) or 0.0), 4),
            annualized_volatility=round(volatility, 4), correlation_penalty=round(penalty, 4),
            reason=reason,
        ))
    allocations.sort(key=lambda item: (item.allocation_pct, item.shadow_allocation_pct), reverse=True)
    blockers: List[str] = []
    if not shadow_candidates:
        blockers.append("No directional portfolio candidate passed the existing trade-quality gates.")
    if shadow_candidates and live_total <= 0:
        blockers.append("No candidate has a validated positive calibrated expectancy; capital allocation is zero.")
    if max_corr >= 0.85:
        blockers.append(f"Portfolio concentration is excessive: max pairwise correlation={max_corr:.3f}.")
    gross = round(sum(item.allocation_pct for item in allocations), 2)
    if gross > 0 and max_corr < 0.75:
        status = "PORTFOLIO_ALLOCATION_READY_FOR_PAPER"
    elif shadow_candidates:
        status = "PORTFOLIO_SHADOW_ONLY"
    else:
        status = "PORTFOLIO_NO_CANDIDATES"
    risk_level = "HIGH" if max_corr >= 0.75 or gross > 75 else "MEDIUM" if gross > 40 or max_corr >= 0.45 else "LOW"
    return PortfolioDecision(
        version=VERSION, status=status, risk_level=risk_level,
        gross_allocation_pct=gross, cash_allocation_pct=round(100.0 - gross, 2),
        average_pairwise_correlation=round(average_corr, 4), max_pairwise_correlation=round(max_corr, 4),
        correlation_status=correlation_status, allocations=allocations, blockers=blockers,
        warnings=["Shadow allocations are diagnostics only when allocation_pct is zero."],
    )


def format_portfolio_decision(decision: PortfolioDecision) -> str:
    lines = [
        "=" * 100,
        f"Portfolio Decision {decision.version}",
        f"Status: {decision.status} | Risk: {decision.risk_level}",
        f"Gross/Cash: {decision.gross_allocation_pct:.2f}% / {decision.cash_allocation_pct:.2f}%",
        f"Correlation avg/max: {decision.average_pairwise_correlation:.3f} / {decision.max_pairwise_correlation:.3f} ({decision.correlation_status})",
    ]
    for item in decision.allocations:
        lines.append(
            f"- {item.symbol} {item.side}: allocate={item.allocation_pct:.2f}% "
            f"shadow={item.shadow_allocation_pct:.2f}% p={item.historical_win_probability:.1%} E[R]={item.expected_r:+.3f}"
        )
    lines.extend(f"[BLOCKER] {item}" for item in decision.blockers)
    lines.append("=" * 100)
    return "\n".join(lines)
