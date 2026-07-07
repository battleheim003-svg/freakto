import argparse
from engine.research_upgrade_suite import run_pipeline_health, format_section_console, save_section
from telegram_notifier import send_telegram_message


def main():
    p=argparse.ArgumentParser(); p.add_argument('--max-hours', type=float, default=8.0); p.add_argument('--send', action='store_true'); args=p.parse_args()
    report=run_pipeline_health(max_hours_without_run=args.max_hours)
    text=format_section_console('pipeline_health', report)
    print(text)
    j,m=save_section('pipeline_health', report)
    print(f"🚨 Pipeline health JSON ذخیره شد: {j}")
    print(f"📝 Pipeline health report ذخیره شد: {m}")
    if args.send: send_telegram_message(text)
if __name__=='__main__': main()
