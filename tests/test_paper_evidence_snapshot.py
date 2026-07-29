from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from freakto.paper.evidence_snapshot import (
    EVIDENCE_SOURCES,
    EvidenceSnapshotError,
    create_evidence_snapshot,
)
from freakto.paper.service import EXIT_BLOCKED, EXIT_OK, PaperService


FIXED_TIME = datetime(2026, 7, 27, 12, 30, tzinfo=timezone.utc)


def prepare_required(root):
    state = root / ".freakto-runtime" / "paper-campaign" / "state.json"
    policy = root / "config" / "paper_go_live_policy.json"
    state.parent.mkdir(parents=True)
    policy.parent.mkdir(parents=True)
    state.write_text(json.dumps({"campaign_id": "paper-test"}), encoding="utf-8")
    policy.write_text(json.dumps({"policy_version": "test-v1"}), encoding="utf-8")
    return state, policy


def test_snapshot_contains_only_allowlisted_evidence_with_verified_hashes(tmp_path):
    state, policy = prepare_required(tmp_path)
    history = tmp_path / "logs" / "paper_cycle" / "cycle_history.jsonl"
    history.parent.mkdir(parents=True)
    history.write_text('{"status":"COMPLETE"}\n', encoding="utf-8")
    secret = tmp_path / ".env"
    secret.write_text("API_SECRET=must-not-leak", encoding="utf-8")
    unrelated = tmp_path / "logs" / "paper_cycle" / "debug-secret.log"
    unrelated.write_text("must-not-leak", encoding="utf-8")
    before = {path: path.read_bytes() for path in (state, policy, history, secret, unrelated)}

    result = create_evidence_snapshot(tmp_path, generated_at=FIXED_TIME)

    archive_path = tmp_path / ".freakto-runtime" / "campaign-backups" / (
        "paper-test-evidence-20260727T123000.000000Z.zip"
    )
    assert result["archive"] == str(archive_path)
    assert result["status"] == "SNAPSHOT_CREATED"
    assert result["live_orders_enabled"] is False
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        assert names == {
            ".freakto-runtime/paper-campaign/state.json",
            "config/paper_go_live_policy.json",
            "logs/paper_cycle/cycle_history.jsonl",
            "manifest.json",
        }
        assert ".env" not in names
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["contains_secrets"] is False
        for item in manifest["files"]:
            payload = archive.read(item["path"])
            assert item["sha256"] == hashlib.sha256(payload).hexdigest()
            assert item["size_bytes"] == len(payload)

    assert result["archive_sha256"] == hashlib.sha256(archive_path.read_bytes()).hexdigest()
    checksum = archive_path.with_suffix(".zip.sha256").read_text(encoding="ascii")
    assert checksum == f'{result["archive_sha256"]}  {archive_path.name}\n'
    assert {path: path.read_bytes() for path in before} == before


def test_snapshot_fails_closed_when_required_evidence_is_missing(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "paper_go_live_policy.json").write_text("{}", encoding="utf-8")

    with pytest.raises(EvidenceSnapshotError, match="state.json"):
        create_evidence_snapshot(tmp_path, generated_at=FIXED_TIME)

    assert not (tmp_path / ".freakto-runtime" / "campaign-backups").exists()


def test_snapshot_refuses_to_overwrite_an_existing_destination(tmp_path):
    prepare_required(tmp_path)
    first = create_evidence_snapshot(tmp_path, generated_at=FIXED_TIME)

    with pytest.raises(EvidenceSnapshotError, match="already exists"):
        create_evidence_snapshot(tmp_path, generated_at=FIXED_TIME)

    assert len(list((tmp_path / ".freakto-runtime" / "campaign-backups").glob("*.zip"))) == 1
    assert first["archive_sha256"] == hashlib.sha256(
        Path(first["archive"]).read_bytes()
    ).hexdigest()


def test_default_allowlist_never_names_secret_files():
    paths = {source.relative_path.lower() for source in EVIDENCE_SOURCES}
    assert not any(".env" in path or "secret" in path or "credential" in path for path in paths)


def test_campaign_snapshot_service_returns_blocked_instead_of_partial_archive(tmp_path):
    service = PaperService(tmp_path, lambda *_: 0, readiness_loader=lambda: None)

    code, blocked = service.execute("campaign-snapshot")
    assert code == EXIT_BLOCKED
    assert blocked["status"] == "SNAPSHOT_BLOCKED"

    prepare_required(tmp_path)
    code, created = service.execute("campaign-snapshot")
    assert code == EXIT_OK
    assert created["status"] == "SNAPSHOT_CREATED"
