from __future__ import annotations

import numpy as np
import pandas as pd

from engine.multi_cycle_validation import (
    MultiCycleValidationConfig,
    expanding_validation,
    fixed_gate,
    population_stability_index,
    regime_stability,
    return_metrics,
    rolling_validation,
    run_multi_cycle_validation,
)


def replay_frame(start="2020-01-01", periods=1000, shift=0.0):
    rng = np.random.default_rng(42)
    timestamps = pd.date_range(start, periods=periods, freq="12h", tz="UTC")
    returns = rng.normal(shift, 1.0, periods)
    score = rng.integers(45, 96, periods)
    return pd.DataFrame(
        {
            "candle_timestamp": timestamps,
            "net_signed_return_after_6c_pct": returns,
            "score": score,
            "side": np.where(np.arange(periods) % 2 == 0, "LONG", "SHORT"),
            "regime": np.where(np.arange(periods) % 3 == 0, "BULL", "BEAR"),
            "symbol": "BTC/USDT",
            "atr_pct": rng.normal(2.0 + shift, 0.2, periods),
            "rsi_14": rng.normal(50.0, 8.0, periods),
        }
    )


def test_return_metrics_has_expected_profit_factor_and_counts():
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2020-01-01", periods=4, freq="D", tz="UTC"),
            "net_return_pct": [2.0, 1.0, -1.0, -1.0],
            "score": [80, 80, 80, 80],
            "side": ["LONG"] * 4,
        }
    )
    metrics = return_metrics(frame)
    assert metrics.sample_count == 4
    assert metrics.win_rate == 0.5
    assert metrics.expectancy == 0.25
    assert metrics.profit_factor == 1.5


def test_fixed_gate_is_pre_registered_and_directional_only():
    frame = replay_frame(periods=20)
    frame.loc[0, "side"] = "NEUTRAL"
    frame.loc[1, "score"] = 69
    selected = fixed_gate(frame, 70)
    assert selected["score"].min() >= 70
    assert set(selected["side"]) <= {"LONG", "SHORT"}


def test_rolling_validation_is_time_bounded():
    rows = rolling_validation(replay_frame(periods=1200), window_days=120, step_days=60, min_samples=50, label="FULL")
    assert rows
    assert all(pd.Timestamp(row["start_utc"]) < pd.Timestamp(row["end_utc"]) for row in rows)


def test_expanding_validation_never_overlaps_train_and_test():
    rows = expanding_validation(
        replay_frame(periods=3000), min_train_days=365, test_days=90, min_samples=50, label="FULL"
    )
    assert rows
    assert all(row["no_overlap"] for row in rows)
    assert all(pd.Timestamp(row["train_end_utc"]) == pd.Timestamp(row["test_start_utc"]) for row in rows)


def test_population_stability_index_detects_shift():
    rng = np.random.default_rng(3)
    reference = rng.normal(0, 1, 5000)
    stable = rng.normal(0, 1, 5000)
    shifted = rng.normal(2, 1, 5000)
    assert population_stability_index(reference, shifted) > population_stability_index(reference, stable)


def test_regime_stability_records_each_window_and_cross_window_summary():
    frames = {"3Y": replay_frame(periods=500), "5Y": replay_frame(periods=800, shift=0.1)}
    rows = regime_stability(frames, min_samples=30)
    assert any(row["window"] == "3Y" for row in rows)
    assert any(row["window"] == "5Y" for row in rows)
    assert any(row["window"] == "ALL_WINDOWS" for row in rows)


def test_validation_is_descriptive_and_never_promotes(tmp_path):
    frames = {"3Y": replay_frame(periods=1200), "5Y": replay_frame(periods=2000, shift=0.05)}
    config = MultiCycleValidationConfig(
        output_dir=str(tmp_path),
        rolling_window_days=120,
        rolling_step_days=60,
        expanding_min_train_days=365,
        expanding_test_days=90,
        min_window_samples=30,
    )
    report = run_multi_cycle_validation(frames, config)
    assert report.status == "COMPLETE_NO_PROMOTION"
    assert report.promotion_applied is False
    assert report.paper_live_enabled is False
    assert (tmp_path / "multi_cycle_validation_report.json").exists()
