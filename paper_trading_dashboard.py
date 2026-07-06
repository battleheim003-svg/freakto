"""
paper_trading_dashboard.py

Freakto v4.7.1.0 Practical Testing Suite

Commands:
    python paper_trading_dashboard.py
    python paper_trading_dashboard.py --scan
    python paper_trading_dashboard.py --evaluate
    python paper_trading_dashboard.py --scan --evaluate
    python paper_trading_dashboard.py --send
"""

import argparse
from pathlib import Path

from telegram_notifier import send_telegram_message
from engine.paper_trading import (
    PAPER_TRADES_FILE,
    PAPER_EVALUATIONS_FILE,
    evaluate_paper_trades,
    format_paper_evaluation_summary,
    format_paper_record_result,
    record_paper_trades_from_portfolio,
    summarize_paper_evaluations,
)


def _existing_status_text() -> str:
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
    parser.add_argument("--send", action="store_true", help="Send summary to Telegram.")
    args = parser.parse_args()

    outputs = []

    if args.scan:
        from portfolio_scanner import run_portfolio_scan
        result = run_portfolio_scan(send=False)
        record_result = record_paper_trades_from_portfolio(result)
        text = format_paper_record_result(record_result)
        print(text)
        outputs.append(text)

    if args.evaluate:
        from data_fetcher import fetch_ohlcv
        summary = evaluate_paper_trades(fetcher=fetch_ohlcv)
        text = format_paper_evaluation_summary(summary)
        print(text)
        outputs.append(text)

    if not args.scan and not args.evaluate:
        text = _existing_status_text()
        print(text)
        outputs.append(text)

    if args.send:
        send_telegram_message("\n\n".join(outputs))


if __name__ == "__main__":
    main()
