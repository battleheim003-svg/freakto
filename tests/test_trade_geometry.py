import pandas as pd
import pytest

from engine.trade_geometry import (
    GeometrySpec,
    candidate_pretrade_features,
    derive_geometry_features,
    geometry_filter_mask,
    simulate_geometry_returns,
)


def _frame() -> pd.DataFrame:
    return pd.DataFrame({
        "side": ["LONG", "LONG", "LONG", "SHORT"],
        "entry_price": [100.0, 100.0, 100.0, 100.0],
        "stop_zone": ["98", "98", "98", "102"],
        "targets": ['["103"]', '["103"]', '["103"]', '["97"]'],
        "fee_bps_per_side": [2.0] * 4,
        "slippage_bps_per_side": [1.0] * 4,
        "mfe_pct": [3.5, 0.5, 3.5, 0.5],
        "mae_pct": [-0.5, -2.5, -2.5, -0.5],
        "gross_signed_return_after_1c_pct": [1.0, -1.0, 0.0, 0.3],
        "gross_signed_return_after_3c_pct": [1.0, -1.0, 0.0, 0.3],
        "gross_signed_return_after_6c_pct": [1.0, -1.0, 0.0, 0.3],
        "gross_signed_return_after_12c_pct": [1.0, -1.0, 0.0, 0.3],
    })


def test_geometry_uses_planned_stop_when_atr_is_missing():
    enriched = derive_geometry_features(_frame())
    assert enriched["_risk_unit_pct"].tolist() == pytest.approx([2.0, 2.0, 2.0, 2.0])
    assert set(enriched["_risk_unit_source"]) == {"PLANNED_STOP_PROXY"}


def test_geometry_prefers_native_atr_when_available():
    frame = _frame()
    frame["atr_pct"] = [1.25, 1.25, 1.25, 1.25]
    enriched = derive_geometry_features(frame)
    assert enriched["_risk_unit_pct"].tolist() == pytest.approx([1.25] * 4)
    assert set(enriched["_risk_unit_source"]) == {"ATR:atr_pct"}


def test_candidate_pretrade_features_include_net_geometry_and_cost_ratios():
    enriched = derive_geometry_features(_frame())
    features = candidate_pretrade_features(
        enriched, GeometrySpec(horizon_candles=6, stop_multiplier=1.0, reward_risk=1.5)
    )
    assert features.loc[0, "risk_gross_pct"] == pytest.approx(2.0)
    assert features.loc[0, "target_gross_pct"] == pytest.approx(3.0)
    assert features.loc[0, "execution_cost_pct"] == pytest.approx(0.06)
    assert features.loc[0, "target_net_pct"] == pytest.approx(2.94)
    assert features.loc[0, "net_reward_risk"] == pytest.approx(2.94 / 2.06)


def test_fixed_geometry_stop_first_resolves_target_stop_and_both():
    enriched = derive_geometry_features(_frame())
    spec = GeometrySpec(horizon_candles=6, stop_multiplier=1.0, reward_risk=1.5)
    returns, diagnostics, detail = simulate_geometry_returns(enriched, spec)
    assert returns.iloc[0] == pytest.approx(2.94)   # target only
    assert returns.iloc[1] == pytest.approx(-2.06)  # stop only
    assert returns.iloc[2] == pytest.approx(-2.06)  # both -> conservative stop
    assert returns.iloc[3] == pytest.approx(0.24)   # neither -> fixed close minus cost
    assert diagnostics.both_hit_count == 1
    assert detail["both_hit"].sum() == 1


def test_management_first_is_explicit_optimistic_bound():
    enriched = derive_geometry_features(_frame())
    spec = GeometrySpec(
        horizon_candles=6,
        stop_multiplier=1.0,
        reward_risk=1.5,
        path_assumption="MANAGEMENT_FIRST",
    )
    returns, _, _ = simulate_geometry_returns(enriched, spec)
    assert returns.iloc[2] == pytest.approx(2.94)


def test_break_even_and_trailing_are_path_assumption_aware():
    frame = _frame().iloc[[0]].copy()
    frame["mfe_pct"] = [2.5]
    frame["mae_pct"] = [-0.5]
    frame["gross_signed_return_after_6c_pct"] = [-0.4]
    enriched = derive_geometry_features(frame)
    break_even, diagnostics, _ = simulate_geometry_returns(
        enriched,
        GeometrySpec(horizon_candles=6, reward_risk=2.0, management_policy="BREAK_EVEN"),
    )
    trailing, trailing_diagnostics, _ = simulate_geometry_returns(
        enriched,
        GeometrySpec(
            horizon_candles=6,
            reward_risk=2.0,
            management_policy="TRAILING",
            trailing_trigger_r=1.0,
            trailing_distance_r=0.75,
        ),
    )
    assert break_even.iloc[0] == pytest.approx(-0.06)
    assert diagnostics.break_even_count == 1
    assert trailing.iloc[0] == pytest.approx(0.94)
    assert trailing_diagnostics.trailing_count == 1


def test_geometry_filter_uses_only_pretrade_cost_and_reward_risk():
    enriched = derive_geometry_features(_frame())
    features = candidate_pretrade_features(enriched, GeometrySpec(horizon_candles=6, reward_risk=1.5))
    accepted = geometry_filter_mask(
        features,
        minimum_target_cost_multiple=10.0,
        maximum_cost_to_risk=0.10,
        minimum_net_reward_risk=1.0,
    )
    rejected = geometry_filter_mask(
        features,
        minimum_target_cost_multiple=100.0,
        maximum_cost_to_risk=0.01,
        minimum_net_reward_risk=2.0,
    )
    assert accepted.all()
    assert not rejected.any()
