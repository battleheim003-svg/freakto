"""Dashboard for Freakto v10.1.5 real replay metrics."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from engine.replay_real_metrics_evaluator import DEFAULT_FILE, VERSION, run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate real replay threshold metrics")
    parser.add_argument("--input", default=str(DEFAULT_FILE))
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--no-save", action="store_true")
    return parser


def _print(result: dict, compact: bool) -> None:
    print("=" * 118)
    print(f"🧪 Freakto Replay Real Metrics Evaluator {VERSION}")
    print("=" * 118)
    print(f"Status                 : {result['status']}")
    print(f"Rows                   : {result['rows']}")
    schema = result.get("schema_detected", {})
    print(f"Score/Gross/Net/Win    : {schema.get('score')} / {schema.get('gross_return')} / {schema.get('net_return')} / {schema.get('win')}")
    print(f"Candidates             : {len(result.get('forward_shadow_candidates', []))}")
    print("\nThreshold Results:")
    for item in result.get("threshold_results", []):
        test = item["metrics"]["TEST_20"]
        val = item["metrics"]["VALIDATION_20"]
        print(
            f"- Score >= {item['threshold']}: test_n={test['samples']} "
            f"test_win={test['win_rate_pct']}% test_net={test['avg_net_return_pct']}% "
            f"test_PF={test['profit_factor']} | val_net={val['avg_net_return_pct']}% "
            f"| {item['verdict']}"
        )
    if result.get("blockers"):
        print("\nBlockers:")
        for item in result["blockers"]:
            print(f"⛔ {item}")
    print("\nWarnings:")
    for item in result.get("warnings", []):
        print(f"⚠️ {item}")
    print("=" * 118)


def main() -> None:
    args = build_parser().parse_args()
    result = run(args.input)
    _print(result, args.compact)
    if not args.no_save:
        out_dir = Path("logs") / "market_replay" / "optimization"
        out_dir.mkdir(parents=True, exist_ok=True)
        run_id = "replay_real_metrics_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        json_path = out_dir / f"{run_id}.json"
        json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        rows = []
        for item in result.get("threshold_results", []):
            for split, metric in item.get("metrics", {}).items():
                row = dict(metric)
                row["verdict"] = item.get("verdict")
                rows.append(row)
        csv_path = out_dir / f"{run_id}.csv"
        pd.DataFrame(rows).to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"📊 Metrics CSV: {csv_path}")
        print(f"🧾 Metrics JSON: {json_path}")
    if result.get("blockers"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
