from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from engine.baseline_benchmarks import (
    BenchmarkConfig,
    analyze_feature_architecture_v2,
    block_bootstrap_expectancy_ci,
    select_longest_replay,
    strategy_metrics,
    walk_forward_architecture,
    write_benchmark_outputs,
)
from engine.feature_architecture_v2 import FeatureArchitectureV2Config
from tests.test_feature_architecture_v2 import synthetic_rows


def benchmark_config() -> BenchmarkConfig:
    architecture = FeatureArchitectureV2Config(
        development_cutoff_utc="2026-07-09T12:00:00Z",
        purge_timestamps=3,
        minimum_train_samples_per_side=100,
        minimum_optimize_samples=25,
        minimum_holdout_samples=40,
        structure_gate_min=4.0,
        expected_return_thresholds=(-0.1, 0.0, 0.1, 0.2),
    )
    return BenchmarkConfig(
        architecture=architecture,
        variants=("ARCH_V2_BASE", "ARCH_V2_NO_MOMENTUM", "ARCH_V2_LONG_ONLY"),
        walk_forward_folds=3,
        minimum_walk_forward_train_rows=300,
        minimum_walk_forward_test_rows=60,
        bootstrap_samples=60,
        bootstrap_block_size=12,
        promotion_min_samples=40,
    )


def test_strategy_metrics_handles_empty_and_profit_factor():
    empty = strategy_metrics([], total_rows=100)
    assert empty["sample_count"] == 0
    metrics = strategy_metrics([1.0, 1.0, -0.5], total_rows=10)
    assert metrics["sample_count"] == 3
    assert metrics["profit_factor"] == 4.0
    assert metrics["coverage"] == 0.3


def test_block_bootstrap_is_deterministic():
    values = np.linspace(-1, 1.5, 200)
    first = block_bootstrap_expectancy_ci(values, samples=50, block_size=10, seed=7)
    second = block_bootstrap_expectancy_ci(values, samples=50, block_size=10, seed=7)
    assert first == second
    assert first[0] <= np.mean(values) <= first[1]


def test_longest_replay_prefers_full_without_concatenation():
    full = synthetic_rows(1000)
    name, selected = select_longest_replay({"3Y": full.tail(300), "5Y": full.tail(600), "FULL": full})
    assert name == "FULL"
    assert len(selected) == 1000


def test_suite_compares_architecture_and_simple_baselines_on_same_holdout():
    report, artifacts = analyze_feature_architecture_v2({"FULL": synthetic_rows(1800)}, benchmark_config())
    assert report.status.startswith("COMPLETE_")
    assert {"ARCHITECTURE_V2", "SIMPLE_BASELINE"}.issubset(set(artifacts.holdout_benchmarks["family"]))
    assert "CHAMPION_SCORE_GE_70" in set(artifacts.holdout_benchmarks["strategy"])
    assert report.promotion_applied is False
    assert report.paper_live_enabled is False


def test_buy_hold_and_random_baselines_are_included_when_market_return_exists():
    _, artifacts = analyze_feature_architecture_v2({"FULL": synthetic_rows(1800)}, benchmark_config())
    names = set(artifacts.holdout_benchmarks["strategy"])
    assert "BUY_AND_HOLD" in names
    assert "RANDOM_DIRECTIONAL" in names


def test_candidate_manifest_never_promotes_runtime():
    report, artifacts = analyze_feature_architecture_v2({"FULL": synthetic_rows(1800)}, benchmark_config())
    manifest = artifacts.candidate_manifest
    assert manifest["fresh_oos_required"] is True
    assert manifest["promotion_applied"] is False
    assert manifest["paper_live_enabled"] is False
    assert manifest["score_used_as_feature"] is False
    assert report.fresh_oos_required is True


def test_threshold_candidates_are_recorded_for_both_sides():
    _, artifacts = analyze_feature_architecture_v2({"FULL": synthetic_rows(1800)}, benchmark_config())
    assert {"LONG", "SHORT"}.issubset(set(artifacts.threshold_candidates["side"]))
    assert artifacts.threshold_candidates["variant"].nunique() >= 2


def test_walk_forward_is_chronological_and_no_overlap():
    table = walk_forward_architecture(synthetic_rows(2200), "ARCH_V2_BASE", benchmark_config())
    assert not table.empty
    assert table["no_overlap"].all()
    assert set(table["fold"]).issubset({1, 2, 3})


def test_missing_replay_is_ready_and_not_promoted():
    report, artifacts = analyze_feature_architecture_v2({}, benchmark_config())
    assert report.status == "READY_AWAITING_MULTI_CYCLE_REPLAY"
    assert report.promotion_applied is False
    assert artifacts.holdout_benchmarks.empty


def test_outputs_are_written(tmp_path: Path):
    report, artifacts = analyze_feature_architecture_v2({"FULL": synthetic_rows(1800)}, benchmark_config())
    files = write_benchmark_outputs(report, artifacts, tmp_path)
    assert Path(files["json"]).exists()
    assert Path(files["markdown"]).exists()
    assert Path(files["candidate_manifest"]).exists()
    text = Path(files["markdown"]).read_text(encoding="utf-8").lower()
    assert "fresh oos" in text
    assert "promotion applied: `false`" in text


def test_frozen_candidate_evaluation_never_refits_or_reselects(tmp_path: Path):
    import joblib
    from engine.baseline_benchmarks import evaluate_frozen_candidate
    from engine.feature_architecture_v2 import (
        ThresholdSelection,
        chronological_development_split,
        fit_architecture_bundle,
        predict_architecture,
        select_side_threshold,
    )

    cfg = benchmark_config()
    split = chronological_development_split(synthetic_rows(1800), cfg.architecture)
    bundle = fit_architecture_bundle(split.train, "ARCH_V2_BASE", cfg.architecture)
    opt = predict_architecture(bundle, split.optimize)
    selections = {side: select_side_threshold(opt, side, cfg.architecture) for side in ("LONG", "SHORT")}
    # Fixed fallback thresholds keep the test independent of optimize eligibility.
    selections = {
        side: selection if selection.threshold is not None else ThresholdSelection(side, -999.0, True, "test fixed", selection.candidate_rows)
        for side, selection in selections.items()
    }
    payload = {
        "version": "2.0.0",
        "variant": "ARCH_V2_BASE",
        "bundle": bundle,
        "selections": selections,
        "long_only": False,
        "development_cutoff_utc": cfg.architecture.development_cutoff_utc,
    }
    model_path = tmp_path / "frozen.joblib"
    joblib.dump(payload, model_path)
    fresh = synthetic_rows(120)
    fresh["candle_timestamp"] = pd.date_range("2026-07-10", periods=len(fresh), freq="4h", tz="UTC")
    result, selected = evaluate_frozen_candidate(model_path, fresh)
    assert result["model_refit"] is False
    assert result["thresholds_reselected"] is False
    assert result["promotion_applied"] is False
    assert result["fresh_rows"] == len(fresh)
    assert len(selected) <= len(fresh)
