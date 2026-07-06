"""
telegram_diagnostics.py

Freakto v3.4.0

Small CLI utility for testing Telegram delivery, Markdown fallback, and message chunking.

Usage:
    python telegram_diagnostics.py
    python telegram_diagnostics.py --long
"""

from __future__ import annotations

import argparse

from telegram_notifier import send_telegram_message_detailed


def _long_message() -> str:
    lines = ["🧪 Freakto Telegram long message diagnostic"]
    for i in range(1, 180):
        lines.append(
            f"Line {i}: Score=70 | MTF=NEUTRAL/65% | RR=1.20 | Warning: test-message-with-dash"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Freakto Telegram diagnostics")
    parser.add_argument("--long", action="store_true", help="Send a long chunked test message")
    args = parser.parse_args()

    if args.long:
        message = _long_message()
    else:
        message = (
            "🧪 Freakto Telegram diagnostic\n"
            "Testing Markdown chars: Score=70 | MTF=NEUTRAL/65% | RR=1.2\n"
            "If this arrives, v3.4 sanitizer is working."
        )

    result = send_telegram_message_detailed(message)

    print("=" * 70)
    print("Telegram Diagnostic Result")
    print("=" * 70)
    print(f"OK              : {result.ok}")
    print(f"Attempted chunks: {result.attempted_chunks}")
    print(f"Sent chunks     : {result.sent_chunks}")
    print(f"Failed chunks   : {result.failed_chunks}")
    print(f"Last error      : {result.last_error}")
    print("=" * 70)


if __name__ == "__main__":
    main()
