"""Freakto v5.0 Risk Lab Dashboard

Runs the three v5.0 research priorities together:
1) Portfolio Memory
2) Confidence Calibration
3) Monte Carlo Risk Lab
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path

from engine.portfolio_memory import build_portfolio_memory, format_portfolio_memory_console, save_portfolio_memory
from engine.confidence_calibration import run_confidence_calibration, format_confidence_calibration_console, save_confidence_calibration
from engine.monte_carlo import run_monte_carlo, format_monte_carlo_console, save_monte_carlo
from telegram_notifier import send_telegram_message

RISK_LAB_DIR = Path("logs") / "risk_lab"


def _save_combined(text: str) -> Path:
    RISK_LAB_DIR.mkdir(parents=True, exist_ok=True)
    path = RISK_LAB_DIR / f"risk_lab_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
    path.write_text(text, encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Send combined v5 risk lab report to Telegram.")
    parser.add_argument("--iterations", type=int, default=2000)
    parser.add_argument("--trades", type=int, default=100)
    args = parser.parse_args()

    memory = build_portfolio_memory()
    calibration = run_confidence_calibration()
    monte = run_monte_carlo(iterations=args.iterations, trades_per_run=args.trades)

    memory_text = format_portfolio_memory_console(memory)
    calibration_text = format_confidence_calibration_console(calibration)
    monte_text = format_monte_carlo_console(monte)
    combined = "\n\n".join([memory_text, calibration_text, monte_text])
    print(combined)

    memory_json, memory_report = save_portfolio_memory(memory)
    cal_json, cal_report = save_confidence_calibration(calibration)
    mc_json, mc_report = save_monte_carlo(monte)
    combined_path = _save_combined(combined)

    print(f"🧠 Portfolio memory JSON ذخیره شد: {memory_json}")
    print(f"📝 Portfolio memory report ذخیره شد: {memory_report}")
    print(f"🎯 Confidence calibration JSON ذخیره شد: {cal_json}")
    print(f"📝 Confidence calibration report ذخیره شد: {cal_report}")
    print(f"🎲 Monte Carlo JSON ذخیره شد: {mc_json}")
    print(f"📝 Monte Carlo report ذخیره شد: {mc_report}")
    print(f"📦 Risk lab combined report ذخیره شد: {combined_path}")

    if args.send:
        send_telegram_message(combined)


if __name__ == "__main__":
    main()
