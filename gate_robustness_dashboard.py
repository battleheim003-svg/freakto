import argparse
from engine.research_upgrade_suite import run_gate_robustness, format_section_console, save_section
from telegram_notifier import send_telegram_message


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--horizon', default='24h', choices=['4h','12h','24h'])
    p.add_argument('--min-samples', type=int, default=30)
    p.add_argument('--windows', type=int, default=5)
    p.add_argument('--embargo-rows', type=int, default=2)
    p.add_argument('--fee-bps', type=float, default=10.0)
    p.add_argument('--slippage-bps', type=float, default=5.0)
    p.add_argument('--send', action='store_true')
    args = p.parse_args()
    report = run_gate_robustness(horizon=args.horizon, min_samples=args.min_samples, windows=args.windows, embargo_rows=args.embargo_rows, fee_bps=args.fee_bps, slippage_bps=args.slippage_bps)
    text = format_section_console('gate_robustness', report)
    print(text)
    j, m = save_section('gate_robustness', report)
    print(f"🧠 Gate robustness JSON ذخیره شد: {j}")
    print(f"📝 Gate robustness report ذخیره شد: {m}")
    if args.send:
        send_telegram_message(text)

if __name__ == '__main__':
    main()
