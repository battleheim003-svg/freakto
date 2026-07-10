"""Freakto v10.1.4 Replay Metrics Repair Engine.
Research only. Reconstructs evaluation metrics from available replay fields.
"""

from __future__ import annotations
import pandas as pd

VERSION = "v10.1.4"

FIELD_CANDIDATES = {
    "entry": ["entry_price", "entry", "price"],
    "exit": ["exit_price", "future_price", "close_after"],
    "side": ["side", "direction"],
    "score": ["score", "decision_score"],
    "target": ["target_hit", "hit_target"],
    "stop": ["stop_hit", "hit_stop"],
}

def find_field(df, names):
    for n in names:
        if n in df.columns:
            return n
    return None

def detect_fields(df):
    return {k: find_field(df, v) for k, v in FIELD_CANDIDATES.items()}

def calculate_return(row, fields):
    entry = fields.get("entry")
    exit_col = fields.get("exit")
    side = fields.get("side")

    if not entry or not exit_col:
        return None

    try:
        entry_price = float(row[entry])
        exit_price = float(row[exit_col])
        if entry_price == 0:
            return None

        result = (exit_price-entry_price)/entry_price

        if side and str(row[side]).upper() == "SHORT":
            result = -result

        return result * 100
    except Exception:
        return None

def repair(df):
    fields = detect_fields(df)
    df = df.copy()

    if "repaired_return" not in df.columns:
        df["repaired_return"] = df.apply(
            lambda r: calculate_return(r, fields), axis=1
        )

    df["repaired_net_return"] = df["repaired_return"]

    if "repaired_win" not in df.columns:
        df["repaired_win"] = df["repaired_return"].apply(
            lambda x: 1 if x is not None and x > 0 else 0
        )

    return df, fields
