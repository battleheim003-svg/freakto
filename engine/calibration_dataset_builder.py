"""Build a stable calibration dataset from replay evaluations."""
from pathlib import Path
import pandas as pd

SRC = Path("logs/market_replay/market_replay_evaluations.csv")
OUT = Path("logs/calibration_dataset/calibration_training.csv")
MAX_ROWS = 3200


def build_calibration_dataset(limit=MAX_ROWS):
    if not SRC.exists():
        raise FileNotFoundError(SRC)
    df = pd.read_csv(SRC, encoding="utf-8-sig", low_memory=False)
    if "evaluation_status" in df.columns:
        df = df[df["evaluation_status"].astype(str).str.upper() == "COMPLETE"]
    if "net_signed_return_after_6c_pct" in df.columns:
        ret = "net_signed_return_after_6c_pct"
    elif "return_after_24h_pct" in df.columns:
        ret = "return_after_24h_pct"
    else:
        raise ValueError("No evaluation return column found")
    df["evaluated_return"] = pd.to_numeric(df[ret], errors="coerce")
    df = df.dropna(subset=["evaluated_return"])
    if "side" in df.columns:
        df = df[df["side"].astype(str).str.upper().isin(["LONG", "SHORT"])]
    cols = [c for c in [
        "decision_id","candle_timestamp","symbol","timeframe","side","score",
        "confidence_label","risk_label","actionability","regime_label",
        "evaluated_return","target_1_hit","target_2_hit","stop_hit",
        "net_return_after_24h_pct","net_signed_return_after_6c_pct"
    ] if c in df.columns]
    out = df[cols].copy()
    out["win"] = out["evaluated_return"] > 0
    out = out.sort_values("candle_timestamp") if "candle_timestamp" in out else out
    out = out.tail(limit)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False, encoding="utf-8-sig")
    return OUT, len(out)


if __name__ == "__main__":
    path, rows = build_calibration_dataset()
    print(f"Calibration dataset created: {path}")
    print(f"Rows: {rows}")
