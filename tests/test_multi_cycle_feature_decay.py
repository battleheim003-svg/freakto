from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from engine.multi_cycle_feature_decay import (
    FeatureDecayConfig,
    analyze_multi_cycle_feature_decay,
    assign_non_overlapping_eras,
    component_distribution_drift,
    component_era_attribution,
    score_decay,
    select_longest_replay,
    summarize_component_decay,
    validate_feature_names,
    write_feature_decay_outputs,
)


def synthetic_replay(rows: int = 4500) -> pd.DataFrame:
    rng = np.random.default_rng(123)
    timestamps = pd.date_range("2018-01-01", "2026-07-09 12:00:00", periods=rows, tz="UTC")
    era = np.where(timestamps < pd.Timestamp("2021-07-09", tz="UTC"), "LEGACY", np.where(timestamps < pd.Timestamp("2023-07-09", tz="UTC"), "TRANSITION", "RECENT"))
    trend = rng.uniform(0, 28, rows)
    momentum = rng.uniform(0, 30, rows)
    volume = rng.uniform(0, 20, rows)
    structure = rng.uniform(0, 12, rows)
    risk = rng.uniform(0, 8, rows)
    regime_score = rng.uniform(-5, 5, rows)
    recent_shift = np.where(era == "RECENT", 8.0, 0.0)
    momentum_effect = np.where(era == "RECENT", -0.055 * momentum, 0.045 * momentum)
    returns = (
        0.035 * trend
        + momentum_effect
        + 0.015 * volume
        - 0.045 * risk
        + rng.normal(0, 0.45, rows)
        - 0.65
    )
    regimes = np.where(np.arange(rows) % 3 == 0, "BULL", np.where(np.arange(rows) % 3 == 1, "BEAR", "SIDEWAYS"))
    sides = np.where(np.arange(rows) % 2 == 0, "LONG", "SHORT")
    symbols = np.array(["BTC/USDT", "ETH/USDT", "SOL/USDT"])[np.arange(rows) % 3]
    score = trend + momentum + volume + structure + regime_score - risk + 20
    return pd.DataFrame(
        {
            "decision_id": [f"d{i}" for i in range(rows)],
            "candle_timestamp": timestamps,
            "symbol": symbols,
            "timeframe": "4h",
            "side": sides,
            "regime": regimes,
            "score": score,
            "trend_score": trend + recent_shift,
            "momentum_score": momentum,
            "volume_score": volume,
            "structure_score": structure,
            "regime_score": regime_score,
            "risk_penalty": risk,
            "net_signed_return_after_6c_pct": returns,
        }
    )


def config() -> FeatureDecayConfig:
    return FeatureDecayConfig(
        development_cutoff_utc="2026-07-09T12:00:00Z",
        minimum_era_samples=50,
        minimum_scope_samples=40,
        minimum_quantile_samples=10,
        association_tolerance=0.02,
        spread_tolerance_pct=0.03,
        decay_tolerance=0.04,
        components=(
            "trend_score",
            "momentum_score",
            "volume_score",
            "structure_score",
            "regime_score",
            "risk_penalty",
        ),
    )


def test_leakage_feature_names_are_rejected():
    with pytest.raises(ValueError):
        validate_feature_names(["trend_score", "future_return"])


def test_assign_eras_is_non_overlapping_and_cutoff_safe():
    frame = synthetic_replay(1200)
    extra = frame.tail(2).copy()
    extra["candle_timestamp"] = pd.to_datetime(["2026-07-10T00:00:00Z", "2026-07-11T00:00:00Z"])
    work, boundaries = assign_non_overlapping_eras(pd.concat([frame, extra], ignore_index=True), config())
    assert set(work["__era"].unique()) == {"LEGACY", "TRANSITION", "RECENT"}
    assert work["__timestamp"].max() <= pd.Timestamp("2026-07-09T12:00:00Z")
    assert boundaries["recent_start"].startswith("2023-07-09")
    assert work.groupby("decision_id")["__era"].nunique().max() == 1


def test_full_window_is_primary_and_nested_windows_are_not_concatenated():
    full = synthetic_replay(1000)
    frames = {"3Y": full.tail(300), "5Y": full.tail(600), "FULL": full}
    name, selected, warnings = select_longest_replay(frames)
    assert name == "FULL"
    assert len(selected) == len(full)
    assert not warnings


def test_component_decay_detects_recent_harmful_momentum_and_aligned_risk():
    work, _ = assign_non_overlapping_eras(synthetic_replay(), config())
    directional = work[work["side"].isin(["LONG", "SHORT"])]
    by_era = component_era_attribution(directional, config().components, config())
    summary = summarize_component_decay(by_era, config())
    momentum = summary[(summary["scope"] == "ALL") & (summary["component"] == "momentum_score")].iloc[0]
    risk = summary[(summary["scope"] == "ALL") & (summary["component"] == "risk_penalty")].iloc[0]
    assert momentum["status"] in {"RECENT_HARMFUL", "DECAYED"}
    assert momentum["recent_aligned_spearman"] < 0
    assert risk["recent_aligned_spearman"] > 0


def test_distribution_drift_detects_recent_shift():
    work, _ = assign_non_overlapping_eras(synthetic_replay(), config())
    directional = work[work["side"].isin(["LONG", "SHORT"])]
    drift = component_distribution_drift(directional, ["trend_score"], config())
    all_row = drift[(drift["scope"] == "ALL") & (drift["component"] == "trend_score")].iloc[0]
    assert all_row["psi"] > 0.10
    assert all_row["severity"] in {"MODERATE", "SEVERE"}


def test_score_decay_contains_frozen_gate_and_bands():
    work, _ = assign_non_overlapping_eras(synthetic_replay(1800), config())
    table = score_decay(work, config())
    assert "SCORE_GE_70" in set(table["segment"])
    assert any(str(value).startswith("BAND_") for value in table["segment"])
    assert set(table["era"]) == {"LEGACY", "TRANSITION", "RECENT"}


def test_analysis_is_diagnostic_only_and_deduplicates_decisions():
    full = synthetic_replay(2200)
    duplicated = pd.concat([full, full.tail(20)], ignore_index=True)
    report, artifacts = analyze_multi_cycle_feature_decay(
        {"FULL": duplicated, "3Y": full[full["candle_timestamp"] >= "2023-07-09"]},
        config(),
    )
    assert report.status in {"COMPLETE_NO_PROMOTION", "COMPLETE_WITH_INSUFFICIENT_ERAS"}
    assert report.promotion_applied is False
    assert report.paper_live_enabled is False
    assert report.rows_loaded == len(full)
    assert not artifacts.component_decay_summary.empty


def test_missing_replays_is_ready_not_promoted():
    report, artifacts = analyze_multi_cycle_feature_decay({}, config())
    assert report.status == "READY_AWAITING_MULTI_CYCLE_REPLAYS"
    assert report.promotion_applied is False
    assert artifacts.component_decay_summary.empty


def test_outputs_are_written(tmp_path: Path):
    full = synthetic_replay(2200)
    report, artifacts = analyze_multi_cycle_feature_decay({"FULL": full}, config())
    files = write_feature_decay_outputs(report, artifacts, tmp_path)
    assert Path(files["json"]).exists()
    assert Path(files["markdown"]).exists()
    assert Path(files["component_decay_summary"]).exists()
    assert "development diagnostic only" in Path(files["markdown"]).read_text(encoding="utf-8").lower()
