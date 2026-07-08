import argparse

from engine.regime_gate_matrix import (
    format_regime_gate_matrix_console,
    run_regime_gate_matrix,
    save_regime_gate_matrix,
)
from telegram_notifier import send_telegram_message


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--horizon', default='24h', choices=['4h', '12h', '24h'])
    parser.add_argument('--min-samples', type=int, default=10)
    parser.add_argument('--candidate-min-samples', type=int, default=30)
    parser.add_argument('--fee-bps', type=float, default=10.0)
    parser.add_argument('--slippage-bps', type=float, default=5.0)
    parser.add_argument('--primary-only', action='store_true', help='Test only primary v6 candidate gates instead of all standard gates.')
    parser.add_argument('--compact', action='store_true')
    parser.add_argument('--send', action='store_true')
    parser.add_argument('--no-save', action='store_true')
    args = parser.parse_args()

    report = run_regime_gate_matrix(
        horizon=args.horizon,
        min_samples=args.min_samples,
        candidate_min_samples=args.candidate_min_samples,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        include_all_gates=not args.primary_only,
    )
    text = format_regime_gate_matrix_console(report, compact=args.compact)
    print(text)
    if not args.no_save:
        j, m, rg, rgs, av, prop = save_regime_gate_matrix(report)
        print(f"🧬 Regime-Gate matrix JSON ذخیره شد: {j}")
        print(f"📝 Regime-Gate matrix report ذخیره شد: {m}")
        print(f"📊 Regime × Gate CSV ذخیره شد: {rg}")
        print(f"📊 Regime × Gate × Side CSV ذخیره شد: {rgs}")
        print(f"🚫 Avoid regime CSV ذخیره شد: {av}")
        print(f"🧾 Shadow proposals JSON ذخیره شد: {prop}")
    if args.send:
        send_telegram_message(text)


if __name__ == '__main__':
    main()
