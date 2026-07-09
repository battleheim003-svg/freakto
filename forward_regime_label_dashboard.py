"""Freakto v6.2.1 - Forward Regime Label Injection dashboard."""

from __future__ import annotations

import argparse

from engine.forward_regime_labeling import (
    VERSION,
    format_forward_regime_label_console,
    run_forward_regime_labeling,
    save_forward_regime_labeling,
)
from telegram_notifier import send_telegram_message


def build_parser():
    p = argparse.ArgumentParser(description=f"Freakto Forward Regime Label Injection {VERSION}")
    p.add_argument("--compact", action="store_true", help="Print compact report.")
    p.add_argument("--dry-run", action="store_true", help="Analyze but do not rewrite decisions/evaluations logs.")
    p.add_argument("--no-save", action="store_true", help="Do not save JSON/Markdown report.")
    p.add_argument("--send", action="store_true", help="Send report to Telegram.")
    return p


def main():
    args = build_parser().parse_args()
    report = run_forward_regime_labeling(apply_changes=not args.dry_run)
    text = format_forward_regime_label_console(report, compact=args.compact)
    print(text)
    if not args.no_save:
        json_path, md_path = save_forward_regime_labeling(report)
        print(f"🧬 Forward regime labeling JSON ذخیره شد: {json_path}")
        print(f"📝 Forward regime labeling report ذخیره شد: {md_path}")
    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
