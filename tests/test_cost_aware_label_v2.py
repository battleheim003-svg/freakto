from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from engine.cost_aware_label_v2 import (
    CostAwareLabelConfig,
    EventMetaLabelConfig,
    MetaThresholdSelection,
    apply_meta_threshold,
    build_cost_aware_labels,
    chronological_event_split,
    evaluate_frozen_event_candidate,
    event_family_benchmarks,
    event_meta_coefficients,
    fit_event_meta_model,
    predict_event_meta,
    select_meta_threshold,
    walk_forward_event_meta,
)
from engine.event_opportunity_benchmarks import (
    analyze_event_opportunity_universe,
    write_event_opportunity_outputs,
)
from engine.event_opportunity_universe import EventUniverseConfig, build_event_opportunity_universe
from tests.test_event_opportunity_universe import synthetic_event_rows


def config() -> EventMetaLabelConfig:
    return EventMetaLabelConfig(
        event=EventUniverseConfig(
            development_cutoff_utc="2026-07-09T12:00:00Z",
            volatility_lookback=10,
            minimum_target_to_cost=1.5,
            minimum_net_reward_risk=0.4,
        ),
        label=CostAwareLabelConfig(horizon_candles=6),
        purge_timestamps=3,
        minimum_train_events=100,
        minimum_optimize_events=25,
        minimum_holdout_events=40,
        optimize_min_samples=10,
        minimum_walk_forward_train_events=100,
        minimum_walk_forward_test_events=20,
        bootstrap_samples=50,
        bootstrap_block_size=10,
        promotion_min_samples=40,
    )


def labeled_rows(rows: int = 1800) -> pd.DataFrame:
    events, _ = build_event_opportunity_universe(synthetic_event_rows(rows), config().event)
    return build_cost_aware_labels(events, config().label)


def test_triple_barrier_resolves_ambiguity_stop_first():
    events, _ = build_event_opportunity_universe(synthetic_event_rows(100), config().event)
    events = events.head(1).copy()
    events["target_1_hit"] = True
    events["stop_hit"] = True
    events["intrabar_ambiguity"] = True
    labels = build_cost_aware_labels(events, config().label)
    assert labels.iloc[0]["triple_barrier_label"] == "STOP_LOSS"
    assert labels.iloc[0]["realized_net_return_pct"] < 0


def test_target_and_stop_returns_include_round_trip_cost():
    events, _ = build_event_opportunity_universe(synthetic_event_rows(100), config().event)
    sample = pd.concat([events.head(1), events.head(1)], ignore_index=True)
    sample["target_1_hit"] = [True, False]
    sample["stop_hit"] = [False, True]
    sample["intrabar_ambiguity"] = False
    sample["first_exit_reason"] = ["TARGET_1", "STOP"]
    labels = build_cost_aware_labels(sample, config().label)
    assert labels.loc[0, "realized_net_return_pct"] == labels.loc[0, "target_distance_pct"] - labels.loc[0, "event_execution_cost_pct"]
    assert labels.loc[1, "realized_net_return_pct"] == -labels.loc[1, "stop_distance_pct"] - labels.loc[1, "event_execution_cost_pct"]


def test_time_exit_uses_fixed_horizon_net_return():
    events, _ = build_event_opportunity_universe(synthetic_event_rows(100), config().event)
    sample = events.head(1).copy()
    sample["target_1_hit"] = False
    sample["stop_hit"] = False
    sample["first_exit_reason"] = "TIME"
    sample["net_signed_return_after_6c_pct"] = 0.42
    labels = build_cost_aware_labels(sample, config().label)
    assert labels.iloc[0]["triple_barrier_label"] == "TIME_EXIT"
    assert labels.iloc[0]["realized_net_return_pct"] == 0.42


def test_meta_label_compares_trade_with_no_trade_after_cost():
    labels = labeled_rows(300)
    assert labels["no_trade_return_pct"].eq(0).all()
    assert labels["meta_label"].equals(labels["realized_net_return_pct"].gt(0).astype(int))
    assert labels["label_is_cost_aware"].all()


def test_chronological_split_has_purge_and_no_overlap():
    split = chronological_event_split(labeled_rows(1200), config())
    assert split.train["__timestamp"].max() < split.optimize["__timestamp"].min()
    assert split.optimize["__timestamp"].max() < split.holdout["__timestamp"].min()
    assert split.boundaries["purge_timestamps"] == "3"


def test_meta_model_predicts_probability_and_expected_value():
    split = chronological_event_split(labeled_rows(), config())
    model = fit_event_meta_model(split.train, config())
    predictions = predict_event_meta(model, split.optimize)
    assert predictions["predicted_meta_probability"].between(0, 1).all()
    assert predictions["predicted_event_ev_pct"].notna().all()
    assert model.train_rows >= config().minimum_train_events


def test_threshold_is_selected_on_optimize_and_applied_to_holdout():
    split = chronological_event_split(labeled_rows(), config())
    model = fit_event_meta_model(split.train, config())
    optimize = predict_event_meta(model, split.optimize)
    selection = select_meta_threshold(optimize, config())
    holdout = predict_event_meta(model, split.holdout)
    selected = apply_meta_threshold(holdout, selection)
    assert selection.candidate_rows
    assert set(selected.index).issubset(set(holdout.index))
    if selection.eligible:
        assert selected["predicted_meta_probability"].ge(selection.threshold).all()


def test_model_coefficients_are_exportable():
    split = chronological_event_split(labeled_rows(), config())
    model = fit_event_meta_model(split.train, config())
    table = event_meta_coefficients(model)
    assert not table.empty
    assert {"feature", "coefficient"}.issubset(table.columns)
    assert np.isfinite(table["coefficient"]).all()


def test_event_family_benchmarks_include_cost_gated_variants():
    table = event_family_benchmarks(labeled_rows(600), scope="TEST")
    assert not table.empty
    assert "EVENT_ANY" in set(table["strategy"])
    assert "EVENT_COST_GATED" in set(table["strategy"])
    assert table["strategy"].str.endswith("_COST_GATED").any()


def test_walk_forward_is_chronological_and_fail_closed():
    table = walk_forward_event_meta(labeled_rows(1800), config())
    assert not table.empty
    assert table["no_overlap"].all()
    assert set(table["fold"]).issubset({1, 2, 3})


def test_full_suite_includes_no_trade_and_never_promotes_runtime():
    report, artifacts = analyze_event_opportunity_universe({"FULL": synthetic_event_rows(1800)}, config())
    assert report.status.startswith("COMPLETE_")
    assert "NO_TRADE" in set(artifacts.holdout_benchmarks["strategy"])
    assert "ALL_DIRECTIONAL" in set(artifacts.holdout_benchmarks["strategy"])
    assert "EVENT_META_LABEL_V2" in set(artifacts.holdout_benchmarks["strategy"])
    assert report.promotion_applied is False
    assert report.paper_live_enabled is False
    assert artifacts.candidate_manifest["event_detection_uses_outcomes"] is False


def test_missing_replay_is_ready_and_not_promoted():
    report, artifacts = analyze_event_opportunity_universe({}, config())
    assert report.status == "READY_AWAITING_MULTI_CYCLE_REPLAY"
    assert report.promotion_applied is False
    assert artifacts.holdout_benchmarks.empty


def test_outputs_are_written(tmp_path: Path):
    report, artifacts = analyze_event_opportunity_universe({"FULL": synthetic_event_rows(1800)}, config())
    files = write_event_opportunity_outputs(report, artifacts, tmp_path)
    assert Path(files["json"]).exists()
    assert Path(files["markdown"]).exists()
    assert Path(files["candidate_manifest"]).exists()
    text = Path(files["markdown"]).read_text(encoding="utf-8").lower()
    assert "no result authorizes runtime promotion" in text
    assert "paper/live enabled: `false`" in text


def test_frozen_candidate_evaluation_never_refits_or_reselects(tmp_path: Path):
    cfg = config()
    labels = labeled_rows(1800)
    split = chronological_event_split(labels, cfg)
    model = fit_event_meta_model(split.train, cfg)
    selection = MetaThresholdSelection(-1.0, True, "fixed test threshold", [])
    path = tmp_path / "frozen_event.joblib"
    joblib.dump({"version": "2.0.0", "model": model, "selection": selection, "config": cfg}, path)
    fresh = synthetic_event_rows(300)
    fresh["candle_timestamp"] = pd.date_range("2026-07-10", periods=len(fresh), freq="4h", tz="UTC")
    result, selected = evaluate_frozen_event_candidate(path, fresh)
    assert result["model_refit"] is False
    assert result["thresholds_reselected"] is False
    assert result["promotion_applied"] is False
    assert len(selected) <= result["fresh_event_rows"]
