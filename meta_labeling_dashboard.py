import argparse
from engine.research_upgrade_suite import run_meta_labeling, format_section_console, save_section
from telegram_notifier import send_telegram_message


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--horizon', default='24h', choices=['4h','12h','24h'])
    p.add_argument('--min-samples', type=int, default=120)
    p.add_argument('--send', action='store_true')
    args=p.parse_args()
    report=run_meta_labeling(horizon=args.horizon, min_samples=args.min_samples)
    text=format_section_console('meta_labeling', report)
    print(text)
    j,m=save_section('meta_labeling', report)
    print(f"🤖 Meta-labeling JSON ذخیره شد: {j}")
    print(f"📝 Meta-labeling report ذخیره شد: {m}")
    if args.send: send_telegram_message(text)
if __name__=='__main__': main()
