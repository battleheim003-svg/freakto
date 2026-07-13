from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine.feature_architecture_v2 import (
    FeatureArchitectureV2Config,
    apply_thresholds,
    chronological_development_split,
    engineer_entry_features,
    entry_gate_mask,
    fit_architecture_bundle,
    model_coefficients,
    predict_architecture,
    prepare_architecture_rows,
    select_side_threshold,
    validate_entry_feature_names,
)


def synthetic_rows(rows: int = 1800, *, start: str = "2019-01-01") -> pd.DataFrame:
    rng = np.random.default_rng(12345)
    ts = pd.date_range(start, periods=rows, freq="4h", tz="UTC")
    side = np.where(np.arange(rows) % 2 == 0, "LONG", "SHORT")
    trend = rng.uniform(0, 28, rows)
    momentum = rng.uniform(0, 30, rows)
    volume = rng.uniform(0, 20, rows)
    structure = rng.uniform(0, 12, rows)
    regime_score = rng.uniform(-5, 5, rows)
    risk = rng.uniform(0, 12, rows)
    atr = rng.uniform(0.6, 4.0, rows)
    rsi = rng.uniform(20, 80, rows)
    macd = rng.normal(0, 1, rows)
    cost = rng.uniform(0.20, 0.70, rows)
    entry = rng.uniform(100, 300, rows)
    stop_distance = rng.uniform(1.2, 3.0, rows)
    target_distance = rng.uniform(1.5, 4.5, rows)
    stop = np.where(side == "LONG", entry * (1 - stop_distance / 100), entry * (1 + stop_distance / 100))
    target = np.where(side == "LONG", entry * (1 + target_distance / 100), entry * (1 - target_distance / 100))
    side_sign = np.where(side == "LONG", 1.0, -1.0)
    # Stable learnable relation without using aggregate score.
    returns = (
        0.055 * trend
        + 0.030 * volume
        - 0.070 * risk
        + 0.20 * (structure >= 4)
        + 0.08 * side_sign * regime_score
        - cost
        + rng.normal(0, 0.55, rows)
        - 0.65
    )
    market = rng.normal(0.05, 1.4, rows)
    return pd.DataFrame(
        {
            "decision_id": [f"d{i}" for i in range(rows)],
            "candle_timestamp": ts,
            "symbol": np.array(["BTC/USDT", "ETH/USDT", "SOL/USDT"])[np.arange(rows) % 3],
            "timeframe": "4h",
            "side": side,
            "regime": np.array(["BULL", "BEAR", "SIDEWAYS"])[np.arange(rows) % 3],
            "score": trend + momentum + volume + structure + 20 - risk,
            "trend_score": trend,
            "momentum_score": momentum,
            "volume_score": volume,
            "structure_score": structure,
            "regime_score": regime_score,
            "risk_penalty": risk,
            "atr_pct": atr,
            "rsi_14": rsi,
            "macd_histogram": macd,
            "round_trip_cost_pct": cost,
            "entry_price": entry,
            "target_1": target,
            "stop_price": stop,
            "market_return_after_6c_pct": market,
            "net_signed_return_after_6c_pct": returns,
        }
    )


def config() -> FeatureArchitectureV2Config:
    return FeatureArchitectureV2Config(
        development_cutoff_utc="2026-07-09T12:00:00Z",
        purge_timestamps=3,
        minimum_train_samples_per_side=120,
        minimum_optimize_samples=30,
        minimum_holdout_samples=40,
        structure_gate_min=4.0,
        expected_return_thresholds=(-0.1, 0.0, 0.1, 0.2),
    )


def test_leakage_and_aggregate_score_are_rejected():
    with pytest.raises(ValueError):
        validate_entry_feature_names(["future_return"])
    with pytest.raises(ValueError):
        validate_entry_feature_names(["score"])


def test_prepare_rows_enforces_cutoff_and_deduplicates():
    frame = synthetic_rows(400)
    duplicate = frame.tail(1).copy()
    duplicate["candle_timestamp"] = pd.Timestamp("2027-01-01", tz="UTC")
    work = prepare_architecture_rows(pd.concat([frame, frame.tail(1), duplicate], ignore_index=True), config())
    assert work["decision_id"].is_unique
    assert work["__timestamp"].max() <= pd.Timestamp(config().development_cutoff_utc)
    assert set(work["side"]) == {"LONG", "SHORT"}


def test_engineering_excludes_score_and_uses_structure_gate():
    features, diagnostics = engineer_entry_features(synthetic_rows(300), config())
    assert "score" in features.columns  # metadata is preserved
    assert diagnostics["aggregate_score_used_as_feature"] is False
    assert diagnostics["structure_used_as_additive_score"] is False
    assert set(features["structure_gate"].unique()).issubset({0.0, 1.0})
    assert "cost_to_atr" in features.columns
    assert "net_reward_risk" in features.columns


def test_chronological_split_has_purge_and_no_overlap():
    split = chronological_development_split(synthetic_rows(1000), config())
    assert split.train["__timestamp"].max() < split.optimize["__timestamp"].min()
    assert split.optimize["__timestamp"].max() < split.holdout["__timestamp"].min()
    assert len(split.train) > len(split.optimize) > 0
    assert split.boundaries["purge_timestamps"] == "3"


def test_entry_gate_blocks_low_structure_and_high_risk():
    features, _ = engineer_entry_features(synthetic_rows(100), config())
    features.loc[features.index[:5], "structure_gate"] = 0.0
    features.loc[features.index[5:10], "risk_penalty"] = 99.0
    mask = entry_gate_mask(features, config())
    assert not mask.iloc[:10].any()


def test_models_are_side_specific_and_score_independent():
    split = chronological_development_split(synthetic_rows(), config())
    bundle = fit_architecture_bundle(split.train, "ARCH_V2_BASE", config())
    assert set(bundle.models) == {"LONG", "SHORT"}
    assert all("score" not in column.lower() for model in bundle.models.values() for column in model.feature_columns)
    assert all(model.side in {"LONG", "SHORT"} for model in bundle.models.values())


def test_prediction_contains_probability_and_expected_net():
    split = chronological_development_split(synthetic_rows(), config())
    bundle = fit_architecture_bundle(split.train, "ARCH_V2_BASE", config())
    pred = predict_architecture(bundle, split.optimize)
    assert pred["predicted_expected_net_pct"].notna().mean() > 0.95
    assert pred["predicted_win_probability"].between(0, 1).all()
    assert pred["gate_pass"].dtype == bool


def test_no_momentum_variant_removes_momentum_features():
    split = chronological_development_split(synthetic_rows(), config())
    bundle = fit_architecture_bundle(split.train, "ARCH_V2_NO_MOMENTUM", config())
    assert all("momentum" not in name for model in bundle.models.values() for name in model.feature_columns)


def test_threshold_selection_and_application_are_optimize_only():
    split = chronological_development_split(synthetic_rows(), config())
    bundle = fit_architecture_bundle(split.train, "ARCH_V2_BASE", config())
    optimize = predict_architecture(bundle, split.optimize)
    selections = {side: select_side_threshold(optimize, side, config()) for side in ("LONG", "SHORT")}
    holdout = predict_architecture(bundle, split.holdout)
    selected = apply_thresholds(holdout, selections)
    assert all(selection.candidate_rows for selection in selections.values())
    assert set(selected.index).issubset(set(holdout.index))


def test_coefficients_are_exportable_and_finite():
    split = chronological_development_split(synthetic_rows(), config())
    bundle = fit_architecture_bundle(split.train, "ARCH_V2_LEAN", config())
    table = model_coefficients(bundle)
    assert not table.empty
    assert {"variant", "side", "model", "feature", "coefficient"}.issubset(table.columns)
    assert np.isfinite(table["coefficient"]).all()


def test_fresh_time_scope_is_strictly_post_cutoff():
    frame = synthetic_rows(200)
    frame.loc[frame.index[-20:], "candle_timestamp"] = pd.date_range(
        "2026-07-10", periods=20, freq="4h", tz="UTC"
    )
    development = prepare_architecture_rows(frame, config(), time_scope="development")
    fresh = prepare_architecture_rows(frame, config(), time_scope="fresh")
    cutoff = pd.Timestamp(config().development_cutoff_utc)
    assert development["__timestamp"].max() <= cutoff
    assert fresh["__timestamp"].min() > cutoff
    assert set(development["decision_id"]).isdisjoint(set(fresh["decision_id"]))
