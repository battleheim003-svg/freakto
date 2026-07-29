"""Portfolio-level concentration, direction, and correlation-cluster overlay."""

from __future__ import annotations

from collections.abc import Iterable

from freakto.technical_v2.contracts import PortfolioAssessment


MAJOR_CLUSTER = {"BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "AVAX", "DOT", "LINK", "NEAR", "LTC", "BCH"}


def _base(symbol: str) -> str:
    return str(symbol).split("/")[0].split("-")[0].upper()


def assess_portfolio(
    symbol: str,
    side: str,
    positions: Iterable[dict[str, object]],
    *,
    proposed_notional_usdt: float = 250.0,
    maximum_gross_exposure_usdt: float = 5_000.0,
) -> PortfolioAssessment:
    open_positions = [item for item in positions if str(item.get("status", "OPEN")) == "OPEN"]
    gross = sum(float(item.get("notional_usdt", 0) or 0) for item in open_positions)
    same_side = sum(str(item.get("side", "")).upper() == side.upper() for item in open_positions)
    base = _base(symbol)
    correlated = sum(_base(str(item.get("symbol", ""))) in MAJOR_CLUSTER for item in open_positions) if base in MAJOR_CLUSTER else 0
    projected = gross + proposed_notional_usdt
    concentration = proposed_notional_usdt / max(projected, proposed_notional_usdt)
    multiplier = 1.0
    warnings = []
    if same_side >= 3:
        multiplier *= 0.7
        warnings.append("SAME_SIDE_CONCENTRATION")
    if correlated >= 4:
        multiplier *= 0.7
        warnings.append("CORRELATED_CRYPTO_EXPOSURE")
    if projected > maximum_gross_exposure_usdt:
        multiplier *= max(0.2, (maximum_gross_exposure_usdt - gross) / max(proposed_notional_usdt, 1))
        warnings.append("GROSS_EXPOSURE_LIMIT")
    status = "BLOCK" if multiplier <= 0.2 else "REDUCE" if multiplier < 1 else "PASS"
    return PortfolioAssessment(status, round(gross, 2), same_side, correlated, round(concentration, 4), round(max(0.0, min(1.0, multiplier)), 4), tuple(warnings))
