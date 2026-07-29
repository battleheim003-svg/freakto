from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from engine.artifact_protocols import (
    DEFAULT_ARTIFACT_SELECTOR,
    GLOBAL_UTC_PROFILE,
    GLOBAL_UTC_PROTOCOL,
    GLOBAL_UTC_SELECTOR,
    assign_global_utc_split,
    build_global_replay_manifest,
    global_utc_fingerprint,
    resolve_artifact_route,
    validate_global_replay_manifest,
    validate_global_utc_request,
    validate_v3_upstream_purge_metadata,
)
from engine.cost_aware_label_v2 import EventMetaLabelConfig, chronological_event_split
from engine.market_replay import MarketReplayConfig, _assign_replay_split
from engine.multi_cycle_archive import MultiCycleArchiveConfig, run_multi_cycle_archive
from engine.paper_readiness_v2 import build_paper_launch_readiness


V3_DIRS = (
    Path("logs/multi_cycle_archive_v3_global_utc"),
    Path("logs/event_opportunity_v3_global_utc"),
    Path("logs/cost_gate_diagnostics_v3_global_utc"),
)


def _valid_request(**overrides):
    values = {
        "protocol_id": GLOBAL_UTC_PROTOCOL,
        "profile_id": GLOBAL_UTC_PROFILE.profile_id,
        "window": "FULL",
        "symbols": ["SOL/USDT", "BTC/USDT", "ETH/USDT"],
        "timeframe": "4h",
        "cutoff_utc": "2026-07-09T12:00:00Z",
    }
    values.update(overrides)
    return values


def _v3_split_frame() -> pd.DataFrame:
    records = []
    groups = (
        ("TRAIN_60", "2023-01-01", 8),
        ("VALIDATION_20", "2023-02-01", 8),
        ("TEST_20", "2024-11-01", 8),
    )
    for label, start, count in groups:
        for index, timestamp in enumerate(pd.date_range(start, periods=count, freq="4h", tz="UTC")):
            records.append(
                {
                    "__timestamp": timestamp,
                    "decision_id": f"{label}-{index}",
                    "replay_split": label,
                    "split_protocol": GLOBAL_UTC_PROTOCOL,
                    "split_profile": GLOBAL_UTC_PROFILE.profile_id,
                    "purge_owner": "EVENT_PIPELINE",
                    "purge_applied": False,
                    "purge_timestamps": 6,
                    "purge_unit": "unique UTC timestamps",
                }
            )
    return pd.DataFrame(records)


def _v3_purge_manifest():
    return {
        "split_protocol": GLOBAL_UTC_PROTOCOL,
        "split_profile": GLOBAL_UTC_PROFILE.profile_id,
        "purge_owner": "EVENT_PIPELINE",
        "purge_applied": False,
        "purge_timestamps": 6,
        "purge_unit": "unique UTC timestamps",
        "canonical": False,
    }


def test_registry_defaults_to_v2_and_v3_is_disjoint_opt_in():
    v2 = resolve_artifact_route()
    v3 = resolve_artifact_route(GLOBAL_UTC_SELECTOR)
    assert v2.selector == DEFAULT_ARTIFACT_SELECTOR and v2.canonical is True
    assert v3.canonical is False
    assert {v2.replay_root, v2.event_root, v2.cost_root}.isdisjoint(
        {v3.replay_root, v3.event_root, v3.cost_root}
    )
    with pytest.raises(ValueError, match="unknown selector"):
        resolve_artifact_route("v3-typo")


@pytest.mark.parametrize(
    ("timestamp", "expected"),
    [
        ("2023-01-20T08:00:00Z", "TRAIN_60"),
        ("2023-01-20T12:00:00Z", "TRAIN_60"),
        ("2023-01-20T16:00:00Z", "VALIDATION_20"),
        ("2024-10-13T12:00:00Z", "VALIDATION_20"),
        ("2024-10-13T16:00:00Z", "TEST_20"),
    ],
)
def test_frozen_boundary_assignment(timestamp, expected):
    assert assign_global_utc_split(timestamp) == expected


def test_timestamp_contract_rejects_naive_and_normalizes_aware_values():
    with pytest.raises(ValueError, match="naive"):
        assign_global_utc_split("2023-01-20 16:00:00")
    assert assign_global_utc_split("2023-01-20T19:30:00+03:30") == "VALIDATION_20"
    with pytest.raises(ValueError, match="undefined boundary gap"):
        assign_global_utc_split("2023-01-20T14:00:00Z")


def test_profile_is_exact_but_symbol_order_is_not_semantic():
    assert validate_global_utc_request(**_valid_request()) == GLOBAL_UTC_PROFILE
    failures = (
        {"window": "3Y"},
        {"window": "5Y"},
        {"symbols": ["BTC/USDT", "ETH/USDT"]},
        {"symbols": ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT"]},
        {"timeframe": "1h"},
        {"cutoff_utc": "2026-07-09T08:00:00Z"},
        {"protocol_id": "other"},
        {"profile_id": "other"},
    )
    for mismatch in failures:
        with pytest.raises(ValueError, match="request mismatch"):
            validate_global_utc_request(**_valid_request(**mismatch))
    with pytest.raises(ValueError, match="frozen boundary mutation"):
        replace(GLOBAL_UTC_PROFILE, test_start_utc="2024-10-13T20:00:00Z").validate()


def test_multi_cycle_v3_rejects_non_full_before_any_output_is_written(tmp_path):
    output = tmp_path / "must-not-exist"
    with pytest.raises(ValueError, match="request mismatch"):
        run_multi_cycle_archive(
            MultiCycleArchiveConfig(
                windows=["3Y"],
                development_cutoff_utc=GLOBAL_UTC_PROFILE.research_cutoff_utc,
                output_dir=str(output),
                artifact_selector=GLOBAL_UTC_SELECTOR,
            )
        )
    assert not output.exists()


def test_cross_asset_labels_depend_only_on_global_timestamp():
    config = MarketReplayConfig(
        symbols=list(GLOBAL_UTC_PROFILE.symbols),
        end_utc=GLOBAL_UTC_PROFILE.research_cutoff_utc,
        artifact_selector=GLOBAL_UTC_SELECTOR,
        split_window="FULL",
        split_profile=GLOBAL_UTC_PROFILE.profile_id,
    )
    labels = {
        _assign_replay_split(config, timestamp="2024-10-13T16:00:00Z", position=position, total=999)
        for position in (0, 500, 998)
    }
    assert labels == {"TEST_20"}


def test_fingerprint_and_manifest_are_deterministic_and_complete():
    first = global_utc_fingerprint(source_fingerprints={"SOL/USDT": "c", "BTC/USDT": "a", "ETH/USDT": "b"})
    second = global_utc_fingerprint(source_fingerprints={"ETH/USDT": "b", "BTC/USDT": "a", "SOL/USDT": "c"})
    changed = global_utc_fingerprint(source_fingerprints={"ETH/USDT": "changed", "BTC/USDT": "a", "SOL/USDT": "c"})
    assert first == second and first != changed
    manifest = build_global_replay_manifest(
        source_fingerprints={"BTC/USDT": "a", "ETH/USDT": "b", "SOL/USDT": "c"},
        counts_by_split={"TRAIN_60": 3, "VALIDATION_20": 2, "TEST_20": 1},
        counts_by_symbol_and_split={"BTC/USDT": {"TRAIN_60": 1}},
        first_last_timestamp_by_split={"TRAIN_60": {"first": "x", "last": "y"}},
        cross_asset_timestamp_label_conflicts=0,
    )
    assert manifest["output_fingerprint"] == first
    assert manifest["purge_applied"] is False
    assert manifest["canonical"] is False
    assert manifest["cross_asset_timestamp_label_conflicts"] == 0


def test_manifest_reconciles_counts_and_rejects_mixed_labels():
    rows = pd.DataFrame(
        [
            {"symbol": symbol, "candle_timestamp": timestamp, "replay_split": label}
            for symbol in GLOBAL_UTC_PROFILE.symbols
            for timestamp, label in (
                ("2023-01-20T12:00:00Z", "TRAIN_60"),
                ("2023-01-20T16:00:00Z", "VALIDATION_20"),
                ("2024-10-13T16:00:00Z", "TEST_20"),
            )
        ]
    )
    counts = rows.groupby("replay_split").size().astype(int).to_dict()
    by_symbol = {
        str(symbol): group.groupby("replay_split").size().astype(int).to_dict()
        for symbol, group in rows.groupby("symbol")
    }
    first_last = {
        label: {
            "first": pd.Timestamp(group["candle_timestamp"].min()).isoformat(),
            "last": pd.Timestamp(group["candle_timestamp"].max()).isoformat(),
        }
        for label, group in rows.groupby("replay_split")
    }
    manifest = build_global_replay_manifest(
        source_fingerprints={"BTC/USDT": "a", "ETH/USDT": "b", "SOL/USDT": "c"},
        counts_by_split=counts,
        counts_by_symbol_and_split=by_symbol,
        first_last_timestamp_by_split=first_last,
        cross_asset_timestamp_label_conflicts=0,
    )
    validate_global_replay_manifest(manifest, rows)
    bad = rows.copy()
    bad.loc[len(bad)] = ["BTC/USDT", "2024-10-13T16:00:00Z", "VALIDATION_20"]
    with pytest.raises(ValueError, match="split counts|conflict"):
        validate_global_replay_manifest(manifest, bad)


def test_v3_event_split_applies_exact_downstream_purge_once():
    frame = _v3_split_frame()
    split = chronological_event_split(
        frame,
        EventMetaLabelConfig(
            artifact_selector=GLOBAL_UTC_SELECTOR,
            upstream_split_manifest=_v3_purge_manifest(),
            minimum_train_events=1,
            minimum_optimize_events=1,
            minimum_holdout_events=1,
        ),
    )
    assert len(split.train) == 8
    assert len(split.optimize) == 2
    assert len(split.holdout) == 2
    assert split.manifest["artifact_selector"] == GLOBAL_UTC_SELECTOR
    assert split.manifest["purge"]["train_to_optimize"]["unique_timestamps_removed"] == 6
    assert split.manifest["purge"]["optimize_to_holdout"]["unique_timestamps_removed"] == 6
    assert split.manifest["purge_applied"] is True


def test_multi_symbol_purge_is_by_unique_timestamp_not_row():
    base = _v3_split_frame()
    frame = pd.concat(
        [
            base.assign(symbol=symbol, decision_id=base["decision_id"] + "-" + symbol)
            for symbol in GLOBAL_UTC_PROFILE.symbols
        ],
        ignore_index=True,
    )
    split = chronological_event_split(
        frame,
        EventMetaLabelConfig(
            artifact_selector=GLOBAL_UTC_SELECTOR,
            upstream_split_manifest=_v3_purge_manifest(),
            minimum_train_events=1,
            minimum_optimize_events=1,
            minimum_holdout_events=1,
        ),
    )
    assert len(split.optimize) == 2 * len(GLOBAL_UTC_PROFILE.symbols)
    assert (
        split.manifest["purge"]["train_to_optimize"]["rows_removed"]
        == 6 * len(GLOBAL_UTC_PROFILE.symbols)
    )


def test_v3_missing_or_double_purge_metadata_fails_closed():
    frame = _v3_split_frame()
    validate_v3_upstream_purge_metadata(frame)
    with pytest.raises(ValueError, match="already applied"):
        validate_v3_upstream_purge_metadata(frame.assign(purge_applied=True))
    with pytest.raises(ValueError, match="missing v3 purge metadata"):
        validate_v3_upstream_purge_metadata(frame.drop(columns=["purge_owner"]))
    with pytest.raises(ValueError, match="upstream manifest is missing"):
        EventMetaLabelConfig(artifact_selector=GLOBAL_UTC_SELECTOR).validate()
    with pytest.raises(ValueError, match="manifest metadata mismatch"):
        EventMetaLabelConfig(
            artifact_selector=GLOBAL_UTC_SELECTOR,
            upstream_split_manifest={**_v3_purge_manifest(), "purge_applied": True},
        ).validate()


def test_v3_readiness_uses_candidate_roots_without_v2_fallback(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    readiness, _ = build_paper_launch_readiness(artifact_selector=GLOBAL_UTC_SELECTOR)
    assert readiness.research_collection_ready is False
    assert readiness.strategy_paper_ready is False
    assert any("Event universe is missing" in blocker for blocker in readiness.blockers)
    with pytest.raises(ValueError, match="do not match v3 roots"):
        build_paper_launch_readiness(
            event_dir="logs/mixed-event-root",
            cost_dir="logs/cost_gate_diagnostics_v3_global_utc",
            artifact_selector=GLOBAL_UTC_SELECTOR,
        )


def test_protocol_import_and_readiness_do_not_create_candidate_directories(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert all(not path.exists() for path in V3_DIRS)
