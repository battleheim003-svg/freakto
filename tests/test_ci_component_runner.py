from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from scripts.ci_component_runner import run_component


def test_required_failure_propagates_and_is_reported(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "scripts.ci_component_runner.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=7, stdout="out", stderr="err"),
    )
    report = tmp_path / "components.json"
    assert run_component("core", "required", ["probe"], report) == 7
    record = json.loads(report.read_text(encoding="utf-8"))["components"][0]
    assert record["status"] == "FAILED" and record["exit_code"] == 7


def test_optional_failure_is_degraded_not_silently_passed(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "scripts.ci_component_runner.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=9, stdout="", stderr="diagnostic"),
    )
    report = tmp_path / "components.json"
    assert run_component("advisory", "optional", ["probe"], report) == 0
    record = json.loads(report.read_text(encoding="utf-8"))["components"][0]
    assert record["status"] == "DEGRADED" and record["exit_code"] == 9
    assert record["stderr_tail"] == "diagnostic"


def test_report_appends_component_results_atomically(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "scripts.ci_component_runner.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="ok", stderr=""),
    )
    report = tmp_path / "components.json"
    assert run_component("one", "required", ["probe"], report) == 0
    assert run_component("two", "optional", ["probe"], report) == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert [item["name"] for item in payload["components"]] == ["one", "two"]
    assert all(item["status"] == "PASSED" for item in payload["components"])


def test_github_summary_receives_visible_degraded_status(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "scripts.ci_component_runner.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout="", stderr=""),
    )
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    assert run_component("optional-check", "optional", ["probe"], tmp_path / "r.json") == 0
    text = summary.read_text(encoding="utf-8")
    assert "DEGRADED" in text and "optional-check" in text
