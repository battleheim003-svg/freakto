import math

import pandas as pd
import pytest

from engine.outcome_economics import (
    enrich_planned_economics,
    first_touch_return,
    parse_price,
    parse_targets,
    return_metrics,
    round_trip_cost_pct,
    signed_price_return_pct,
)


def _frame() -> pd.DataFrame:
    return pd.DataFrame({
        "side": ["LONG", "SHORT", "LONG"],
        "entry_price": [100.0, 100.0, 100.0],
        "stop_zone": ["95", "105", "95"],
        "targets": ['["104", "108"]', '["96", "92"]', '["104"]'],
        "fee_bps_per_side": [10.0, 10.0, 10.0],
        "slippage_bps_per_side": [5.0, 5.0, 5.0],
        "first_exit_reason": ["TARGET_1", "STOP", "STOP_FIRST_CONSERVATIVE_AMBIGUOUS"],
        "first_exit_candle_offset": [1, 2, 1],
        "intrabar_ambiguity": [False, False, True],
        "net_signed_return_after_1c_pct": [0.5, -0.5, -0.2],
        "net_signed_return_after_3c_pct": [0.7, -0.7, 0.2],
        "net_signed_return_after_6c_pct": [0.9, -0.9, 0.4],
        "net_signed_return_after_12c_pct": [1.0, -1.0, 0.5],
    })


def test_price_and_target_parsing_handles_formatted_values():
    assert parse_price("29,481") == 29481.0
    assert math.isnan(parse_price("نامشخص"))
    assert parse_targets('["29,481", "29,588"]') == [29481.0, 29588.0]


def test_round_trip_cost_reconstructs_legacy_bps():
    frame = pd.DataFrame({
        "fee_bps_per_side": [10.0],
        "slippage_bps_per_side": [5.0],
    })
    assert round_trip_cost_pct(frame).iloc[0] == pytest.approx(0.30)


def test_signed_price_return_is_direction_aware():
    entry = pd.Series([100.0, 100.0])
    exit_price = pd.Series([105.0, 95.0])
    side = pd.Series(["LONG", "SHORT"])
    result = signed_price_return_pct(entry, exit_price, side)
    assert result.tolist() == pytest.approx([5.0, 5.0])


def test_enriched_planned_economics_includes_costs_and_break_even():
    enriched = enrich_planned_economics(_frame())
    assert enriched.loc[0, "_target_1_net_return_pct"] == pytest.approx(3.7)
    assert enriched.loc[0, "_stop_net_return_pct"] == pytest.approx(-5.3)
    assert enriched.loc[0, "_planned_net_reward_risk"] == pytest.approx(3.7 / 5.3)
    assert enriched.loc[0, "_planned_break_even_win_rate"] == pytest.approx(5.3 / 9.0)


def test_first_touch_uses_recorded_first_exit_only_within_horizon():
    enriched = enrich_planned_economics(_frame())
    one_candle = first_touch_return(enriched, 1, ambiguity_policy="STOP_FIRST")
    three_candle = first_touch_return(enriched, 3, ambiguity_policy="STOP_FIRST")
    assert one_candle.iloc[0] == pytest.approx(3.7)
    assert one_candle.iloc[1] == pytest.approx(-0.5)  # stop occurred after 1c
    assert three_candle.iloc[1] == pytest.approx(-5.3)


def test_intrabar_ambiguity_policy_changes_only_ambiguous_row():
    enriched = enrich_planned_economics(_frame())
    conservative = first_touch_return(enriched, 1, ambiguity_policy="STOP_FIRST")
    optimistic = first_touch_return(enriched, 1, ambiguity_policy="TARGET_FIRST")
    dropped = first_touch_return(enriched, 1, ambiguity_policy="DROP")
    assert conservative.iloc[2] == pytest.approx(-5.3)
    assert optimistic.iloc[2] == pytest.approx(3.7)
    assert math.isnan(dropped.iloc[2])
    assert conservative.iloc[0] == optimistic.iloc[0]


def test_return_metrics_exposes_payoff_implied_break_even():
    metrics = return_metrics([1.0, 1.0, -2.0, -2.0])
    assert metrics.win_rate == pytest.approx(0.5)
    assert metrics.payoff_ratio == pytest.approx(0.5)
    assert metrics.break_even_win_rate == pytest.approx(2.0 / 3.0)
    assert metrics.expectancy == pytest.approx(-0.5)
    assert metrics.profit_factor == pytest.approx(0.5)
