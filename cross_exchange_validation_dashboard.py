import argparse
from engine.research_upgrade_suite import run_cross_exchange_validation, format_section_console, save_section
from telegram_notifier import send_telegram_message


def main():
    p=argparse.ArgumentParser(); p.add_argument('--horizon', default='24h', choices=['4h','12h','24h']); p.add_argument('--send', action='store_true'); args=p.parse_args()
    report=run_cross_exchange_validation(horizon=args.horizon)
    text=format_section_console('cross_exchange_validation', report)
    print(text)
    j,m=save_section('cross_exchange_validation', report)
    print(f"🏦 Cross-exchange JSON ذخیره شد: {j}")
    print(f"📝 Cross-exchange report ذخیره شد: {m}")
    if args.send: send_telegram_message(text)
if __name__=='__main__': main()
