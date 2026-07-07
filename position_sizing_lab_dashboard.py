import argparse
from engine.research_upgrade_suite import run_position_sizing_lab, format_section_console, save_section
from telegram_notifier import send_telegram_message


def main():
    p=argparse.ArgumentParser(); p.add_argument('--horizon', default='24h', choices=['4h','12h','24h']); p.add_argument('--max-risk-pct', type=float, default=0.50); p.add_argument('--send', action='store_true'); args=p.parse_args()
    report=run_position_sizing_lab(horizon=args.horizon, max_risk_pct=args.max_risk_pct)
    text=format_section_console('position_sizing_lab', report)
    print(text)
    j,m=save_section('position_sizing_lab', report)
    print(f"📏 Position sizing JSON ذخیره شد: {j}")
    print(f"📝 Position sizing report ذخیره شد: {m}")
    if args.send: send_telegram_message(text)
if __name__=='__main__': main()
