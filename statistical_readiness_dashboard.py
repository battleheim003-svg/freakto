import argparse
from engine.research_upgrade_suite import run_statistical_readiness, format_section_console, save_section
from telegram_notifier import send_telegram_message


def main():
    p=argparse.ArgumentParser(); p.add_argument('--horizon', default='24h', choices=['4h','12h','24h']); p.add_argument('--send', action='store_true'); args=p.parse_args()
    report=run_statistical_readiness(horizon=args.horizon)
    text=format_section_console('statistical_readiness', report)
    print(text)
    j,m=save_section('statistical_readiness', report)
    print(f"🚦 Statistical readiness JSON ذخیره شد: {j}")
    print(f"📝 Statistical readiness report ذخیره شد: {m}")
    if args.send: send_telegram_message(text)
if __name__=='__main__': main()
