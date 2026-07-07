import argparse
from engine.research_upgrade_suite import run_research_db_export, format_section_console, save_section
from telegram_notifier import send_telegram_message


def main():
    p=argparse.ArgumentParser(); p.add_argument('--send', action='store_true'); args=p.parse_args()
    report=run_research_db_export()
    text=format_section_console('research_db', report)
    print(text)
    j,m=save_section('research_db', report)
    print(f"🗄️ Research DB JSON ذخیره شد: {j}")
    print(f"📝 Research DB report ذخیره شد: {m}")
    if args.send: send_telegram_message(text)
if __name__=='__main__': main()
