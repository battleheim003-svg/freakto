"""CLI dashboard for Freakto v10.2 Score Calibration Lab."""
from __future__ import annotations

import argparse
import builtins
import sys

from engine.replay_score_calibration import (
    DEFAULT_FILE,
    VERSION,
    format_replay_score_calibration_console,
    run_replay_score_calibration,
    save_replay_score_calibration,
)


def print(value) -> None:
    """Console-safe local print for Windows legacy code pages."""
    encoding = sys.stdout.encoding or "utf-8"
    builtins.print(str(value).encode(encoding, errors="replace").decode(encoding))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay score calibration and feature attribution")
    parser.add_argument("--input", default=str(DEFAULT_FILE))
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--no-save", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    report = run_replay_score_calibration(args.input)
    print(format_replay_score_calibration_console(report, compact=args.compact))
    if not args.no_save:
        paths = save_replay_score_calibration(report)
        print(f"🧾 Calibration JSON: {paths.json_path}")
        print(f"📝 Calibration report: {paths.report_path}")
        print(f"📊 Score bands CSV: {paths.score_bands_csv}")
        print(f"🧬 Feature attribution CSV: {paths.feature_attribution_csv}")
        print(f"🔗 Feature interactions CSV: {paths.interactions_csv}")
        print(f"🧩 Segment performance CSV: {paths.segments_csv}")
        print(f"📚 Calibration observations: {paths.observations_csv}")
    if report.get("blockers"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
