from engine.common import ScoreComponent
from engine.score import OpportunityV2


def _opportunity(edge_gate_passed):
    return OpportunityV2(
        symbol="BTC/USDT",
        timeframe="4h",
        side="LONG",
        score=88,
        confidence_label="High",
        risk_label="Low",
        entry_zone="1 - 2",
        stop_zone="0.5",
        components=[
            ScoreComponent("Trend", 28, 28),
            ScoreComponent("Momentum", 28, 30),
            ScoreComponent("Volume", 15, 20),
            ScoreComponent("Structure", 12, 12),
            ScoreComponent("Risk Penalty", 0, 25),
        ],
        raw={
            "regime_label": "TRENDING_BULL",
            "edge_gate_passed": edge_gate_passed,
            "edge_gate_failures": [] if edge_gate_passed else ["کالیبراسیون تجربی در دسترس نیست."],
        },
    )


def test_high_raw_score_is_not_actionable_without_empirical_edge():
    opportunity = _opportunity(False)
    assert opportunity.is_actionable is False
    assert opportunity.actionability_label == "WATCHLIST"


def test_empirical_edge_allows_existing_quality_gate_to_pass():
    opportunity = _opportunity(True)
    assert opportunity.is_actionable is True
    assert opportunity.actionability_label == "HIGH_ACTIONABILITY"
