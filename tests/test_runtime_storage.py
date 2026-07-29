from __future__ import annotations

import json
from pathlib import Path

import pytest

from freakto.core.runtime import runtime_paths
from scripts.migrate_runtime_state import apply_plan, build_plan, main


def test_runtime_paths_default_outside_tracked_output_directories(tmp_path, monkeypatch):
    monkeypatch.delenv("FREAKTO_RUNTIME_ROOT", raising=False)
    paths = runtime_paths(tmp_path)
    assert paths.root == tmp_path / ".freakto-runtime"
    assert paths.logs == tmp_path / ".freakto-runtime" / "logs"


def test_runtime_paths_honor_explicit_external_root(tmp_path, monkeypatch):
    target = tmp_path / "external"
    monkeypatch.setenv("FREAKTO_RUNTIME_ROOT", str(target))
    assert runtime_paths(tmp_path / "project").root == target


def test_plan_inventory_and_copy_preserve_source(tmp_path):
    root = tmp_path / "project"
    destination = tmp_path / "runtime"
    source = root / "logs" / "paper"
    source.mkdir(parents=True)
    (source / "state.json").write_text('{"ok": true}', encoding="utf-8")
    plan = build_plan(root, destination)
    logs = next(item for item in plan if item.category == "runtime_logs")
    assert logs.files == 1 and logs.bytes > 0
    result = apply_plan(plan)
    assert (source / "state.json").exists()
    assert (destination / "logs" / "paper" / "state.json").exists()
    assert next(item for item in result if item.category == "runtime_logs").action == "COPIED"


def test_destination_collision_fails_closed(tmp_path):
    root = tmp_path / "project"
    (root / "logs").mkdir(parents=True)
    destination = tmp_path / "runtime"
    (destination / "logs").mkdir(parents=True)
    with pytest.raises(FileExistsError):
        apply_plan(build_plan(root, destination))


def test_cli_defaults_to_dry_run_and_writes_manifest(tmp_path):
    root = tmp_path / "project"
    (root / "history").mkdir(parents=True)
    (root / "history" / "signals.db").write_bytes(b"fixture")
    destination = tmp_path / "runtime"
    manifest = tmp_path / "manifest.json"
    assert main(["--root", str(root), "--destination", str(destination), "--manifest", str(manifest)]) == 0
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["mode"] == "dry-run"
    assert not destination.exists()
