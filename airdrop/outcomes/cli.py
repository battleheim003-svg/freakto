"""Operational CLI for prediction sync, outcome recording, and reports."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from airdrop.outcomes import OutcomeObservation, OutcomeTracker, build_backtest_report

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRACKER_DB = ROOT / "history" / "airdrop_outcomes.db"
DEFAULT_RADAR_DB = ROOT / "history" / "airdrop_radar.db"


def _optional_bool(value: str) -> bool | None:
    return {"yes": True, "no": False, "unknown": None}[value]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Airdrop outcome tracker and backtest")
    parser.add_argument("--db", default=str(DEFAULT_TRACKER_DB))
    commands = parser.add_subparsers(dest="command", required=True)

    sync = commands.add_parser("sync")
    sync.add_argument("--source-db", default=str(DEFAULT_RADAR_DB))

    record = commands.add_parser("record")
    record.add_argument("--identity", required=True)
    record.add_argument("--status", required=True)
    record.add_argument("--observed-at", default="")
    record.add_argument("--eligible", choices=["yes", "no", "unknown"], required=True)
    record.add_argument("--claimed", choices=["yes", "no", "unknown"], default="unknown")
    record.add_argument("--gross-reward-usd", type=float)
    record.add_argument("--cost-usd", type=float, default=0.0)
    record.add_argument("--source-ref", required=True)
    record.add_argument("--notes", default="")

    report = commands.add_parser("report")
    report.add_argument("--min-resolved", type=int, default=30)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    tracker = OutcomeTracker(args.db)
    if args.command == "sync":
        try:
            imported = tracker.sync_opportunity_database(args.source_db)
        except FileNotFoundError:
            print(
                json.dumps(
                    {
                        "status": "SYNC_BLOCKED",
                        "blocker": "AIRDROP_RADAR_DATABASE_NOT_FOUND",
                        "source_db": str(Path(args.source_db)),
                    },
                    indent=2,
                )
            )
            return 2
        print(json.dumps({"status": "SYNCED", "new_snapshots": imported}, indent=2))
        return 0
    if args.command == "record":
        observed_at = args.observed_at or datetime.now(timezone.utc).isoformat()
        created = tracker.record_outcome(
            OutcomeObservation(
                identity=args.identity,
                observed_at=observed_at,
                status=args.status,
                eligible=_optional_bool(args.eligible),
                claimed=_optional_bool(args.claimed),
                gross_reward_usd=args.gross_reward_usd,
                cost_usd=args.cost_usd,
                source_ref=args.source_ref,
                notes=args.notes,
            )
        )
        print(json.dumps({"status": "RECORDED" if created else "DUPLICATE"}, indent=2))
        return 0
    report = build_backtest_report(tracker, min_resolved=args.min_resolved)
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
