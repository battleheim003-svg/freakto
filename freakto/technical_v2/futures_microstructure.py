"""Optional futures and microstructure evidence family.

Missing external data remains neutral; it never fabricates order-book or futures values.
"""

from __future__ import annotations

from collections.abc import Mapping

from freakto.technical_v2.contracts import SignalEvidence
from freakto.technical_v2.features import clamp


def microstructure_evidence(data: Mapping[str, float] | None, *, timeframe: str = "1m") -> tuple[tuple[SignalEvidence, ...], dict[str, object]]:
    if not data:
        return (), {"status": "UNAVAILABLE", "fields": [], "warnings": ["MICROSTRUCTURE_DATA_UNAVAILABLE"]}
    evidence = []
    if "open_interest_change_pct" in data:
        value = float(data["open_interest_change_pct"])
        price_change = float(data.get("price_change_pct", 0))
        direction = clamp(value / 3) * (1 if price_change >= 0 else -1)
        evidence.append(SignalEvidence("OPEN_INTEREST_CHANGE", "microstructure", value, direction, abs(direction), timeframe))
    if "funding_rate_pct" in data:
        value = float(data["funding_rate_pct"])
        direction = clamp(-value / 0.05)
        evidence.append(SignalEvidence("FUNDING_EXTREME", "microstructure", value, direction, abs(direction), timeframe, "Contrarian crowding signal"))
    if "taker_buy_ratio" in data:
        value = float(data["taker_buy_ratio"])
        direction = clamp((value - 0.5) * 4)
        evidence.append(SignalEvidence("TAKER_IMBALANCE", "microstructure", value, direction, abs(direction), timeframe))
    if "order_book_imbalance" in data:
        value = float(data["order_book_imbalance"])
        direction = clamp(value)
        evidence.append(SignalEvidence("ORDER_BOOK_IMBALANCE", "microstructure", value, direction, abs(direction), timeframe))
    if "liquidation_imbalance" in data:
        value = float(data["liquidation_imbalance"])
        direction = clamp(-value)
        evidence.append(SignalEvidence("LIQUIDATION_IMBALANCE", "microstructure", value, direction, abs(direction), timeframe))
    return tuple(evidence), {"status": "AVAILABLE" if evidence else "PARTIAL", "fields": [item.name for item in evidence], "warnings": [] if evidence else ["NO_SUPPORTED_MICROSTRUCTURE_FIELDS"]}
