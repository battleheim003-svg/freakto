"""Freakto Replay Metrics Repair Dashboard v10.1.4"""

import pandas as pd
from engine.replay_metrics_repair import repair, VERSION

def main():
    path="logs/market_replay/market_replay_evaluations.csv"
    df=pd.read_csv(path)

    repaired, fields = repair(df)

    print("="*90)
    print("🛠️ Freakto Replay Metrics Repair v10.1.4")
    print("="*90)
    print("version:", VERSION)
    print("rows:", len(repaired))
    print("detected_fields:", fields)
    print("repaired_return_available:", "repaired_return" in repaired.columns)
    print("repaired_win_available:", "repaired_win" in repaired.columns)

if __name__=="__main__":
    main()
