"""
portfolio_consistency_check.py

Freakto v4.6 diagnostic helper.

Runs the Portfolio Scanner once and verifies that no public ELITE/ACTIONABLE/
WATCHLIST recommendation is emitted while the Trade Intelligence layer says
Avoid, invalid R:R, or too-weak R:R.
"""

from __future__ import annotations

import argparse
import sys

from portfolio_scanner import _parse_symbols, run_portfolio_scan


ACTIVE_RECOMMENDATIONS = {"ELITE", "ACTIONABLE", "WATCHLIST"}


def _is_inconsistent(item) -> tuple[bool, str]:
    recommendation = getattr(item, "recommendation", "")
    if recommendation not in ACTIVE_RECOMMENDATIONS:
        return False, ""

    trade_grade = str(getattr(item, "trade_quality_grade", "") or "")
    trade_score = int(getattr(item, "trade_quality_score", 0) or 0)
    first_rr = float(getattr(item, "first_rr", 0.0) or 0.0)

    if trade_grade == "Avoid":
        return True, "active recommendation with Trade=Avoid"

    if recommendation in {"ELITE", "ACTIONABLE"} and first_rr < 1.20:
        return True, f"{recommendation} with RR below 1.20 ({first_rr:.2f})"

    if recommendation == "WATCHLIST" and first_rr < 1.00:
        return True, f"WATCHLIST with RR below 1.00 ({first_rr:.2f})"

    if recommendation in {"ELITE", "ACTIONABLE"} and trade_score < 55:
        return True, f"{recommendation} with Trade score below 55 ({trade_score})"

    if recommendation == "WATCHLIST" and trade_score < 45:
        return True, f"WATCHLIST with Trade score below 45 ({trade_score})"

    return False, ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Check portfolio recommendation consistency.")
    parser.add_argument("--symbols", default=None, help="Comma-separated symbols. Defaults to config.PORTFOLIO_SYMBOLS.")
    args = parser.parse_args()

    result = run_portfolio_scan(_parse_symbols(args.symbols), send=False)
    problems = []

    for item in result.ranked_items:
        bad, reason = _is_inconsistent(item)
        if bad:
            problems.append((item, reason))

    print("=" * 110)
    print("🧪 Freakto Portfolio Consistency Check v4.6")
    print("=" * 110)

    if not problems:
        print("OK: No actionable/watchlist recommendation conflicts with Trade Quality or R:R gates.")
        print("=" * 110)
        return 0

    print("FAILED: Inconsistent portfolio recommendations detected:")
    for item, reason in problems:
        print(
            f"- {item.symbol}: Rec={item.recommendation} | Trade={item.trade_quality_grade} "
            f"({item.trade_quality_score}/100) | RR={item.first_rr} | Reason={reason}"
        )
    print("=" * 110)
    return 1


if __name__ == "__main__":
    sys.exit(main())
