"""Command line entry point for research-only new-market data collection."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from freakto.markets import (
    DukascopyAdapter,
    TwelveDataAdapter,
    load_market_config,
    persist_replay_dataset,
)
from freakto.markets.compatibility import audit_replay_compatibility

ROOT = Path(__file__).resolve().parents[2]
CONFIGS = {
    "forex": ROOT / "config" / "markets" / "forex.json",
    "gold": ROOT / "config" / "markets" / "gold.json",
}


def _datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch and validate research-only forex/gold OHLCV."
    )
    parser.add_argument("asset_class", choices=sorted(CONFIGS))
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--timeframe", default="1d")
    parser.add_argument("--start", required=True, help="Inclusive UTC ISO timestamp")
    parser.add_argument("--end", required=True, help="Exclusive audit boundary in UTC")
    parser.add_argument("--api-key-env", default="TWELVE_DATA_API_KEY")
    parser.add_argument("--data-dir", default=str(ROOT / "data" / "market_replay"))
    parser.add_argument(
        "--raw-cache-dir",
        default=str(ROOT / "data" / "market_replay" / ".dukascopy_raw"),
    )
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Persist only a brand-new schema-valid dataset; never overwrite.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_market_config(CONFIGS[args.asset_class])
    symbol = str(args.symbol).strip().upper()
    if symbol not in config.symbols:
        raise SystemExit(f"Symbol {symbol} is not allowed by {args.asset_class} config.")
    start = _datetime(args.start)
    end = _datetime(args.end)
    if config.provider == "dukascopy":
        adapter = DukascopyAdapter(cache_dir=args.raw_cache_dir)
    elif config.provider == "twelve_data":
        api_key = os.getenv(args.api_key_env, "").strip()
        if not api_key:
            raise SystemExit(f"Missing API key environment variable: {args.api_key_env}")
        adapter = TwelveDataAdapter(api_key)
    else:
        raise SystemExit(f"Unsupported configured provider: {config.provider}")
    frame, contract = adapter.fetch_range(
        symbol,
        args.timeframe,
        start=start,
        end=end,
    )
    compatibility = audit_replay_compatibility(
        frame,
        timeframe=args.timeframe,
        config=config,
    )
    output = {
        "contract": asdict(contract),
        "compatibility": asdict(compatibility),
        "persisted": False,
        "dataset": None,
        "manifest": None,
    }
    if args.persist:
        if not contract.ok:
            output["persistence_blocker"] = "DATA_CONTRACT_FAILED"
        else:
            dataset, manifest, _ = persist_replay_dataset(
                frame,
                symbol=symbol,
                timeframe=args.timeframe,
                config=config,
                data_dir=args.data_dir,
            )
            output.update(
                {
                    "persisted": True,
                    "dataset": str(dataset),
                    "manifest": str(manifest),
                }
            )
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if contract.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
