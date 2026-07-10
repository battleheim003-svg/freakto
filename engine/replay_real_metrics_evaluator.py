"""Freakto v10.1.3 Real Replay Metrics Evaluator."""

from __future__ import annotations
import pandas as pd
from engine.replay_schema_adapter import normalize_metrics

VERSION = "v10.1.3"

THRESHOLDS = [40,50,60,70,80,90]

def evaluate(df):
    df, schema = normalize_metrics(df)
    output=[]

    for t in THRESHOLDS:
        if "score" not in df.columns:
            break

        part=df[df["score"]>=t]

        item={
            "threshold":t,
            "samples":len(part),
            "schema":schema
        }

        if "normalized_return" in part:
            item["avg_return"]=float(part["normalized_return"].mean())

        if "normalized_net_return" in part:
            item["avg_net_return"]=float(part["normalized_net_return"].mean())

        if "normalized_win" in part:
            item["win_rate"]=float(part["normalized_win"].mean())

        output.append(item)

    return {
        "version":VERSION,
        "rows":len(df),
        "schema_detected":schema,
        "threshold_results":output,
        "status":"REAL_METRICS_READY"
    }

def run(path="logs/market_replay/market_replay_evaluations.csv"):
    return evaluate(pd.read_csv(path))
