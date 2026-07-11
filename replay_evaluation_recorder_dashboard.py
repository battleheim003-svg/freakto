"""CLI for Freakto v10.1.5 Replay Evaluation Recorder."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.replay_evaluation_recorder import (
    DEFAULT_REPLAY_FILE,
    VERSION,
    backfill_replay_file,
    format_recorder_console,
    report_to_dict,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Backfill canonical replay evaluation metrics safely",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input", default=str(DEFAULT_REPLAY_FILE))
    parser.add_argument("--horizon", type=int, default=0, help="Primary horizon in candles; 0=auto (prefers 6c)")
    parser.add_argument("--apply", action="store_true", help="Write repaired CSV after making a timestamped backup")
    parser.add_argument("--json", action="store_true", help="Print machine-readable report")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    _, report = backfill_replay_file(
        args.input,
        apply=args.apply,
        primary_horizon_candles=args.horizon,
    )
    if args.json:
        print(json.dumps(report_to_dict(report), ensure_ascii=False, indent=2))
    else:
        print(format_recorder_console(report))
    if report.blockers:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
