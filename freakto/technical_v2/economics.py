"""Net expected-value gate including execution, exchange, and funding costs."""

from __future__ import annotations

from freakto.technical_v2.contracts import EconomicsAssessment, ExecutionAssessment, TradeGeometry


def assess_economics(
    confidence: float,
    geometry: TradeGeometry,
    execution: ExecutionAssessment,
    *,
    fee_bps_per_side: float = 10.0,
    funding_bps: float = 0.0,
    rollover_bps: float = 0.0,
) -> EconomicsAssessment:
    probability = max(0.01, min(0.99, float(confidence)))
    win_pct = abs(geometry.target - geometry.entry) / geometry.entry * 100
    loss_pct = abs(geometry.entry - geometry.stop) / geometry.entry * 100
    fee_pct = fee_bps_per_side * 2 / 100
    funding_pct = max(0.0, funding_bps) / 100
    rollover_pct = max(0.0, rollover_bps) / 100
    execution_pct = execution.estimated_round_trip_cost_pct
    total_cost = fee_pct + funding_pct + rollover_pct + execution_pct
    gross_ev = probability * win_pct - (1 - probability) * loss_pct
    net_ev = gross_ev - total_cost
    break_even = (loss_pct + total_cost) / max(win_pct + loss_pct, 1e-12)
    status = "POSITIVE" if net_ev > 0 else "MARGINAL" if net_ev > -0.05 else "NEGATIVE"
    return EconomicsAssessment(
        win_probability=round(probability, 4),
        gross_expected_value_pct=round(gross_ev, 5),
        total_cost_pct=round(total_cost, 5),
        net_expected_value_pct=round(net_ev, 5),
        break_even_probability=round(min(1.0, break_even), 4),
        status=status,
        cost_breakdown={"fees": round(fee_pct, 5), "execution": round(execution_pct, 5), "funding": round(funding_pct, 5), "rollover": round(rollover_pct, 5)},
    )
