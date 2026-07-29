from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from freakto.paper import campaign
from freakto.paper.state_paths import atomic_write_json, paper_state_paths


def _campaign_state(status: str = "RUNNING", pid=42, **extra):
    return {
        "campaign_id": "paper-test",
        "status": status,
        "started_utc": "2026-07-01T00:00:00+00:00",
        "pid": pid,
        **extra,
    }


def test_dead_running_pid_is_atomically_recovered_once(tmp_path, monkeypatch):
    campaign.write_state(campaign.state_path(tmp_path), _campaign_state())
    monkeypatch.setattr(
        campaign,
        "_pid_liveness",
        lambda _pid: campaign.ProcessLiveness.DEAD,
    )
    now = datetime(2026, 7, 2, tzinfo=timezone.utc)

    first = campaign.campaign_status(tmp_path, now=now)
    recovered_at = first["recovered_at_utc"]
    second = campaign.campaign_status(tmp_path, now=now)

    assert first["status"] == "STALE_RECOVERED"
    assert first["previous_status"] == "RUNNING"
    assert first["recovery_reason"] == "STALE_PROCESS_NOT_FOUND"
    assert first["stale_pid"] == 42
    assert first["campaign_id"] == "paper-test"
    assert second["recovered_at_utc"] == recovered_at


def test_unknown_pid_does_not_trigger_recovery(tmp_path, monkeypatch):
    campaign.write_state(campaign.state_path(tmp_path), _campaign_state())
    monkeypatch.setattr(
        campaign,
        "_pid_liveness",
        lambda _pid: campaign.ProcessLiveness.UNKNOWN,
    )

    status = campaign.campaign_status(tmp_path)

    assert status["status"] == "RUNNING"
    assert status["process_liveness"] == "UNKNOWN"


def test_remote_host_pid_is_not_used_as_local_proof(tmp_path, monkeypatch):
    campaign.write_state(
        campaign.state_path(tmp_path),
        _campaign_state(worker_host="another-host"),
    )
    monkeypatch.setattr(
        campaign,
        "_pid_liveness",
        lambda _pid: pytest.fail("remote PID must not be probed"),
    )

    status = campaign.campaign_status(tmp_path)

    assert status["status"] == "RUNNING"
    assert status["process_identity"] == "REMOTE_HOST_UNVERIFIED"


@pytest.mark.parametrize("pid", [None, "", 0, -1, "not-a-pid"])
def test_invalid_running_pid_is_recovered(tmp_path, pid):
    campaign.write_state(campaign.state_path(tmp_path), _campaign_state(pid=pid))

    status = campaign.campaign_status(tmp_path)

    assert status["status"] == "STALE_RECOVERED"
    assert status["stale_pid"] == pid


def test_non_running_state_is_not_probed(tmp_path, monkeypatch):
    campaign.write_state(
        campaign.state_path(tmp_path),
        _campaign_state(status="STOPPED"),
    )
    monkeypatch.setattr(
        campaign,
        "_pid_liveness",
        lambda _pid: pytest.fail("non-running state must not be probed"),
    )

    assert campaign.campaign_status(tmp_path)["status"] == "STOPPED"


def test_canonical_only_resolution(tmp_path):
    path = paper_state_paths(tmp_path).canonical("heartbeat.json")
    path.parent.mkdir(parents=True)
    path.write_text('{"status":"WAITING"}', encoding="utf-8")

    resolution = paper_state_paths(tmp_path).resolve_for_read("heartbeat.json")

    assert resolution.path == path
    assert resolution.source == "CANONICAL"
    assert resolution.conflict is False


def test_legacy_only_fallback_does_not_delete_legacy(tmp_path):
    path = paper_state_paths(tmp_path).legacy("heartbeat.json")
    path.parent.mkdir(parents=True)
    path.write_text('{"status":"WAITING"}', encoding="utf-8")

    resolution = paper_state_paths(tmp_path).resolve_for_read("heartbeat.json")

    assert resolution.path == path
    assert resolution.source == "LEGACY_FALLBACK"
    assert path.exists()


def test_equal_dual_state_is_not_a_conflict(tmp_path):
    paths = paper_state_paths(tmp_path)
    for path in (paths.canonical("heartbeat.json"), paths.legacy("heartbeat.json")):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"same":true}', encoding="utf-8")

    resolution = paths.resolve_for_read("heartbeat.json")

    assert resolution.source == "CANONICAL"
    assert resolution.conflict is False


def test_conflicting_dual_state_surfaces_warning_without_merge(tmp_path):
    paths = paper_state_paths(tmp_path)
    paths.canonical_dir.mkdir(parents=True)
    paths.legacy_dir.mkdir(parents=True)
    paths.canonical("heartbeat.json").write_text('{"version":2}', encoding="utf-8")
    paths.legacy("heartbeat.json").write_text('{"version":1}', encoding="utf-8")

    resolution = paths.resolve_for_read("heartbeat.json")

    assert resolution.path == paths.canonical("heartbeat.json")
    assert resolution.conflict is True
    assert "without merging" in str(resolution.warning)


def test_malformed_canonical_does_not_silently_fall_back(tmp_path):
    paths = paper_state_paths(tmp_path)
    paths.canonical_dir.mkdir(parents=True)
    paths.legacy_dir.mkdir(parents=True)
    paths.canonical("heartbeat.json").write_text("{", encoding="utf-8")
    paths.legacy("heartbeat.json").write_text('{"valid":true}', encoding="utf-8")

    resolution = paths.resolve_for_read("heartbeat.json")

    assert resolution.path == paths.canonical("heartbeat.json")
    assert resolution.conflict is True


def test_history_reads_legacy_but_new_orchestrator_writes_canonical(tmp_path):
    legacy = paper_state_paths(tmp_path).legacy("cycle_history.jsonl")
    legacy.parent.mkdir(parents=True)
    legacy.write_text(
        json.dumps(
            {
                "started_utc": "2026-07-02T00:00:00+00:00",
                "status": "COMPLETE",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    campaign.write_state(campaign.state_path(tmp_path), _campaign_state(status="STOPPED"))

    status = campaign.campaign_status(
        tmp_path,
        now=datetime(2026, 7, 3, tzinfo=timezone.utc),
    )

    assert status["cycles"] == 1
    assert status["persistence_source"] == "LEGACY_FALLBACK"
    assert legacy.exists()


def test_atomic_write_preserves_previous_state_when_replace_fails(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    path.write_text('{"version":1}\n', encoding="utf-8")
    monkeypatch.setattr(
        "freakto.paper.state_paths.os.replace",
        lambda *_args: (_ for _ in ()).throw(OSError("replace failed")),
    )

    with pytest.raises(OSError, match="replace failed"):
        atomic_write_json(path, {"version": 2})

    assert path.read_text(encoding="utf-8") == '{"version":1}\n'
    assert not list(tmp_path.glob("*.tmp"))


def test_paths_are_root_based_not_cwd_based(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.chdir(other)

    paths = paper_state_paths(root)

    assert paths.canonical_dir == root.resolve() / "logs" / "paper_launch_v2"


@pytest.mark.parametrize(
    "value",
    [
        "2026-07-01T00:00:00Z",
        "2026-07-01T00:00:00+00:00",
        "2026-07-01T03:30:00+03:30",
    ],
)
def test_timestamp_parser_normalizes_aware_legacy_forms(value):
    parsed = campaign._parse_aware_timestamp(value)
    assert parsed.tzinfo == timezone.utc


def test_timestamp_parser_rejects_naive_legacy_value():
    with pytest.raises(ValueError, match="naive"):
        campaign._parse_aware_timestamp("2026-07-01T00:00:00")


def test_network_skips_are_excluded_from_strategy_success_rate(tmp_path):
    history = paper_state_paths(tmp_path).canonical("cycle_history.jsonl")
    history.parent.mkdir(parents=True)
    rows = [
        {"started_utc": "2026-07-01T01:00:00+00:00", "status": "COMPLETE"},
        {
            "started_utc": "2026-07-01T02:00:00+00:00",
            "status": "SKIPPED_DUE_TO_NETWORK",
        },
        {
            "started_utc": "2026-07-01T03:00:00+00:00",
            "status": "COMPLETE_WITH_STEP_FAILURES",
        },
    ]
    history.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    campaign.write_state(
        campaign.state_path(tmp_path),
        _campaign_state(status="STOPPED"),
    )

    status = campaign.campaign_status(
        tmp_path,
        now=datetime(2026, 7, 2, tzinfo=timezone.utc),
    )

    assert status["cycles"] == 3
    assert status["network_skipped_cycles"] == 1
    assert status["successful_cycles"] == 1
    assert status["failed_cycles"] == 1
    assert status["cycle_success_rate"] == 0.5
