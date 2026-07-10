"""Freakto v10.1.2 Replay Performance Evaluator.
Research only. No live/paper mutation.
"""
from __future__ import annotations
import pandas as pd

VERSION = "v10.1.2"

THRESHOLDS = [40, 50, 60, 70, 80, 90]
HOLDING_PERIODS = ["4h", "8h", "12h", "24h", "48h"]

def safe_metric(df, col):
    if col in df.columns:
        return float(df[col].mean())
    return None

def evaluate_thresholds(df):
    results = []
    if "score" not in df.columns:
        return results

    for t in THRESHOLDS:
        subset = df[df["score"] >= t]
        item = {
            "threshold": t,
            "samples": int(len(subset)),
            "status": "INSUFFICIENT_DATA"
        }
        if len(subset):
            item["avg_return"] = safe_metric(subset, "return")
            item["avg_net_return"] = safe_metric(subset, "net_return")
            item["status"] = "RESEARCH_READY"
        results.append(item)
    return results

def evaluate_holding(df):
    return [
        {
            "holding": h,
            "status": "RESEARCH_CANDIDATE"
        }
        for h in HOLDING_PERIODS
    ]

def run(path="logs/market_replay/market_replay_evaluations.csv"):
    df = pd.read_csv(path)

    return {
        "version": VERSION,
        "rows": int(len(df)),
        "threshold_results": evaluate_thresholds(df),
        "holding_results": evaluate_holding(df),
        "verdict": "REPLAY_EVALUATION_READY"
    }
