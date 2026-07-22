"""Canonical Forward Test status and cycle retained-engine adapter."""

from __future__ import annotations

import argparse
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from engine.forward_test import (
    build_forward_progress,
    build_forward_test_plan,
    format_forward_plan_console,
    format_forward_progress_console,
    format_forward_run_console,
    run_forward_cycle,
    save_forward_progress,
    write_windows_batch_files,
)
from telegram_notifier import send_telegram_message


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", action="store_true", help="Show current Forward Test progress. Default action.")
    parser.add_argument("--plan", action="store_true", help="Show the command plan without executing it.")
    parser.add_argument("--dry-run", action="store_true", help="Build a dry-run report without running child commands.")
    parser.add_argument("--cycle", action="store_true", help="Execute one safe Forward Test data-collection cycle.")
    parser.add_argument("--validate", action="store_true", help="Run validation_suite_dashboard.py after collection.")
    parser.add_argument("--risk-lab", action="store_true", help="Run risk_lab_dashboard.py in the cycle.")
    parser.add_argument("--send", action="store_true", help="Send the final Forward Test status/report to Telegram.")
    parser.add_argument("--symbols", type=str, default="", help="Optional comma-separated portfolio symbols for portfolio_scanner.py.")
    parser.add_argument("--no-monitor", action="store_true", help="Skip monitor.py --once.")
    parser.add_argument("--no-portfolio", action="store_true", help="Skip portfolio_scanner.py --paper.")
    parser.add_argument("--no-evaluator", action="store_true", help="Skip decision_evaluator.py.")
    parser.add_argument("--no-paper-evaluator", action="store_true", help="Skip paper_trading_dashboard.py --evaluate.")
    parser.add_argument("--stop-on-error", action="store_true", help="Stop the cycle if a required task fails.")
    parser.add_argument("--continue-on-error", action="store_true", help="Continue even if a required task fails; useful for scheduled runs.")
    parser.add_argument("--write-bat", action="store_true", help="Create Windows helper .bat files.")
    args = parser.parse_args()

    plan = build_forward_test_plan(
        symbols=args.symbols,
        include_monitor=not args.no_monitor,
        include_portfolio=not args.no_portfolio,
        include_evaluator=not args.no_evaluator,
        include_paper_evaluator=not args.no_paper_evaluator,
        include_validation=args.validate,
        include_risk_lab=args.risk_lab,
        send=args.send,
    )

    if args.write_bat:
        files = write_windows_batch_files()
        print("✅ Windows helper files created:")
        for path in files:
            print(f"- {path}")
        return

    if args.plan:
        text = format_forward_plan_console(plan)
        print(text)
        return

    if args.cycle or args.dry_run:
        result = run_forward_cycle(
            plan,
            continue_on_error=(args.continue_on_error or not args.stop_on_error),
            dry_run=args.dry_run,
        )
        text = format_forward_run_console(result)
        print(text)
        progress = build_forward_progress()
        progress_text = format_forward_progress_console(progress)
        print(progress_text)
        save_forward_progress(progress)
        if args.send:
            send_telegram_message(text + "\n\n" + progress_text)
        return

    progress = build_forward_progress()
    text = format_forward_progress_console(progress)
    print(text)
    json_path, report_path = save_forward_progress(progress)
    print(f"🧭 Forward status JSON ذخیره شد: {json_path}")
    print(f"📝 Forward status report ذخیره شد: {report_path}")
    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
