import argparse
from engine.research_upgrade_suite import run_data_enrichment_readiness, format_section_console, save_section
from telegram_notifier import send_telegram_message


def main():
    p=argparse.ArgumentParser(); p.add_argument('--send', action='store_true'); args=p.parse_args()
    report=run_data_enrichment_readiness()
    text=format_section_console('data_enrichment', report)
    print(text)
    j,m=save_section('data_enrichment', report)
    print(f"🛰️ Data enrichment JSON ذخیره شد: {j}")
    print(f"📝 Data enrichment report ذخیره شد: {m}")
    if args.send: send_telegram_message(text)
if __name__=='__main__': main()
