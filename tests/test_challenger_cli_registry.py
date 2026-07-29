from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

import champion_challenger_analysis as challenger_cli
from engine.champion_challenger import (
    ChampionChallengerArtifacts,
    ChampionChallengerResult,
)
from engine.experiment_registry import ExperimentRegistry


def _result(dataset: Path, output: Path) -> tuple[ChampionChallengerResult, ChampionChallengerArtifacts]:
    output.mkdir(parents=True)
    report = output / "champion_challenger_report.json"
    report.write_text("{}", encoding="utf-8")
    return (
        ChampionChallengerResult(
            created_utc="2026-07-27T00:00:00+00:00",
            version="test",
            challenger_version="test",
            status="PASS_RESEARCH_ONLY",
            dataset_path=str(dataset),
            dataset_sha256="fixture",
            selected_run_id=None,
            rows_loaded=100,
            rows_usable=100,
            output_files={"report_json": str(report)},
        ),
        ChampionChallengerArtifacts(summary=pd.DataFrame()),
    )


def test_challenger_cli_claims_holdout_once_and_records_ineligible_scope(
    monkeypatch, tmp_path: Path, capsys
):
    dataset = tmp_path / "replay.csv"
    dataset.write_text("timestamp,side\n2026-01-01T00:00:00Z,LONG\n", encoding="utf-8")
    output = tmp_path / "outputs"
    registry_path = tmp_path / "registry.sqlite3"
    calls: list[Path] = []

    def fake_run(source, *, output_dir, **_kwargs):
        calls.append(Path(output_dir))
        return _result(Path(source), Path(output_dir))

    monkeypatch.setattr(challenger_cli, "run_champion_challenger", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "champion_challenger_analysis.py",
            "--dataset",
            str(dataset),
            "--output-dir",
            str(output),
            "--registry-path",
            str(registry_path),
            "--experiment-id",
            "challenger-one",
        ],
    )

    assert challenger_cli.main() == 0
    first_output = capsys.readouterr().out
    assert "Official evidence         : False" in first_output
    run = ExperimentRegistry(registry_path).get_run("challenger-one")
    assert run is not None
    assert run.status == "COMPLETED"
    assert run.hyperparameters["official_evidence_eligible"] is False
    assert run.results["official_evidence_eligible"] is False
    assert calls == [output / "challenger-one"]

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "champion_challenger_analysis.py",
            "--dataset",
            str(dataset),
            "--output-dir",
            str(output),
            "--registry-path",
            str(registry_path),
            "--experiment-id",
            "challenger-two",
        ],
    )

    assert challenger_cli.main() == 2
    blocked_output = capsys.readouterr().out
    assert "HOLDOUT_ALREADY_CONSUMED" in blocked_output
    blocked = ExperimentRegistry(registry_path).get_run("challenger-two")
    assert blocked is not None
    assert blocked.status == "BLOCKED"
    assert blocked.results["official_evidence_eligible"] is False
    assert calls == [output / "challenger-one"]
