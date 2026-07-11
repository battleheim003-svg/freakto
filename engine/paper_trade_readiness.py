"""Fail-closed preflight for starting new paper trades."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import pandas as pd

from engine.model_contract import CURRENT_MODEL_CONTRACT
from engine.experiment_registry import ExperimentRegistry


DEFAULT_REPLAY_FILE = Path("logs") / "market_replay" / "market_replay_evaluations.csv"


@dataclass
class PaperTradePreflight:
    ready: bool
    status: str
    replay_rows: int = 0
    test_directional_rows: int = 0
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def run_paper_trade_preflight(path: str | Path = DEFAULT_REPLAY_FILE) -> PaperTradePreflight:
    replay_path = Path(path)
    blockers: List[str] = []
    warnings: List[str] = []
    if not replay_path.exists():
        return PaperTradePreflight(False, "BLOCKED_NO_REPLAY", blockers=["No cumulative market replay exists."])
    try:
        frame = pd.read_csv(replay_path, encoding="utf-8-sig", low_memory=False)
    except Exception as error:
        return PaperTradePreflight(False, "BLOCKED_REPLAY_UNREADABLE", blockers=[f"Replay cannot be read: {error}"])
    latest_run = ""
    if "run_id" in frame.columns and not frame.empty:
        latest_run = str(frame["run_id"].dropna().iloc[-1])
        frame = frame[frame["run_id"].astype(str) == latest_run].copy()
    required_versions = CURRENT_MODEL_CONTRACT.as_dict()
    for column, expected in required_versions.items():
        if column not in frame.columns:
            blockers.append(f"Replay is missing {column}; rerun replay with the current contract.")
        elif not frame[column].astype(str).eq(expected).all():
            blockers.append(f"Replay mixes {column} values or does not match {expected}.")
    if "replay_safe" not in frame.columns or not frame["replay_safe"].astype(str).str.lower().isin({"true", "1"}).all():
        blockers.append("Replay no-lookahead safety marker is missing or failed.")
    if "execution_price_basis" not in frame.columns or not frame["execution_price_basis"].astype(str).eq("NEXT_AVAILABLE_BAR_OPEN").all():
        blockers.append("Replay did not use next-bar-open execution.")
    if "dynamic_execution_costs" not in frame.columns or not frame["dynamic_execution_costs"].astype(str).str.lower().isin({"true", "1"}).all():
        blockers.append("Replay did not use volatility/liquidity-aware execution costs.")
    complete = frame[frame.get("evaluation_status", pd.Series("", index=frame.index)).astype(str) == "COMPLETE"]
    test = complete[
        (complete.get("replay_split", pd.Series("", index=complete.index)).astype(str) == "TEST_20")
        & complete.get("side", pd.Series("", index=complete.index)).astype(str).isin(["LONG", "SHORT"])
    ]
    if len(complete) < 500:
        blockers.append(f"At least 500 complete replay rows are required; found {len(complete)}.")
    if len(test) < 50:
        blockers.append(f"At least 50 untouched TEST directional rows are required; found {len(test)}.")
    if latest_run:
        calibration = ExperimentRegistry().latest_run("CALIBRATION", parent_run_id=latest_run)
        if calibration is None or calibration.status != "COMPLETED":
            blockers.append("No completed one-shot calibration is registered for the latest replay run.")
    warnings.append("Paper readiness means safe forward observation, not proven positive edge or live-trading approval.")
    return PaperTradePreflight(
        ready=not blockers,
        status="READY_FOR_PAPER_OBSERVATION" if not blockers else "BLOCKED_RESEARCH_PREFLIGHT",
        replay_rows=int(len(complete)),
        test_directional_rows=int(len(test)),
        blockers=blockers,
        warnings=warnings,
    )
