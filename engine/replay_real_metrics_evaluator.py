"""Freakto v10.1.5 real replay metrics evaluator.

Ranks score thresholds using chronological Train/Validation/Test splits and
canonical metrics.  Research only; it never mutates strategy settings.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from engine.replay_evaluation_recorder import record_canonical_metrics
from engine.replay_schema_adapter import normalize_metrics

VERSION = "v10.1.5"
THRESHOLDS = [40, 50, 60, 70, 80, 90]
DEFAULT_FILE = Path("logs") / "market_replay" / "market_replay_evaluations.csv"


@dataclass
class ThresholdMetric:
    threshold: int
    split: str
    samples: int
    win_rate_pct: float
    avg_gross_return_pct: float
    avg_net_return_pct: float
    median_net_return_pct: float
    profit_factor: float
    max_drawdown_proxy_pct: float


def _metric(frame: pd.DataFrame, threshold: int, split: str) -> ThresholdMetric:
    part = frame[frame["normalized_score"] >= threshold]
    if split != "ALL" and "normalized_split" in part.columns:
        part = part[part["normalized_split"] == split]
    if "normalized_status" in part.columns:
        part = part[part["normalized_status"] == "COMPLETE"]
    if "normalized_side" in part.columns:
        part = part[part["normalized_side"].isin(["LONG", "SHORT"])]
    net = pd.to_numeric(part.get("normalized_net_return", pd.Series(dtype=float)), errors="coerce").dropna()
    gross = pd.to_numeric(part.get("normalized_gross_return", pd.Series(dtype=float)), errors="coerce").dropna()
    wins = net[net > 0]
    losses = net[net < 0]
    pf = float(wins.sum() / abs(losses.sum())) if len(losses) and abs(losses.sum()) > 0 else (999.0 if len(wins) else 0.0)
    equity = net.fillna(0).cumsum()
    drawdown = equity - equity.cummax() if len(equity) else pd.Series(dtype=float)
    return ThresholdMetric(
        threshold=threshold,
        split=split,
        samples=int(len(net)),
        win_rate_pct=round(float((net > 0).mean() * 100), 2) if len(net) else 0.0,
        avg_gross_return_pct=round(float(gross.mean()), 6) if len(gross) else 0.0,
        avg_net_return_pct=round(float(net.mean()), 6) if len(net) else 0.0,
        median_net_return_pct=round(float(net.median()), 6) if len(net) else 0.0,
        profit_factor=round(pf, 4),
        max_drawdown_proxy_pct=round(float(drawdown.min()), 6) if len(drawdown) else 0.0,
    )


def _verdict(rows: Dict[str, ThresholdMetric]) -> str:
    train = rows.get("TRAIN_60")
    validation = rows.get("VALIDATION_20")
    test = rows.get("TEST_20")
    if not test or test.samples < 50:
        return "LOW_TEST_SAMPLE"
    if not validation or validation.samples < 50:
        return "LOW_VALIDATION_SAMPLE"
    if test.avg_net_return_pct > 0 and test.profit_factor > 1 and validation.avg_net_return_pct > 0:
        return "FORWARD_SHADOW_CANDIDATE"
    if train and train.avg_net_return_pct > 0 and test.avg_net_return_pct <= 0:
        return "OVERFIT_TRAIN_POSITIVE_TEST_NEGATIVE"
    if test.avg_net_return_pct <= 0:
        return "REJECT_TEST_NET_NON_POSITIVE"
    return "RESEARCH_ONLY_UNSTABLE"


def evaluate(frame: pd.DataFrame) -> Dict[str, Any]:
    canonical, recorder = record_canonical_metrics(frame)
    normalized, schema = normalize_metrics(canonical)
    blockers: List[str] = list(recorder.blockers)
    required = ["normalized_score", "normalized_gross_return", "normalized_net_return"]
    missing = [column for column in required if column not in normalized.columns]
    if missing:
        blockers.append("Missing normalized metrics: " + ", ".join(missing))

    threshold_results: List[Dict[str, Any]] = []
    candidates: List[Dict[str, Any]] = []
    if not blockers:
        for threshold in THRESHOLDS:
            metrics = {split: _metric(normalized, threshold, split) for split in ["ALL", "TRAIN_60", "VALIDATION_20", "TEST_20"]}
            verdict = _verdict(metrics)
            item = {
                "threshold": threshold,
                "verdict": verdict,
                "metrics": {key: asdict(value) for key, value in metrics.items()},
            }
            threshold_results.append(item)
            if verdict == "FORWARD_SHADOW_CANDIDATE":
                candidates.append(item)

    status = "REAL_METRICS_EVALUATED" if not blockers else "REAL_METRICS_BLOCKED"
    if not blockers and not candidates:
        status = "REAL_METRICS_NO_ROBUST_CANDIDATE"
    return {
        "version": VERSION,
        "rows": int(len(frame)),
        "schema_detected": schema,
        "recorder": asdict(recorder),
        "status": status,
        "threshold_results": threshold_results,
        "forward_shadow_candidates": candidates,
        "blockers": blockers,
        "warnings": [
            "Threshold ranking alone is not permission for Paper/Live.",
            "Candidates require Forward Shadow validation with unchanged parameters.",
        ],
    }


def run(path: str | Path = DEFAULT_FILE) -> Dict[str, Any]:
    return evaluate(pd.read_csv(path, encoding="utf-8-sig"))
