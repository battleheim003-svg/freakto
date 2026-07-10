"""Freakto v10.1.3 Replay Schema Adapter.
Research layer only.
Automatically maps replay columns to evaluation metrics.
"""

from __future__ import annotations
import pandas as pd

VERSION = "v10.1.3"

COLUMN_MAP = {
    "score": ["score", "decision_score", "quality_score"],
    "return": ["return", "avg_return", "avg_24h_return", "realized_return", "pnl_percent"],
    "net_return": ["net_return", "net_pnl", "net_profit", "net_pnl_percent"],
    "win": ["win", "is_win", "target_hit"],
}

def find_column(df, candidates):
    for col in candidates:
        if col in df.columns:
            return col
    return None

def detect_schema(df):
    detected = {}
    for key, candidates in COLUMN_MAP.items():
        detected[key] = find_column(df, candidates)
    return detected

def normalize_metrics(df):
    schema = detect_schema(df)
    result = df.copy()

    if schema["return"]:
        result["normalized_return"] = result[schema["return"]]

    if schema["net_return"]:
        result["normalized_net_return"] = result[schema["net_return"]]

    if schema["win"]:
        result["normalized_win"] = result[schema["win"]]

    return result, schema
