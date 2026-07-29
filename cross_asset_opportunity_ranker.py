"""Research-only CLI for calibrated cross-asset opportunity ranking."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from freakto.cross_asset import evaluate_rankings, rank_opportunities


def main() -> int:
    parser = argparse.ArgumentParser(description="Research-only cross-asset ranker")
    commands = parser.add_subparsers(dest="command", required=True)
    rank = commands.add_parser("rank")
    rank.add_argument("--input", required=True)
    rank.add_argument("--output")
    rank.add_argument("--rankings-csv")
    rank.add_argument("--min-calibration-samples", type=int, default=100)
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("--rankings", required=True)
    evaluate.add_argument("--outcomes", required=True)
    evaluate.add_argument("--min-completed-periods", type=int, default=20)
    args = parser.parse_args()

    if args.command == "rank":
        report = rank_opportunities(
            pd.read_csv(args.input),
            min_calibration_samples=args.min_calibration_samples,
        )
        payload = asdict(report)
        if args.output:
            Path(args.output).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        if args.rankings_csv:
            pd.DataFrame(report.rankings).to_csv(
                args.rankings_csv,
                index=False,
                encoding="utf-8",
            )
    else:
        report = evaluate_rankings(
            pd.read_csv(args.rankings),
            pd.read_csv(args.outcomes),
            min_completed_periods=args.min_completed_periods,
        )
        payload = asdict(report)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if report.status != "BLOCKED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
