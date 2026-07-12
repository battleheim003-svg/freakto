from pathlib import Path

import pandas as pd
import pytest

from engine.execution_cost_optimizer import (
    ExecutionGeometryConfig,
    chronological_split,
    generate_candidates,
    optimize_execution_geometry,
    run_execution_geometry_optimizer,
)
from engine.trade_geometry import derive_geometry_features


def _rows(run_id: str, count: int, start: str, *, profitable: bool = True) -> pd.DataFrame:
    timestamps = pd.date_range(start, periods=count, freq="4h", tz="UTC")
    rows = []
    for index, timestamp in enumerate(timestamps):
        side = "LONG" if index % 2 == 0 else "SHORT"
        win = profitable and (index % 4 != 3)
        rows.append({
            "run_id": run_id,
            "decision_id": f"{run_id}-{index}",
            "candle_timestamp": timestamp.isoformat(),
            "side": side,
            "score": 75,
            "symbol": "BTC/USDT",
            "timeframe": "4h",
            "regime_label": "TRENDING_BULL" if side == "LONG" else "TRENDING_BEAR",
            "evaluation_status": "COMPLETE",
            "entry_price": 100.0,
            "stop_zone": "98" if side == "LONG" else "102",
            "targets": '["103", "106", "109"]' if side == "LONG" else '["97", "94", "91"]',
            "fee_bps_per_side": 2.0,
            "slippage_bps_per_side": 1.0,
            "round_trip_cost_pct": 0.06,
            "target_1_hit": win,
            "target_2_hit": False,
            "target_3_hit": False,
            "stop_hit": not win,
            "first_exit_reason": "TARGET_1" if win else "STOP",
            "first_exit_candle_offset": 1,
            "intrabar_ambiguity": False,
            "mfe_pct": 3.5 if win else 0.4,
            "mae_pct": -0.4 if win else -2.5,
            "win": win,
            "direction_correct": win,
            "target_hit": win,
            "outcome_label": "WIN" if win else "LOSS",
            "net_return_pct": 0.5 if win else -0.5,
            "adaptive_horizon_candles": 6,
            "adaptive_gross_return_pct": 0.6 if win else -0.4,
            "adaptive_net_return_pct": 0.54 if win else -0.46,
            "gross_signed_return_after_1c_pct": 0.5 if win else -0.5,
            "net_signed_return_after_1c_pct": 0.44 if win else -0.56,
            "gross_signed_return_after_3c_pct": 0.5 if win else -0.5,
            "net_signed_return_after_3c_pct": 0.44 if win else -0.56,
            "gross_signed_return_after_6c_pct": 0.5 if win else -0.5,
            "net_signed_return_after_6c_pct": 0.44 if win else -0.56,
            "gross_signed_return_after_12c_pct": 0.5 if win else -0.5,
            "net_signed_return_after_12c_pct": 0.44 if win else -0.56,
        })
    return pd.DataFrame(rows)


def _config(**overrides) -> ExecutionGeometryConfig:
    values = dict(
        horizons=(6,),
        stop_multipliers=(1.0,),
        reward_risks=(1.5,),
        minimum_target_cost_multiples=(1.0,),
        maximum_cost_to_risks=(1.0,),
        minimum_net_reward_risks=(0.5,),
        minimum_scores=(0,),
        scopes=("ALL",),
        management_policies=("NONE",),
        train_fraction=0.50,
        optimize_fraction=0.25,
        purge_candles=6,
        minimum_total_rows=40,
        minimum_train_rows=10,
        minimum_optimize_rows=8,
        minimum_holdout_rows=8,
        minimum_walk_forward_pass_rate=0.5,
        walk_forward_folds=2,
        maximum_candidate_drawdown_multiple=10.0,
    )
    values.update(overrides)
    return ExecutionGeometryConfig(**values)


def test_chronological_split_has_purged_non_overlapping_timestamps():
    frame = _rows("run", 100, "2025-01-01")
    frame["_event_time"] = pd.to_datetime(frame["candle_timestamp"], utc=True)
    masks, summary = chronological_split(frame, _config())
    train_max = frame.loc[masks["TRAIN"], "_event_time"].max()
    optimize_min = frame.loc[masks["OPTIMIZE"], "_event_time"].min()
    optimize_max = frame.loc[masks["OPTIMIZE"], "_event_time"].max()
    holdout_min = frame.loc[masks["HOLDOUT"], "_event_time"].min()
    assert train_max < optimize_min
    assert optimize_max < holdout_min
    assert summary["purge_candles"] == 6


def test_candidate_generation_is_deterministic_and_bounded():
    candidates = list(generate_candidates(_config()))
    assert len(candidates) == 1
    assert candidates[0].candidate_id == list(generate_candidates(_config()))[0].candidate_id


def test_optimizer_selection_does_not_depend_on_holdout_outcomes():
    frame = _rows("run", 120, "2025-01-01", profitable=True)
    frame["_event_time"] = pd.to_datetime(frame["candle_timestamp"], utc=True)
    frame = derive_geometry_features(frame)
    selected_a, _, _ = optimize_execution_geometry(frame, _config())

    masks, _ = chronological_split(frame, _config())
    changed = frame.copy()
    changed.loc[masks["HOLDOUT"], "mfe_pct"] = 0.0
    changed.loc[masks["HOLDOUT"], "mae_pct"] = -10.0
    selected_b, _, _ = optimize_execution_geometry(changed, _config())
    assert selected_a is not None
    assert selected_b is not None
    assert selected_a.candidate_id == selected_b.candidate_id


def test_optimizer_fails_closed_when_development_has_no_edge():
    frame = _rows("run", 120, "2025-01-01", profitable=False)
    frame["_event_time"] = pd.to_datetime(frame["candle_timestamp"], utc=True)
    frame = derive_geometry_features(frame)
    selected, artifacts, diagnostics = optimize_execution_geometry(frame, _config())
    assert selected is None
    assert diagnostics["development_eligible_candidates"] == 0
    assert not artifacts.candidate_summary.empty


def test_full_run_is_research_only_and_writes_artifacts(tmp_path: Path):
    source = tmp_path / "replay.csv"
    output = tmp_path / "out"
    old = _rows("market_replay_20260101_000000", 120, "2024-01-01")
    latest = _rows("market_replay_20260102_000000", 120, "2025-01-01")
    pd.concat([old, latest], ignore_index=True).to_csv(source, index=False)
    result, artifacts = run_execution_geometry_optimizer(
        source, output_dir=output, config=_config()
    )
    assert result.mode == "RESEARCH_OPTIMIZATION_ONLY"
    assert result.promotion_applied is False
    assert result.paper_live_enabled is False
    assert result.selected_run_id == "market_replay_20260102_000000"
    assert result.status == "PASS"
    assert result.recommended_policy is not None
    assert not artifacts.holdout_summary.empty
    for path in result.output_files.values():
        assert Path(path).exists()


def test_full_run_blocks_failed_holdout_without_changing_runtime(tmp_path: Path):
    source = tmp_path / "replay.csv"
    output = tmp_path / "out"
    frame = _rows("market_replay_20260102_000000", 120, "2025-01-01")
    # Development remains profitable; final quarter is forced to lose.
    frame.loc[90:, "mfe_pct"] = 0.0
    frame.loc[90:, "mae_pct"] = -3.0
    frame.to_csv(source, index=False)
    result, _ = run_execution_geometry_optimizer(source, output_dir=output, config=_config())
    assert result.status == "FAIL"
    assert result.selected_candidate is not None
    assert result.recommended_policy is None
    assert result.promotion_applied is False


def test_config_rejects_nonconservative_promotion_path():
    with pytest.raises(ValueError, match="STOP_FIRST"):
        _config(path_assumption="MANAGEMENT_FIRST").validate()


def test_path_managed_candidates_are_marked_diagnostic_only():
    frame = _rows("run", 120, "2025-01-01", profitable=True)
    frame["_event_time"] = pd.to_datetime(frame["candle_timestamp"], utc=True)
    frame = derive_geometry_features(frame)
    config = _config(management_policies=("NONE", "TRAILING"), management_shortlist=1)
    _, artifacts, _ = optimize_execution_geometry(frame, config)
    managed = artifacts.candidate_summary[
        artifacts.candidate_summary["geometry.management_policy"].eq("TRAILING")
    ]
    assert not managed.empty
    assert not managed["path_promotion_eligible"].astype(bool).any()
