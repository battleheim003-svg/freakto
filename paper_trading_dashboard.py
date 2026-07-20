"""
paper_trading_dashboard.py

Freakto v4.7.1.0 Practical Testing Suite

Commands:
    python paper_trading_dashboard.py
    python paper_trading_dashboard.py --scan
    python paper_trading_dashboard.py --evaluate
    python paper_trading_dashboard.py --scan --evaluate
    python paper_trading_dashboard.py --send
    python paper_trading_dashboard.py --web
"""

import argparse
import subprocess
import sys
from pathlib import Path

def _safe_print(text: str) -> None:
    encoding = sys.stdout.encoding or "utf-8"
    print(str(text).encode(encoding, errors="replace").decode(encoding))


def _existing_status_text() -> str:
    from engine.paper_trading import PAPER_EVALUATIONS_FILE, PAPER_TRADES_FILE, summarize_paper_evaluations

    summary = summarize_paper_evaluations()
    lines = []
    lines.append("=" * 110)
    lines.append("🧪 Freakto Paper Trading Dashboard v4.7.1")
    lines.append("=" * 110)
    lines.append(f"Paper trades file      : {PAPER_TRADES_FILE} | exists={PAPER_TRADES_FILE.exists()}")
    lines.append(f"Paper evaluations file : {PAPER_EVALUATIONS_FILE} | exists={PAPER_EVALUATIONS_FILE.exists()}")
    lines.append(f"Total paper trades     : {summary.total_trades}")
    lines.append(f"Closed paper trades    : {summary.complete_rows}")
    lines.append(f"Open paper trades      : {summary.open_rows}")
    lines.append(f"Paper Trade Win Rate   : {summary.win_rate:.2f}%")
    lines.append(f"Paper Expectancy       : {summary.expectancy_r:.3f}R")
    lines.append("")
    lines.append("برای ثبت معاملات فرضی از آخرین اسکن زنده:")
    lines.append("python paper_trading_dashboard.py --scan")
    lines.append("")
    lines.append("برای ارزیابی معاملات فرضی:")
    lines.append("python paper_trading_dashboard.py --evaluate")
    lines.append("=" * 110)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan", action="store_true", help="Run portfolio scan and record eligible paper trades.")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate existing paper trades.")
    parser.add_argument("--preflight", action="store_true", help="Check whether new paper observations may be recorded.")
    parser.add_argument("--send", action="store_true", help="Send summary to Telegram.")
    parser.add_argument("--web", action="store_true", help="Open the local Shadow/Paper web dashboard.")
    args = parser.parse_args()

    outputs = []

    if args.web:
        dashboard = Path(__file__).resolve().with_name("live_paper_web_dashboard.py")
        return subprocess.call([sys.executable, "-m", "streamlit", "run", str(dashboard)])

    from engine.paper_trading import (
        evaluate_paper_trades,
        format_paper_evaluation_summary,
        format_paper_record_result,
        record_paper_trades_from_portfolio,
    )

    if args.preflight:
        from engine.paper_trade_readiness import run_paper_trade_preflight

        preflight = run_paper_trade_preflight()
        lines = [
            f"Paper preflight: {preflight.status}",
            f"Ready: {preflight.ready}",
            f"Replay rows: {preflight.replay_rows}",
            f"TEST directional rows: {preflight.test_directional_rows}",
            f"Economic calibration: {preflight.economic_calibration_status}",
            f"Capital allocation ready: {preflight.capital_allocation_ready}",
        ]
        lines.extend(f"[BLOCKER] {item}" for item in preflight.blockers)
        lines.extend(f"[WARNING] {item}" for item in preflight.warnings)
        text = "\n".join(lines)
        _safe_print(text)
        outputs.append(text)

    if args.scan:
        from portfolio_scanner import run_portfolio_scan
        result = run_portfolio_scan(send=False)
        record_result = record_paper_trades_from_portfolio(result)
        text = format_paper_record_result(record_result)
        _safe_print(text)
        outputs.append(text)

    if args.evaluate:
        from data_fetcher import fetch_ohlcv
        summary = evaluate_paper_trades(fetcher=fetch_ohlcv)
        text = format_paper_evaluation_summary(summary)
        _safe_print(text)
        outputs.append(text)

    if not args.scan and not args.evaluate and not args.preflight and not args.web:
        text = _existing_status_text()
        _safe_print(text)
        outputs.append(text)

    if args.send:
        from telegram_notifier import send_telegram_message

        send_telegram_message("\n\n".join(outputs))

    return 0


if __name__ == "__main__":
    main()
