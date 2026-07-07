import argparse
from engine.research_upgrade_suite import run_cost_adjusted_backtest, format_section_console, save_section
from telegram_notifier import send_telegram_message


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--horizon', default='24h', choices=['4h','12h','24h'])
    p.add_argument('--fee-bps', type=float, default=10.0)
    p.add_argument('--slippage-bps', type=float, default=5.0)
    p.add_argument('--send', action='store_true')
    args=p.parse_args()
    report=run_cost_adjusted_backtest(horizon=args.horizon, fee_bps=args.fee_bps, slippage_bps=args.slippage_bps)
    text=format_section_console('cost_adjusted_backtest', report)
    print(text)
    j,m=save_section('cost_adjusted_backtest', report)
    print(f"💸 Cost-adjusted JSON ذخیره شد: {j}")
    print(f"📝 Cost-adjusted report ذخیره شد: {m}")
    if args.send: send_telegram_message(text)
if __name__=='__main__': main()
