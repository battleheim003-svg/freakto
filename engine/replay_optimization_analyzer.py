"""Freakto v10.1.1 Replay Optimization Analyzer
Research only. Does not modify live decision logic.
"""
from __future__ import annotations
import pandas as pd

VERSION = "v10.1.1"

DEFAULT_THRESHOLDS = [40, 50, 60, 70, 80, 90]
DEFAULT_HOLDING = ["4h", "8h", "12h", "24h", "48h"]

def analyze_thresholds(df: pd.DataFrame):
    results = []
    if "score" not in df.columns:
        return results
    return [
        {
            "threshold": t,
            "samples": int(len(df[df["score"] >= t]))
        }
        for t in DEFAULT_THRESHOLDS
    ]

def analyze_summary(df: pd.DataFrame):
    return {
        "version": VERSION,
        "rows": int(len(df)),
        "threshold_analysis": analyze_thresholds(df),
        "holding_candidates": DEFAULT_HOLDING,
        "status": "RESEARCH_ANALYSIS_READY"
    }

def run(path="logs/market_replay/market_replay_evaluations.csv"):
    df = pd.read_csv(path)
    return analyze_summary(df)
