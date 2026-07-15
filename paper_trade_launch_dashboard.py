"""Freakto Paper Trade Launch Dashboard v2.

Commands:
  python -X utf8 paper_trade_launch_dashboard.py --preflight
  python -X utf8 paper_trade_launch_dashboard.py --arm-research
  python -X utf8 paper_trade_launch_dashboard.py --arm-strategy
  python -X utf8 paper_trade_launch_dashboard.py --scan --decision-file logs/decisions.csv
  python -X utf8 paper_trade_launch_dashboard.py --evaluate
  python -X utf8 paper_trade_launch_dashboard.py --status
  python -X utf8 paper_trade_launch_dashboard.py --disarm

No command in this dashboard can send a real exchange order.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

from engine.paper_observation_v2 import (
    PaperRiskConfig,
    arm_paper_mode,
    disarm_paper_mode,
    load_arm_state,
    record_paper_observations,
)
from engine.paper_readiness_v2 import (
    build_paper_launch_readiness,
    write_paper_readiness_outputs,
)


def _read_decisions(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p, encoding="utf-8-sig", low_memory=False)


def _print_readiness(readiness) -> None:
    print("=" * 116)
    print("Freakto Paper Trade Launch v2")
    print("=" * 116)
    print(f"Status                    : {readiness.status}")
    print(f"Research collection ready : {readiness.research_collection_ready}")
    print(f"Strategy paper ready      : {readiness.strategy_paper_ready}")
    print(f"Selected policy           : {readiness.selected_policy}")
    print(f"Event / cost-gated rows   : {readiness.event_rows} / {readiness.cost_gated_event_rows}")
    print(f"Fresh directional rows    : {readiness.fresh_directional_rows}")
    print(f"Fresh fixed-gate samples  : {readiness.fresh_fixed_gate_samples}")
    print("Live orders enabled       : False")
    if readiness.candidate_assessments:
        print("Deterministic candidates:")
        for item in readiness.candidate_assessments:
            print(
                f"- {item.strategy}: eligible={item.eligible} | Holdout n={item.holdout_sample_count} | "
                f"exp={item.holdout_expectancy_pct:.6f}% | PF={item.holdout_profit_factor} | "
                f"WF={item.positive_walk_forward_folds}/{item.valid_walk_forward_folds}"
            )
    if readiness.blockers:
        print("Blockers:")
        for item in readiness.blockers:
            print(f"- {item}")
    if readiness.warnings:
        print("Warnings:")
        for item in readiness.warnings:
            print(f"- {item}")
    print("Safety                    : virtual observations only; no real orders or capital allocation.")
    print("=" * 116)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--preflight", action="store_true")
    p.add_argument("--status", action="store_true")
    p.add_argument("--arm-research", action="store_true")
    p.add_argument("--arm-strategy", action="store_true")
    p.add_argument("--disarm", action="store_true")
    p.add_argument("--scan", action="store_true")
    p.add_argument("--evaluate", action="store_true")
    p.add_argument("--decision-file", default="logs/decisions.csv")
    p.add_argument("--event-dir", default="logs/event_opportunity_v2")
    p.add_argument("--cost-dir", default="logs/cost_gate_diagnostics")
    p.add_argument("--fresh-report", default="logs/fresh_oos_v2/fresh_oos_report.json")
    p.add_argument("--output-dir", default="logs/paper_launch_v2")
    p.add_argument("--virtual-equity", type=float, default=10000.0)
    p.add_argument("--risk-per-trade-pct", type=float, default=0.25)
    p.add_argument("--max-open-trades", type=int, default=5)
    p.add_argument("--max-open-per-symbol", type=int, default=1)
    p.add_argument("--max-total-open-risk-pct", type=float, default=1.0)
    return p


def main() -> int:
    args = parser().parse_args()
    readiness, walk = build_paper_launch_readiness(args.event_dir, args.cost_dir, args.fresh_report)
    files = write_paper_readiness_outputs(readiness, walk, args.output_dir)
    if args.preflight or not any((args.status, args.arm_research, args.arm_strategy, args.disarm, args.scan, args.evaluate)):
        _print_readiness(readiness)
    if args.status:
        _print_readiness(readiness)
        print("Arm state:", json.dumps(load_arm_state(args.output_dir), ensure_ascii=False))
    if args.arm_research:
        path = arm_paper_mode(readiness, "RESEARCH", args.output_dir)
        print(f"Research paper observation armed: {path}")
    if args.arm_strategy:
        path = arm_paper_mode(readiness, "STRATEGY", args.output_dir)
        print(f"Strategy paper validation armed: {path}")
    if args.disarm:
        path = disarm_paper_mode(args.output_dir)
        print(f"Paper observation disarmed: {path}")
    if args.scan:
        decisions = _read_decisions(args.decision_file)
        risk = PaperRiskConfig(
            virtual_equity=args.virtual_equity,
            risk_per_trade_pct=args.risk_per_trade_pct,
            max_open_trades=args.max_open_trades,
            max_open_per_symbol=args.max_open_per_symbol,
            max_total_open_risk_pct=args.max_total_open_risk_pct,
        )
        result = record_paper_observations(decisions, readiness, risk=risk, output_dir=args.output_dir)
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if args.evaluate:
        try:
            from data_fetcher import fetch_ohlcv
            from engine.paper_trading import evaluate_paper_trades, format_paper_evaluation_summary
            summary = evaluate_paper_trades(fetcher=fetch_ohlcv)
            print(format_paper_evaluation_summary(summary))
        except Exception as exc:
            print(f"Paper evaluation failed: {type(exc).__name__}: {exc}")
            return 2
    print(json.dumps({"status": readiness.status, "strategy_paper_ready": readiness.strategy_paper_ready, "live_orders_enabled": False, "outputs": files}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
