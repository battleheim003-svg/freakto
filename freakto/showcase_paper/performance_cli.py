"""Read-only CLI for causal Showcase quality diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from freakto.showcase_paper.performance import compare_quality_profiles, losing_trade_mfe_distribution


def _load_trades(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Showcase session must contain a JSON object")
    return [item for item in payload.get("trades", []) if isinstance(item, dict)]


def _human(report: dict[str, object], mfe: dict[str, object]) -> str:
    baseline = report["baseline"]
    lines = [
        "Showcase causal quality comparison (Research-only)",
        f"Baseline  N={baseline['samples']}  Win={baseline['win_rate'] * 100:.1f}%  PF={baseline['profit_factor']:.2f}  Exp={baseline['expectancy_usdt']:+.4f} USDT",
    ]
    for key, comparison in report["profiles"].items():
        candidate = comparison["candidate"]
        lines.append(
            f"{key:<9} N={candidate['samples']}  Win={candidate['win_rate'] * 100:.1f}%  PF={candidate['profit_factor']:.2f}  Exp={candidate['expectancy_usdt']:+.4f} USDT"
        )
        for segment in comparison["rejections_by_symbol_side"][:10]:
            reasons = ", ".join(f"{name}={count}" for name, count in segment["reasons"].items())
            lines.append(f"  reject {segment['symbol']} {segment['side']}: {reasons}")
    lines.append(
        f"Losing-trade MFE  N={mfe['samples']}  median={mfe['median_r']:.3f}R  p75={mfe['p75_r']:.3f}R  p90={mfe['p90_r']:.3f}R"
    )
    lines.append("LIVE ORDERS: OFF | official_evidence_eligible=false")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", type=Path, default=Path("logs/showcase_paper/session.json"))
    parser.add_argument("--profiles", nargs="+", default=["BALANCED", "WIN_RATE"])
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    trades = _load_trades(args.session)
    report = compare_quality_profiles(trades, profile_keys=args.profiles)
    mfe = losing_trade_mfe_distribution(trades)
    if args.as_json:
        print(json.dumps({"comparison": report, "losing_trade_mfe": mfe}, ensure_ascii=False, indent=2))
    else:
        print(_human(report, mfe))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
