from pathlib import Path

import pandas as pd
import pytest

from engine.exit_policy_audit import (
    ExitPolicyAuditConfig,
    load_exit_audit_dataset,
    run_exit_policy_audit,
)


def _rows(run_id: str, count: int, start: str, positive: bool = False) -> pd.DataFrame:
    timestamps = pd.date_range(start, periods=count, freq="4h", tz="UTC")
    gross = 0.15 if positive else 0.10
    net = -0.20 if not positive else 0.05
    rows = []
    for index, timestamp in enumerate(timestamps):
        side = "LONG" if index % 2 == 0 else "SHORT"
        ambiguous = index == 3
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
            "stop_zone": "95" if side == "LONG" else "105",
            "targets": '["104", "108", "112"]' if side == "LONG" else '["96", "92", "88"]',
            "fee_bps_per_side": 10.0,
            "slippage_bps_per_side": 5.0,
            "target_1_hit": index % 3 != 0,
            "target_2_hit": False,
            "target_3_hit": False,
            "stop_hit": index % 3 == 0,
            "first_exit_reason": "STOP_FIRST_CONSERVATIVE_AMBIGUOUS" if ambiguous else ("TARGET_1" if index % 3 else "STOP"),
            "first_exit_candle_offset": 1,
            "intrabar_ambiguity": ambiguous,
            "mfe_pct": 1.0,
            "mae_pct": -1.0,
            "win": net > 0,
            "direction_correct": gross > 0,
            "target_hit": index % 3 != 0,
            "outcome_label": "WIN" if net > 0 else "LOSS",
            "net_return_pct": net,
            "adaptive_horizon_candles": 6,
            "adaptive_gross_return_pct": gross,
            "adaptive_net_return_pct": net,
            "gross_signed_return_after_1c_pct": gross,
            "net_signed_return_after_1c_pct": net,
            "gross_signed_return_after_3c_pct": gross,
            "net_signed_return_after_3c_pct": net,
            "gross_signed_return_after_6c_pct": gross,
            "net_signed_return_after_6c_pct": net,
            "gross_signed_return_after_12c_pct": gross,
            "net_signed_return_after_12c_pct": net,
        })
    return pd.DataFrame(rows)


def _write_dataset(path: Path, *, count: int = 60) -> None:
    old = _rows("market_replay_20260101_000000", count, "2024-01-01")
    latest = _rows("market_replay_20260102_000000", count, "2025-01-01")
    pd.concat([old, latest], ignore_index=True).to_csv(path, index=False)


def test_loader_selects_latest_run_and_deduplicates(tmp_path: Path):
    source = tmp_path / "replay.csv"
    _write_dataset(source, count=20)
    config = ExitPolicyAuditConfig(minimum_total_rows=10, minimum_policy_rows=5)
    frame, metadata, warnings = load_exit_audit_dataset(source, config=config)
    assert metadata["selected_run_id"] == "market_replay_20260102_000000"
    assert len(frame) == 20
    assert any("ignored 1 older runs" in warning for warning in warnings)


def test_loader_rejects_missing_trade_geometry(tmp_path: Path):
    source = tmp_path / "bad.csv"
    pd.DataFrame({"side": ["LONG"], "candle_timestamp": ["2025-01-01"]}).to_csv(source, index=False)
    config = ExitPolicyAuditConfig(minimum_total_rows=1, minimum_policy_rows=1)
    with pytest.raises(ValueError, match="missing required columns"):
        load_exit_audit_dataset(source, config=config)


def test_audit_is_research_only_and_writes_all_artifacts(tmp_path: Path):
    source = tmp_path / "replay.csv"
    output = tmp_path / "out"
    _write_dataset(source, count=60)
    config = ExitPolicyAuditConfig(
        minimum_total_rows=20,
        minimum_policy_rows=20,
        minimum_positive_stability_folds=3,
    )
    result, artifacts = run_exit_policy_audit(source, output_dir=output, config=config)
    assert result.mode == "RESEARCH_AUDIT_ONLY"
    assert result.policy_change_applied is False
    assert result.paper_live_enabled is False
    assert result.recommended_policy is None
    assert not artifacts.policy_summary.empty
    for path in result.output_files.values():
        assert Path(path).exists()


def test_audit_reports_gross_positive_net_negative_cost_drag(tmp_path: Path):
    source = tmp_path / "replay.csv"
    output = tmp_path / "out"
    _write_dataset(source, count=60)
    config = ExitPolicyAuditConfig(minimum_total_rows=20, minimum_policy_rows=20)
    _, artifacts = run_exit_policy_audit(source, output_dir=output, config=config)
    all_scope = artifacts.cost_drag[artifacts.cost_drag["scope"].eq("ALL_DIRECTIONAL")]
    assert all_scope["gross_positive_net_negative"].astype(bool).all()
    assert (all_scope["execution_cost_drag"] > 0).all()


def test_label_consistency_keeps_target_hit_distinct_from_win(tmp_path: Path):
    source = tmp_path / "replay.csv"
    output = tmp_path / "out"
    _write_dataset(source, count=60)
    config = ExitPolicyAuditConfig(minimum_total_rows=20, minimum_policy_rows=20)
    _, artifacts = run_exit_policy_audit(source, output_dir=output, config=config)
    lookup = artifacts.label_consistency.set_index("diagnostic")["count"].to_dict()
    assert lookup["TARGET_1_HIT_BUT_CANONICAL_NET_LOSS"] > 0
    assert lookup["RECORDED_WIN_DISAGREES_WITH_CANONICAL_NET_SIGN"] == 0


def test_ambiguity_sensitivity_is_explicitly_reported(tmp_path: Path):
    source = tmp_path / "replay.csv"
    output = tmp_path / "out"
    _write_dataset(source, count=60)
    config = ExitPolicyAuditConfig(minimum_total_rows=20, minimum_policy_rows=20)
    _, artifacts = run_exit_policy_audit(source, output_dir=output, config=config)
    assert len(artifacts.ambiguity_sensitivity) == 4
    assert (artifacts.ambiguity_sensitivity["ambiguous_rows"] == 1).all()
    assert (artifacts.ambiguity_sensitivity["target_first_expectancy"] > artifacts.ambiguity_sensitivity["stop_first_expectancy"]).all()
