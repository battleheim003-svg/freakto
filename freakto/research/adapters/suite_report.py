"""Canonical full research-suite retained-engine report adapter."""

import argparse
from engine.research_upgrade_suite import run_full_research_suite, format_full_suite_console, save_full_suite
from telegram_notifier import send_telegram_message


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--send', action='store_true')
    args=p.parse_args()
    report=run_full_research_suite(save=False)
    text=format_full_suite_console(report)
    print(text)
    j,m=save_full_suite(report)
    print(f"🧠 Research suite JSON ذخیره شد: {j}")
    print(f"📝 Research suite report ذخیره شد: {m}")
    dash = report.get('sections', {}).get('static_dashboard', {}).get('html_path')
    if dash: print(f"🌐 Static dashboard ساخته شد: {dash}")
    if args.send: send_telegram_message(text)
if __name__=='__main__': main()
