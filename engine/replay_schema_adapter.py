"""Canonical schema adapter for Freakto Replay outputs v10.1.5."""
from __future__ import annotations
from typing import Dict, Iterable, Optional, Tuple
import pandas as pd

VERSION = "v10.1.5"

COLUMN_MAP = {
    "score": ["score", "decision_score", "quality_score"],
    "gross_return": [
        "gross_return_pct", "return", "return_after_24h_pct",
        "gross_signed_return_after_6c_pct", "return_after_12h_pct",
        "gross_signed_return_after_3c_pct", "return_after_4h_pct",
        "gross_signed_return_after_1c_pct",
    ],
    "net_return": [
        "net_return_pct", "net_return", "net_return_after_24h_pct",
        "net_signed_return_after_6c_pct", "net_return_after_12h_pct",
        "net_signed_return_after_3c_pct", "net_return_after_4h_pct",
        "net_signed_return_after_1c_pct",
    ],
    "win": ["win", "direction_correct", "direction_correct_after_6c"],
    "side": ["side", "direction"],
    "split": ["replay_split", "split"],
    "status": ["evaluation_status", "status"],
}


def find_column(frame: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    for column in candidates:
        if column in frame.columns:
            return column
    return None


def detect_schema(frame: pd.DataFrame) -> Dict[str, Optional[str]]:
    return {key: find_column(frame, candidates) for key, candidates in COLUMN_MAP.items()}


def normalize_metrics(frame: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Optional[str]]]:
    schema = detect_schema(frame)
    result = frame.copy()
    for canonical, source in (
        ("normalized_score", schema["score"]),
        ("normalized_gross_return", schema["gross_return"]),
        ("normalized_net_return", schema["net_return"]),
    ):
        if source:
            result[canonical] = pd.to_numeric(result[source], errors="coerce")
    if schema["win"]:
        values = result[schema["win"]]
        if values.dtype == bool:
            result["normalized_win"] = values
        else:
            result["normalized_win"] = values.astype(str).str.lower().isin({"true", "1", "yes", "y"})
    if schema["side"]:
        result["normalized_side"] = result[schema["side"]].astype(str).str.upper()
    if schema["split"]:
        result["normalized_split"] = result[schema["split"]].astype(str)
    if schema["status"]:
        result["normalized_status"] = result[schema["status"]].astype(str)
    return result, schema
