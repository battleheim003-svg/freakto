"""Freakto v10.1 Replay Optimization Lab."""
from __future__ import annotations
import pandas as pd

VERSION="v10.1.0"

def load_replay(path="logs/market_replay/market_replay_evaluations.csv"):
    return pd.read_csv(path)

def optimize_thresholds(df, scores=("score",)):
    results=[]
    if "score" not in df.columns:
        return results
    for threshold in [40,50,60,70,80,90]:
        x=df[df["score"]>=threshold]
        if len(x):
            results.append({
                "type":"score_threshold",
                "threshold":threshold,
                "samples":len(x)
            })
    return results

def run_lab(path="logs/market_replay/market_replay_evaluations.csv"):
    df=load_replay(path)
    return {
        "version":VERSION,
        "rows":len(df),
        "threshold_candidates":optimize_thresholds(df)
    }
