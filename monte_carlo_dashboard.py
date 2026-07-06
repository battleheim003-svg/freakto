"""Freakto Monte Carlo Risk Lab Dashboard CLI v5.0"""

import argparse

from engine.monte_carlo import run_monte_carlo, format_monte_carlo_console, save_monte_carlo
from telegram_notifier import send_telegram_message


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Send Monte Carlo report to Telegram.")
    parser.add_argument("--iterations", type=int, default=2000)
    parser.add_argument("--trades", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--decision-fallback", action="store_true", help="Use decision returns even when paper R data exists.")
    args = parser.parse_args()

    result = run_monte_carlo(
        iterations=args.iterations,
        trades_per_run=args.trades,
        seed=args.seed,
        prefer_paper=not args.decision_fallback,
    )
    text = format_monte_carlo_console(result)
    print(text)
    json_path, report_path = save_monte_carlo(result)
    print(f"🎲 Monte Carlo JSON ذخیره شد: {json_path}")
    print(f"📝 Monte Carlo report ذخیره شد: {report_path}")
    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
