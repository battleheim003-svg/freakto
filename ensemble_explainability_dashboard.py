import argparse
from engine.research_upgrade_suite import run_ensemble_explainability, format_section_console, save_section
from telegram_notifier import send_telegram_message


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--limit', type=int, default=25)
    p.add_argument('--send', action='store_true')
    args=p.parse_args()
    report=run_ensemble_explainability(limit_recent=args.limit)
    text=format_section_console('ensemble_explainability', report)
    print(text)
    j,m=save_section('ensemble_explainability', report)
    print(f"🧩 Explainability JSON ذخیره شد: {j}")
    print(f"📝 Explainability report ذخیره شد: {m}")
    if args.send: send_telegram_message(text)
if __name__=='__main__': main()
