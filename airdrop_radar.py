"""
CLI entrypoint for Freakto Airdrop Radar.

Examples:
    python airdrop_radar.py --once --dry-run
    python airdrop_radar.py --once --send
    python airdrop_radar.py --loop --send
"""

from __future__ import annotations

import argparse
import time


from airdrop.radar import AirdropRadar, env_int


def main() -> None:
    parser = argparse.ArgumentParser(description="Freakto Airdrop Radar")
    parser.add_argument("--once", action="store_true", help="Run one scan and exit.")
    parser.add_argument("--loop", action="store_true", help="Run forever using AIRDROP_CHECK_INTERVAL_MINUTES.")
    parser.add_argument("--send", action="store_true", help="Send reportable opportunities to Telegram.")
    parser.add_argument("--dry-run", action="store_true", help="Do not send Telegram messages.")
    parser.add_argument("--include-sent", action="store_true", help="Include already-sent opportunities again.")
    parser.add_argument("--min-score", type=int, default=None, help="Override AIRDROP_MIN_SCORE.")
    parser.add_argument("--max-items", type=int, default=None, help="Override AIRDROP_MAX_ITEMS_PER_RUN.")
    args = parser.parse_args()

    radar = AirdropRadar(min_score=args.min_score, max_items=args.max_items)

    def job():
        radar.run(send=args.send, dry_run=args.dry_run, include_sent=args.include_sent)

    print("🪂 Freakto Airdrop Radar started")
    job()

    if args.once or not args.loop:
        print("✅ اجرای یک‌باره Airdrop Radar تمام شد.")
        return

    interval = env_int("AIRDROP_CHECK_INTERVAL_MINUTES", 360)
    try:
        import schedule
    except ImportError as exc:
        raise SystemExit("پکیج schedule نصب نیست. اول اجرا کن: pip install -r requirements.txt") from exc

    schedule.every(interval).minutes.do(job)
    print(f"🔁 Loop mode: every {interval} minutes")
    while True:
        schedule.run_pending()
        time.sleep(15)


if __name__ == "__main__":
    main()
