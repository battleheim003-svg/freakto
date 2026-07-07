import argparse
from engine.research_upgrade_suite import run_regime_research, format_section_console, save_section
from telegram_notifier import send_telegram_message


def main():
    p=argparse.ArgumentParser(); p.add_argument('--horizon', default='24h', choices=['4h','12h','24h']); p.add_argument('--send', action='store_true'); args=p.parse_args()
    report=run_regime_research(horizon=args.horizon)
    text=format_section_console('regime_research', report)
    print(text)
    j,m=save_section('regime_research', report)
    print(f"🧬 Regime research JSON ذخیره شد: {j}")
    print(f"📝 Regime research report ذخیره شد: {m}")
    if args.send: send_telegram_message(text)
if __name__=='__main__': main()
