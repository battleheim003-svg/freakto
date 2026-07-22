"""Canonical paper performance report entry point."""

from __future__ import annotations

import argparse
import json
import sys

from engine.paper_performance_dashboard import build_dashboard


def _format(summary, outputs) -> str:
    pf = "INF" if summary.profit_factor == float("inf") else f"{summary.profit_factor:.4f}"
    lines = [
        "=" * 112,
        "Freakto Paper Performance Dashboard",
        "=" * 112,
        f"Status              : {summary.status}",
        f"Signals             : {summary.total_signals}",
        f"Closed / Open       : {summary.closed_trades} / {summary.open_trades}",
        f"Wins / Losses       : {summary.wins} / {summary.losses}",
        f"Win Rate            : {summary.win_rate_pct:.2f}%",
        f"Profit Factor       : {pf}",
        f"Expectancy          : {summary.expectancy_r:.4f}R",
        f"Cumulative R        : {summary.cumulative_r:.4f}R",
        f"Max Drawdown        : {summary.max_drawdown_r:.4f}R",
        f"Best / Worst        : {summary.best_trade_r:.4f}R / {summary.worst_trade_r:.4f}R",
        f"Initial Balance     : ${summary.initial_balance_usd:,.2f}",
        f"Current Balance     : ${summary.current_balance_usd:,.2f}",
        f"Total P&L           : ${summary.total_pnl_usd:,.2f} ({summary.total_return_pct:.2f}%)",
        f"Risk / Trade        : {summary.risk_per_trade_pct:.2f}% (compounded)",
        f"Max Drawdown USD    : ${summary.max_drawdown_usd:,.2f} ({summary.max_drawdown_pct:.2f}%)",
        f"Regimes             : {summary.regime_count}",
        f"Dashboard           : {outputs.get('markdown', '')}",
        f"Equity Curve        : {outputs.get('equity_png', '')}",
        "Safety              : research-paper only; live orders and real capital remain disabled.",
        "=" * 112,
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Freakto paper performance dashboard")
    parser.add_argument("--trades", default="logs/paper_trades.csv")
    parser.add_argument("--evaluations", default="logs/paper_trade_evaluations.csv")
    parser.add_argument("--output-dir", default="logs/paper_performance")
    parser.add_argument("--balance", type=float, default=10_000.0, help="Initial virtual account balance in USD")
    parser.add_argument("--risk-pct", type=float, default=1.0, help="Percent of current balance risked per closed trade")
    parser.add_argument("--no-plot", action="store_true")
    parser.add_argument("--send", action="store_true", help="Send compact summary to Telegram")
    args = parser.parse_args()

    summary, _ledger, regimes, _equity, outputs = build_dashboard(
        args.trades,
        args.evaluations,
        args.output_dir,
        make_plot=not args.no_plot,
        initial_balance=args.balance,
        risk_pct=args.risk_pct,
    )
    text = _format(summary, outputs)
    print(text)
    if not regimes.empty:
        print("Top regimes:")
        for row in regimes.head(8).itertuples(index=False):
            print(f"- {row.regime}: n={row.closed}, win={row.win_rate_pct:.2f}%, PF={row.profit_factor}, exp={row.expectancy_r:.4f}R")
    if args.send:
        try:
            from telegram_notifier import send_telegram_message
            send_telegram_message(text)
        except Exception as exc:
            print(f"Telegram summary warning: {type(exc).__name__}: {exc}", file=sys.stderr)
    print(json.dumps({"status": summary.status, "summary": summary.to_dict(), "outputs": outputs}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
