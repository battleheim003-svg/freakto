import argparse
from engine.research_upgrade_suite import run_airdrop_shadow_research, format_section_console, save_section
from telegram_notifier import send_telegram_message


def main():
    p=argparse.ArgumentParser(); p.add_argument('--send', action='store_true'); args=p.parse_args()
    report=run_airdrop_shadow_research()
    text=format_section_console('airdrop_shadow_research', report)
    print(text)
    j,m=save_section('airdrop_shadow_research', report)
    print(f"🪂 Airdrop shadow JSON ذخیره شد: {j}")
    print(f"📝 Airdrop shadow report ذخیره شد: {m}")
    if args.send: send_telegram_message(text)
if __name__=='__main__': main()
