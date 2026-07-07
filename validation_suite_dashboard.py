"""Freakto Validation Intelligence Suite CLI v5.0

Runs validation + risk intelligence together:
1) Metric Definitions
2) Edge Validation
3) Regime Performance Matrix
4) Portfolio Memory
5) Confidence Calibration
6) Monte Carlo Risk Lab
7) Forward Test Status
8) Historical Backtest Status
9) Advanced Live Readiness Score
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path

from engine.edge_validation import format_edge_validation_console, run_edge_validation, save_edge_validation
from engine.regime_matrix import format_regime_matrix_console, run_regime_matrix, save_regime_matrix
from engine.metric_definitions import format_metric_definitions_console, save_metric_definitions_report
from engine.portfolio_memory import build_portfolio_memory, format_portfolio_memory_console, save_portfolio_memory
from engine.confidence_calibration import run_confidence_calibration, format_confidence_calibration_console, save_confidence_calibration
from engine.monte_carlo import run_monte_carlo, format_monte_carlo_console, save_monte_carlo
from engine.live_readiness_score import (
    assess_advanced_live_readiness,
    format_advanced_readiness_console,
    save_advanced_readiness,
)
from engine.forward_test import build_forward_progress, format_forward_progress_console, save_forward_progress
from engine.historical_backtest import load_all_backtest_summary, format_summary_console as format_backtest_summary_console
from telegram_notifier import send_telegram_message

SUITE_DIR = Path("logs") / "validation_suite"


def _save_combined_report(text: str) -> Path:
    SUITE_DIR.mkdir(parents=True, exist_ok=True)
    path = SUITE_DIR / f"validation_suite_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
    path.write_text(text, encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Send combined validation suite report to Telegram.")
    parser.add_argument("--iterations", type=int, default=2000)
    parser.add_argument("--trades", type=int, default=100)
    args = parser.parse_args()

    edge = run_edge_validation()
    regime = run_regime_matrix()
    memory = build_portfolio_memory()
    calibration = run_confidence_calibration()
    monte = run_monte_carlo(iterations=args.iterations, trades_per_run=args.trades)
    forward_progress = build_forward_progress()
    backtest_summary = load_all_backtest_summary()
    readiness = assess_advanced_live_readiness()

    metric_text = format_metric_definitions_console()
    edge_text = format_edge_validation_console(edge)
    regime_text = format_regime_matrix_console(regime)
    memory_text = format_portfolio_memory_console(memory)
    calibration_text = format_confidence_calibration_console(calibration)
    monte_text = format_monte_carlo_console(monte)
    forward_text = format_forward_progress_console(forward_progress)
    backtest_text = format_backtest_summary_console(backtest_summary)
    readiness_text = format_advanced_readiness_console(readiness)

    combined = "\n\n".join([metric_text, edge_text, regime_text, memory_text, calibration_text, monte_text, forward_text, backtest_text, readiness_text])
    print(combined)

    metric_report = save_metric_definitions_report()
    edge_json, edge_report = save_edge_validation(edge)
    regime_csv, regime_report = save_regime_matrix(regime)
    memory_json, memory_report = save_portfolio_memory(memory)
    cal_json, cal_report = save_confidence_calibration(calibration)
    mc_json, mc_report = save_monte_carlo(monte)
    forward_json, forward_report = save_forward_progress(forward_progress)
    readiness_json, readiness_report = save_advanced_readiness(readiness)
    combined_path = _save_combined_report(combined)

    print(f"📘 Metric definitions report ذخیره شد: {metric_report}")
    print(f"📐 Edge validation JSON ذخیره شد: {edge_json}")
    print(f"📝 Edge validation report ذخیره شد: {edge_report}")
    print(f"🧬 Regime matrix CSV ذخیره شد: {regime_csv}")
    print(f"📝 Regime matrix report ذخیره شد: {regime_report}")
    print(f"🧠 Portfolio memory JSON ذخیره شد: {memory_json}")
    print(f"📝 Portfolio memory report ذخیره شد: {memory_report}")
    print(f"🎯 Confidence calibration JSON ذخیره شد: {cal_json}")
    print(f"📝 Confidence calibration report ذخیره شد: {cal_report}")
    print(f"🎲 Monte Carlo JSON ذخیره شد: {mc_json}")
    print(f"📝 Monte Carlo report ذخیره شد: {mc_report}")
    print(f"🧭 Forward status JSON ذخیره شد: {forward_json}")
    print(f"📝 Forward status report ذخیره شد: {forward_report}")
    print(f"🚦 Advanced readiness JSON ذخیره شد: {readiness_json}")
    print(f"📝 Advanced readiness report ذخیره شد: {readiness_report}")
    print(f"📦 Combined validation suite report ذخیره شد: {combined_path}")

    if args.send:
        send_telegram_message(combined)


if __name__ == "__main__":
    main()
