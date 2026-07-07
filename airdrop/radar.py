from __future__ import annotations

import os
from pathlib import Path

from airdrop.collectors.configured_collector import ConfiguredWatchlistCollector
from airdrop.collectors.defillama_collector import DefiLlamaTokenlessCollector
from airdrop.collectors.rss_collector import RssAirdropCollector
from airdrop.dedup import deduplicate
from airdrop.formatter import format_console, format_telegram
from airdrop.models import ScoredAirdrop, utc_now_iso
from airdrop.scoring.engine import score_candidate
from airdrop.storage.db import AirdropDatabase

try:
    from config import BASE_DIR
except Exception:
    BASE_DIR = Path(__file__).resolve().parents[1]


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


class AirdropRadar:
    def __init__(
        self,
        min_score: int | None = None,
        max_items: int | None = None,
        db_path: str | Path | None = None,
    ):
        self.min_score = min_score if min_score is not None else env_int("AIRDROP_MIN_SCORE", 65)
        self.max_items = max_items if max_items is not None else env_int("AIRDROP_MAX_ITEMS_PER_RUN", 8)
        self.db = AirdropDatabase(db_path or os.getenv("AIRDROP_DB_PATH", str(Path(BASE_DIR) / "history" / "airdrop_radar.db")))

    def collect(self):
        collectors = [
            ConfiguredWatchlistCollector(os.getenv("AIRDROP_WATCHLIST_FILE", str(Path(BASE_DIR) / "data" / "airdrop_watchlist.json")))
        ]

        if env_bool("AIRDROP_USE_DEFILLAMA", True):
            collectors.append(
                DefiLlamaTokenlessCollector(
                    min_tvl_usd=env_float("AIRDROP_DEFILLAMA_MIN_TVL", 1_000_000),
                    max_items=env_int("AIRDROP_DEFILLAMA_MAX_ITEMS", 200),
                )
            )

        rss_feeds = [x.strip() for x in os.getenv("AIRDROP_RSS_FEEDS", "").split(",") if x.strip()]
        if rss_feeds:
            collectors.append(RssAirdropCollector(rss_feeds))

        candidates = []
        for collector in collectors:
            try:
                batch = collector.collect()
                print(f"✅ {collector.name}: {len(batch)} candidate(s)")
                candidates.extend(batch)
            except Exception as exc:
                print(f"⚠️ {collector.name} failed: {exc}")
        return deduplicate(candidates)

    def run(self, send: bool = False, dry_run: bool = False, include_sent: bool = False) -> list[ScoredAirdrop]:
        self.db.init()
        candidates = self.collect()
        scored = [score_candidate(candidate) for candidate in candidates]
        scored.sort(key=lambda item: item.final_score, reverse=True)

        for item in scored:
            self.db.upsert_scored(item)

        reportable = [item for item in scored if item.final_score >= self.min_score]
        if not include_sent:
            reportable = [item for item in reportable if not self.db.was_sent(item.candidate.identity)]
        reportable = reportable[: self.max_items]

        print("\n" + "#" * 70)
        print(f"Freakto Airdrop Radar | candidates={len(candidates)} | reportable={len(reportable)} | min_score={self.min_score}")
        print("#" * 70)
        for item in reportable:
            print(format_console(item))

        if send and reportable and not dry_run:
            from telegram_notifier import send_telegram_message

            ok = send_telegram_message(format_telegram(reportable))
            if ok:
                now = utc_now_iso()
                for item in reportable:
                    self.db.mark_sent(item.candidate.identity, now)
        elif dry_run:
            print("\nℹ️ Dry-run فعال است؛ پیام تلگرام ارسال نشد.")

        return reportable
