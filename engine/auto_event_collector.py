
"""
Freakto v6.5.1 - Automatic Event Collector Source Resilience Patch

Research-only official/trusted event collection layer for Causal Intelligence.
It collects public announcements/news-like event feeds, classifies significant
items, writes data/auto_events.csv, and never creates Paper/Live trades.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

from engine.research_utils import LOG_DIR, RESEARCH_DIR, run_id, utc_now_iso, write_json, write_text, save_dataframe_csv

VERSION = "v6.5.1"
EVENT_DIR = LOG_DIR / "events"
SUITE_DIR = RESEARCH_DIR / "v6_suite"
AUTO_EVENTS_FILE = Path("data") / "auto_events.csv"
AUTO_EVENT_SOURCES_EXAMPLE = Path("data") / "auto_event_sources.example.json"
EVENT_TIMEOUT_SECONDS = float(os.getenv("FREAKTO_EVENT_TIMEOUT", "14"))
EVENT_USER_AGENT = os.getenv("FREAKTO_EVENT_USER_AGENT", "Mozilla/5.0 (compatible; FreaktoResearchBot/6.5.1; research-only; +local)")
DEFAULT_LOOKBACK_HOURS = int(os.getenv("FREAKTO_EVENT_LOOKBACK_HOURS", "168"))
DEFAULT_MAX_ITEMS_PER_SOURCE = int(os.getenv("FREAKTO_EVENT_MAX_ITEMS", "25"))

TRUST_RANK = {
    "TIER_1_OFFICIAL_REGULATOR": 1,
    "TIER_1_OFFICIAL_MACRO": 1,
    "TIER_1_OFFICIAL_EXCHANGE_NEWS": 1,
    "TIER_1_OFFICIAL_PROTOCOL": 1,
    "TIER_2_OFFICIAL_COMPANY_BLOG": 2,
    "TIER_2_REPUTABLE_MEDIA": 2,
    "TIER_3_AGGREGATOR_OR_SENTIMENT": 3,
}

AUTO_EVENT_COLUMNS = [
    "event_id", "timestamp_utc", "symbol", "event_type", "source_id", "source_name", "source_tier",
    "source_category", "source_url", "impact", "direction", "confidence", "event_risk", "auto_score",
    "title", "description", "tags", "matched_keywords", "collected_utc",
]


@dataclass
class EventSource:
    source_id: str
    name: str
    url: str
    source_type: str
    reliability_tier: str
    category: str
    enabled_by_default: bool = True
    fallback_urls: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class AutoEventRecord:
    event_id: str
    timestamp_utc: str
    symbol: str
    event_type: str
    source_id: str
    source_name: str
    source_tier: str
    source_category: str
    source_url: str
    impact: str
    direction: str
    confidence: str
    event_risk: str
    auto_score: int
    title: str
    description: str
    tags: str
    matched_keywords: str
    collected_utc: str


@dataclass
class SourceHealth:
    source_id: str
    source_name: str
    reliability_tier: str
    source_type: str
    status: str
    fetched_items: int = 0
    significant_events: int = 0
    error: str = ""
    url: str = ""


@dataclass
class EventCollectionReport:
    run_id: str
    generated_utc: str
    version: str
    status: str
    fetch_live: bool
    apply_changes: bool
    lookback_hours: int
    sources_total: int
    sources_ok: int
    sources_failed: int
    events_fetched: int
    significant_events: int
    new_events_written: int
    total_auto_events: int
    high_impact_events: int
    official_tier_events: int
    source_health: List[Dict[str, Any]] = field(default_factory=list)
    top_events: List[Dict[str, Any]] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


def _norm(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return default
    return text


def _upper(value: Any, default: str = "") -> str:
    return _norm(value, default).upper().replace("-", "_").replace(" ", "_")


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_dt(value: Any) -> Optional[datetime]:
    text = _norm(value)
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass
    try:
        dt = parsedate_to_datetime(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass
    if pd is not None:
        try:
            dt = pd.to_datetime(text, utc=True, errors="coerce")
            if not pd.isna(dt):
                return dt.to_pydatetime().astimezone(timezone.utc)
        except Exception:
            pass
    return None


def _http_get(url: str, accept: str = "*/*", timeout: float = EVENT_TIMEOUT_SECONDS) -> Tuple[str, str]:
    headers = {"User-Agent": EVENT_USER_AGENT, "Accept": accept}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec - public information sources only
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace"), ""
    except Exception as error:
        return "", f"{type(error).__name__}: {error}"


def build_event_source_registry(include_media: bool = False) -> List[EventSource]:
    sources = [
        EventSource(
            "sec_press_releases", "SEC Press Releases RSS", "https://www.sec.gov/news/pressreleases.rss", "rss",
            "TIER_1_OFFICIAL_REGULATOR", "regulatory", True,
            ["https://www.sec.gov/news/press-release/rss", "https://www.sec.gov/news/press-releases"],
            "Official SEC news releases; high value for ETF/enforcement/regulatory catalysts.",
        ),
        EventSource(
            "sec_litigation_releases", "SEC Litigation Releases", "https://www.sec.gov/litigation/litreleases.rss", "rss",
            "TIER_1_OFFICIAL_REGULATOR", "regulatory", True,
            ["https://www.sec.gov/news/litigation/litreleases.rss", "https://www.sec.gov/enforcement-litigation/litigation-releases"],
            "Official SEC litigation releases; bearish/regulatory-risk context when crypto-related. v6.5.1 can fall back to the official HTML listing page when RSS moves.",
        ),
        EventSource(
            "federal_reserve_press", "Federal Reserve Press Releases RSS", "https://www.federalreserve.gov/feeds/press_all.xml", "rss",
            "TIER_1_OFFICIAL_MACRO", "macro", True,
            ["https://www.federalreserve.gov/feeds/press_monetary.xml", "https://www.federalreserve.gov/newsevents/pressreleases.htm"],
            "Official Fed press feed; macro and rate-policy context.",
        ),
        EventSource(
            "federal_reserve_speeches", "Federal Reserve Speeches RSS", "https://www.federalreserve.gov/feeds/speeches.xml", "rss",
            "TIER_1_OFFICIAL_MACRO", "macro", True,
            ["https://www.federalreserve.gov/feeds/testimony.xml", "https://www.federalreserve.gov/newsevents/speeches.htm"],
            "Official Fed speeches/testimony feed; used as event-risk context, not standalone direction.",
        ),
        EventSource(
            "ethereum_foundation_blog", "Ethereum Foundation Blog", "https://blog.ethereum.org/feed.xml", "rss",
            "TIER_1_OFFICIAL_PROTOCOL", "protocol", True,
            ["https://blog.ethereum.org/rss.xml", "https://blog.ethereum.org/"],
            "Official Ethereum Foundation blog feed for protocol/security/upgrade items.",
        ),
        EventSource(
            "coinbase_blog", "Coinbase Blog", "https://www.coinbase.com/blog/rss.xml", "rss",
            "TIER_2_OFFICIAL_COMPANY_BLOG", "exchange_company", True,
            ["https://www.coinbase.com/blog/feed.xml", "https://www.coinbase.com/blog/feed", "https://www.coinbase.com/blog"],
            "Coinbase official blog; useful for company/product/listing context. v6.5.1 uses multiple feed/page fallbacks.",
        ),
        EventSource(
            "binance_announcements", "Binance Announcements", "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=1&pageSize=30", "binance_json",
            "TIER_1_OFFICIAL_EXCHANGE_NEWS", "exchange", True,
            [
                "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&catalogId=48&pageNo=1&pageSize=30",
                "https://www.binance.com/en/support/announcement/list/48",
                "https://www.binance.com/en/support/announcement",
            ],
            "Binance official announcement source; v6.5.1 tries JSON plus HTML fallbacks because the public endpoint can change.",
        ),
    ]
    if include_media:
        sources.append(EventSource(
            "coindesk_rss", "CoinDesk RSS", "https://www.coindesk.com/arc/outboundfeeds/rss/", "rss",
            "TIER_2_REPUTABLE_MEDIA", "media", True,
            ["https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml", "https://www.coindesk.com/"],
            "Reputable crypto media context only; lower priority than official sources.",
        ))
    return sources


def ensure_sources_example() -> None:
    AUTO_EVENT_SOURCES_EXAMPLE.parent.mkdir(parents=True, exist_ok=True)
    registry = [asdict(s) for s in build_event_source_registry(include_media=True)]
    AUTO_EVENT_SOURCES_EXAMPLE.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")


def _rss_entries(xml_text: str) -> List[Dict[str, Any]]:
    root = ET.fromstring(xml_text.encode("utf-8"))
    entries: List[Dict[str, Any]] = []
    # RSS
    for item in root.findall(".//item"):
        title = _norm(item.findtext("title"))
        link = _norm(item.findtext("link"))
        pub = _norm(item.findtext("pubDate") or item.findtext("date"))
        desc = _strip_html(_norm(item.findtext("description") or item.findtext("summary")))
        if title:
            entries.append({"title": title, "url": link, "published": pub, "description": desc})
    if entries:
        return entries
    # Atom with namespace-insensitive parsing.
    for entry in root.iter():
        if entry.tag.split("}")[-1] != "entry":
            continue
        title = ""; link = ""; pub = ""; desc = ""
        for child in entry:
            tag = child.tag.split("}")[-1]
            if tag == "title":
                title = _norm(child.text)
            elif tag == "link":
                link = _norm(child.attrib.get("href") or child.text)
            elif tag in {"updated", "published"} and not pub:
                pub = _norm(child.text)
            elif tag in {"summary", "content"} and not desc:
                desc = _strip_html(_norm(child.text))
        if title:
            entries.append({"title": title, "url": link, "published": pub, "description": desc})
    return entries




def _html_entries(html_text: str, base_url: str, max_items: int) -> List[Dict[str, Any]]:
    """Best-effort fallback parser for official listing pages when RSS/API changes.

    This is intentionally conservative: it only extracts title/link/date-like snippets
    from the same official source page and then the normal classifier decides whether
    the item is significant. It is not used as a trading signal by itself.
    """
    text = html_text or ""
    entries: List[Dict[str, Any]] = []
    seen = set()

    # JSON-LD / embedded metadata titles sometimes appear in HTML even when pages are JS-heavy.
    meta_titles = re.findall(r'"(?:headline|name|title)"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', text, flags=re.I)
    meta_dates = re.findall(r'"(?:datePublished|dateModified|publishDate|releaseDate)"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', text, flags=re.I)
    for idx, raw_title in enumerate(meta_titles[:max_items * 2]):
        title = _strip_html(raw_title.encode("utf-8", errors="ignore").decode("unicode_escape", errors="ignore"))
        if len(title) < 12:
            continue
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        entries.append({"title": title, "url": base_url, "published": meta_dates[idx] if idx < len(meta_dates) else "", "description": title})
        if len(entries) >= max_items:
            return entries

    # Anchor fallback for official listing pages.
    for href, raw_title in re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', text, flags=re.I | re.S):
        title = _strip_html(raw_title)
        if len(title) < 12:
            continue
        title_l = title.lower()
        # Avoid navigation/header noise.
        if title_l in seen or any(x in title_l for x in ["privacy", "terms", "subscribe", "cookie", "contact us", "careers"]):
            continue
        if len(title.split()) < 3:
            continue
        seen.add(title_l)
        url = urllib.parse.urljoin(base_url, html.unescape(href))
        # Use nearby context to pick up a date if present.
        published = ""
        idx = text.find(href)
        window = _strip_html(text[max(0, idx - 240): idx + 360]) if idx >= 0 else ""
        m = re.search(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4}\b', window, flags=re.I)
        if m:
            published = m.group(0)
        entries.append({"title": title, "url": url, "published": published, "description": window or title})
        if len(entries) >= max_items:
            break
    return entries


def _fetch_rss_or_html(url: str, max_items: int) -> Tuple[List[Dict[str, Any]], str]:
    text, error = _http_get(url, accept="application/rss+xml, application/atom+xml, application/xml, text/xml, text/html, */*")
    if error:
        return [], error
    try:
        return _rss_entries(text)[:max_items], ""
    except Exception as xml_error:
        fallback_rows = _html_entries(text, url, max_items)
        if fallback_rows:
            return fallback_rows[:max_items], ""
        return [], f"XMLParseError: {xml_error}"

def _find_binance_articles(obj: Any) -> List[Dict[str, Any]]:
    found: List[Dict[str, Any]] = []
    if isinstance(obj, dict):
        title = obj.get("title") or obj.get("name")
        if title and (obj.get("code") or obj.get("id") or obj.get("releaseDate")):
            ts = obj.get("releaseDate") or obj.get("publishDate") or obj.get("createdAt") or obj.get("date")
            if isinstance(ts, (int, float)) and ts > 10_000_000_000:
                published = datetime.fromtimestamp(ts/1000, timezone.utc).isoformat()
            elif isinstance(ts, (int, float)):
                published = datetime.fromtimestamp(ts, timezone.utc).isoformat()
            else:
                published = _norm(ts)
            code = _norm(obj.get("code") or obj.get("id"))
            url = f"https://www.binance.com/en/support/announcement/{code}" if code else "https://www.binance.com/en/support/announcement"
            found.append({"title": _strip_html(str(title)), "url": url, "published": published, "description": _strip_html(_norm(obj.get("summary") or obj.get("subTitle") or ""))})
        for v in obj.values():
            found.extend(_find_binance_articles(v))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(_find_binance_articles(item))
    return found


def fetch_source_items(source: EventSource, max_items: int) -> Tuple[List[Dict[str, Any]], str]:
    urls = [source.url] + [u for u in (source.fallback_urls or []) if u and u != source.url]
    errors: List[str] = []

    if source.source_type == "rss":
        for url in urls:
            rows, error = _fetch_rss_or_html(url, max_items)
            if rows:
                return rows[:max_items], ""
            if error:
                errors.append(f"{url} -> {error}")
        return [], " | ".join(errors[-3:]) or "no_items"

    if source.source_type == "binance_json":
        for url in urls:
            if "bapi" in url:
                text, error = _http_get(url, accept="application/json, text/plain, */*")
                if error:
                    errors.append(f"{url} -> {error}")
                    continue
                try:
                    payload = json.loads(text)
                    rows = _find_binance_articles(payload)
                    seen = set(); deduped = []
                    for r in rows:
                        key = (_norm(r.get("title")).lower(), _norm(r.get("url")))
                        if key in seen:
                            continue
                        seen.add(key); deduped.append(r)
                    if deduped:
                        return deduped[:max_items], ""
                    errors.append(f"{url} -> no_json_articles")
                except Exception as error:
                    errors.append(f"{url} -> JSONParseError: {error}")
            else:
                rows, error = _fetch_rss_or_html(url, max_items)
                if rows:
                    return rows[:max_items], ""
                if error:
                    errors.append(f"{url} -> {error}")
        return [], " | ".join(errors[-3:]) or "no_items"

    return [], f"unsupported_source_type:{source.source_type}"


BULLISH_PATTERNS = [
    "approve", "approval", "approved", "launch", "listing", "list", "etf approval", "spot etf", "rate cut", "dovish", "inflow",
    "upgrade", "mainnet", "partnership", "integrat", "support", "expand", "record inflow",
]
BEARISH_PATTERNS = [
    "reject", "rejected", "denied", "lawsuit", "enforcement", "charge", "charged", "fine", "penalty", "ban", "sanction",
    "hack", "exploit", "vulnerability", "drain", "attack", "delist", "delisting", "suspend", "halt", "outflow", "rate hike", "hawkish", "higher than expected",
]
HIGH_IMPACT_PATTERNS = [
    "fomc", "federal reserve", "interest rate", "rate decision", "cpi", "inflation", "sec", "etf", "spot etf", "bitcoin etf",
    "hack", "exploit", "security breach", "binance", "coinbase", "ethereum", "hard fork", "mainnet", "lawsuit", "enforcement",
]
TYPE_PATTERNS = [
    ("macro", ["fomc", "federal reserve", "fed ", "interest rate", "cpi", "inflation", "jobs", "payroll", "treasury", "yields"]),
    ("regulatory", ["sec", "cftc", "lawsuit", "enforcement", "court", "approval", "etf", "regulat", "sanction"]),
    ("exchange_listing", ["listing", "will list", "listed", "launchpool", "launchpad", "delist", "trading pairs", "coinbase", "binance"]),
    ("security", ["hack", "exploit", "breach", "vulnerability", "attack", "drain", "phishing", "security"]),
    ("protocol", ["ethereum", "upgrade", "hard fork", "mainnet", "protocol", "eip", "validator", "staking"]),
    ("liquidity", ["stablecoin", "usdt", "usdc", "reserve", "inflow", "outflow", "liquidity", "tvl"]),
]


def classify_event(source: EventSource, item: Dict[str, Any], collected: str) -> Optional[AutoEventRecord]:
    title = _strip_html(_norm(item.get("title")))
    desc = _strip_html(_norm(item.get("description")))
    url = _norm(item.get("url") or source.url)
    text = f"{title} {desc} {source.name}".lower()
    if not title:
        return None

    matched: List[str] = []
    for words in [BULLISH_PATTERNS, BEARISH_PATTERNS, HIGH_IMPACT_PATTERNS]:
        for w in words:
            if w in text and w not in matched:
                matched.append(w)

    # Keep all official macro/regulatory/protocol/exchange headlines, but only keep media items if keywords exist.
    if source.reliability_tier == "TIER_2_REPUTABLE_MEDIA" and not matched:
        return None

    event_type = source.category
    for t, keys in TYPE_PATTERNS:
        if any(k in text for k in keys):
            event_type = t
            break

    bull = sum(1 for w in BULLISH_PATTERNS if w in text)
    bear = sum(1 for w in BEARISH_PATTERNS if w in text)
    direction = "NEUTRAL"
    if bull > bear:
        direction = "BULLISH"
    elif bear > bull:
        direction = "BEARISH"

    high = any(w in text for w in HIGH_IMPACT_PATTERNS) or source.reliability_tier.startswith("TIER_1_OFFICIAL_MACRO") or source.reliability_tier.startswith("TIER_1_OFFICIAL_REGULATOR")
    impact = "HIGH" if high and matched else "MEDIUM" if matched else "LOW"
    if event_type in {"security", "regulatory", "macro"} and source.reliability_tier.startswith("TIER_1"):
        impact = "HIGH"

    confidence = "HIGH" if source.reliability_tier.startswith("TIER_1") and impact == "HIGH" else "MEDIUM" if source.reliability_tier.startswith("TIER_1") or matched else "LOW"
    event_risk = "HIGH" if event_type in {"security", "regulatory", "macro"} and impact == "HIGH" else "MEDIUM" if impact in {"HIGH", "MEDIUM"} else "LOW"

    score_mag = 12 if impact == "HIGH" else 7 if impact == "MEDIUM" else 2
    auto_score = score_mag if direction == "BULLISH" else -score_mag if direction == "BEARISH" else 0

    symbol = "ALL"
    if any(w in text for w in ["bitcoin", "btc", "spot bitcoin", "bitcoin etf"]):
        symbol = "BTC/USDT"
    if any(w in text for w in ["ethereum", "ether", " eth ", "ethereum foundation"]):
        symbol = "ETH/USDT"
    if event_type == "macro":
        symbol = "ALL"

    ts = _parse_dt(item.get("published")) or datetime.now(timezone.utc)
    raw_id = f"{source.source_id}|{title.lower()}|{url}|{ts.date().isoformat()}"
    event_id = hashlib.sha256(raw_id.encode("utf-8", errors="ignore")).hexdigest()[:24]
    tags = [event_type, source.category, impact.lower(), direction.lower()]

    return AutoEventRecord(
        event_id=event_id,
        timestamp_utc=ts.isoformat(),
        symbol=symbol,
        event_type=event_type,
        source_id=source.source_id,
        source_name=source.name,
        source_tier=source.reliability_tier,
        source_category=source.category,
        source_url=url,
        impact=impact,
        direction=direction,
        confidence=confidence,
        event_risk=event_risk,
        auto_score=auto_score,
        title=title[:280],
        description=(desc or title)[:800],
        tags=";".join(tags),
        matched_keywords=";".join(matched[:16]),
        collected_utc=collected,
    )


def _read_existing_events() -> List[Dict[str, Any]]:
    if not AUTO_EVENTS_FILE.exists():
        return []
    try:
        with AUTO_EVENTS_FILE.open("r", newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def _write_events(rows: List[Dict[str, Any]]) -> None:
    AUTO_EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with AUTO_EVENTS_FILE.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=AUTO_EVENT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in AUTO_EVENT_COLUMNS})


def _merge_events(events: List[AutoEventRecord]) -> Tuple[int, int]:
    existing = _read_existing_events()
    by_id = {str(r.get("event_id", "")): r for r in existing if r.get("event_id")}
    new_count = 0
    for e in events:
        row = asdict(e)
        if e.event_id not in by_id:
            new_count += 1
        by_id[e.event_id] = row
    rows = list(by_id.values())
    def sort_key(r):
        return _norm(r.get("timestamp_utc"))
    rows.sort(key=sort_key, reverse=True)
    # Keep ledger bounded for GitHub branch/log size.
    max_rows = int(os.getenv("FREAKTO_AUTO_EVENTS_MAX_LEDGER_ROWS", "1200"))
    rows = rows[:max_rows]
    _write_events(rows)
    return new_count, len(rows)


def _existing_total_count() -> int:
    return len(_read_existing_events())


def run_auto_event_collector(
    *,
    fetch_live: bool = True,
    apply_changes: bool = True,
    lookback_hours: int = DEFAULT_LOOKBACK_HOURS,
    max_items_per_source: int = DEFAULT_MAX_ITEMS_PER_SOURCE,
    include_media: bool = False,
) -> EventCollectionReport:
    ensure_sources_example()
    rid = run_id("auto_events")
    generated = utc_now_iso()
    sources = [s for s in build_event_source_registry(include_media=include_media) if s.enabled_by_default]
    health: List[SourceHealth] = []
    events: List[AutoEventRecord] = []
    fetched_total = 0
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

    if fetch_live:
        for source in sources:
            items, error = fetch_source_items(source, max_items=max_items_per_source)
            fetched_total += len(items)
            source_events: List[AutoEventRecord] = []
            if not error:
                for item in items:
                    ts = _parse_dt(item.get("published"))
                    if ts is not None and ts < cutoff:
                        continue
                    ev = classify_event(source, item, generated)
                    if ev is not None:
                        source_events.append(ev)
                events.extend(source_events)
                health.append(SourceHealth(source.source_id, source.name, source.reliability_tier, source.source_type, "OK", len(items), len(source_events), "", source.url))
            else:
                health.append(SourceHealth(source.source_id, source.name, source.reliability_tier, source.source_type, "FAILED", 0, 0, error, source.url))
            time.sleep(float(os.getenv("FREAKTO_EVENT_SLEEP", "0.2")))
    else:
        # No live calls: summarize current ledger only.
        for source in sources:
            health.append(SourceHealth(source.source_id, source.name, source.reliability_tier, source.source_type, "SKIPPED_NO_FETCH", 0, 0, "", source.url))

    # Deduplicate within this run.
    dedup: Dict[str, AutoEventRecord] = {}
    for ev in events:
        dedup[ev.event_id] = ev
    events = list(dedup.values())

    new_count = 0
    total_after = _existing_total_count()
    if apply_changes and events:
        new_count, total_after = _merge_events(events)

    high_events = sum(1 for e in events if e.impact == "HIGH")
    official_events = sum(1 for e in events if TRUST_RANK.get(e.source_tier, 9) <= 1)
    ok_count = sum(1 for h in health if h.status == "OK")
    failed_count = sum(1 for h in health if h.status == "FAILED")
    official_failures = [h for h in health if h.status == "FAILED" and TRUST_RANK.get(h.reliability_tier, 9) <= 1]

    blockers: List[str] = []
    warnings: List[str] = [
        "Automatic Event Collector فقط داده و tag تحقیقاتی تولید می‌کند؛ Paper/Live فعال نمی‌کند.",
        "Event direction با keyword/rule ساده ساخته می‌شود و باید به عنوان catalyst context دیده شود، نه سیگنال مستقل.",
    ]
    recommendations: List[str] = []
    if fetch_live and ok_count == 0:
        blockers.append("هیچ source رسمی/معتبر با موفقیت fetch نشد؛ network/rate limit/URL sourceها را بررسی کن.")
    if official_failures:
        warnings.append(f"{len(official_failures)} منبع رسمی fail شد؛ v6.5.1 چند fallback را امتحان می‌کند اما شکست source چرخه Forward را متوقف نمی‌کند.")
    if high_events:
        recommendations.append("رویدادهای high-impact جمع شد؛ causal_intelligence_dashboard.py را اجرا کن تا روی تصمیم‌ها اثر context بررسی شود.")
    else:
        recommendations.append("فعلاً event high-impact جدید دیده نشد؛ collector را در GitHub Actions فعال نگه دار تا ledger بسازد.")
    recommendations.append("manual_events.csv را فقط برای رویدادهای بسیار مهمی استفاده کن که collector از دست داده یا نیاز به curated override دارند.")

    status = "AUTO_EVENT_COLLECTOR_READY"
    if blockers:
        status = "AUTO_EVENT_COLLECTOR_WITH_BLOCKERS"
    elif not fetch_live:
        status = "AUTO_EVENT_COLLECTOR_LEDGER_ONLY"
    elif events and high_events:
        status = "AUTO_EVENTS_COLLECTED_HIGH_IMPACT"
    elif events:
        status = "AUTO_EVENTS_COLLECTED"
    else:
        status = "AUTO_EVENTS_NO_SIGNIFICANT_NEW_ITEMS"

    top_events = sorted([asdict(e) for e in events], key=lambda r: (r.get("impact") == "HIGH", abs(int(r.get("auto_score") or 0))), reverse=True)[:12]
    return EventCollectionReport(
        run_id=rid,
        generated_utc=generated,
        version=VERSION,
        status=status,
        fetch_live=fetch_live,
        apply_changes=apply_changes,
        lookback_hours=lookback_hours,
        sources_total=len(sources),
        sources_ok=ok_count,
        sources_failed=failed_count,
        events_fetched=fetched_total,
        significant_events=len(events),
        new_events_written=new_count,
        total_auto_events=total_after,
        high_impact_events=high_events,
        official_tier_events=official_events,
        source_health=[asdict(h) for h in health],
        top_events=top_events,
        blockers=blockers,
        warnings=warnings,
        recommendations=recommendations,
    )


def format_auto_event_console(report: EventCollectionReport, compact: bool = True) -> str:
    data = asdict(report)
    sep = "=" * 110
    lines = [sep, f"🗞️ Freakto Automatic Event Collector {VERSION}", sep]
    lines.append(f"Status                 : {data.get('status')}")
    lines.append(f"Run ID                 : {data.get('run_id')}")
    lines.append(f"Fetch Live / Apply     : {data.get('fetch_live')} / {data.get('apply_changes')}")
    lines.append(f"Lookback Hours         : {data.get('lookback_hours')}")
    lines.append(f"Sources OK/Failed      : {data.get('sources_ok')} / {data.get('sources_failed')}")
    lines.append(f"Fetched Items          : {data.get('events_fetched')}")
    lines.append(f"Significant Events     : {data.get('significant_events')}")
    lines.append(f"New Events Written     : {data.get('new_events_written')}")
    lines.append(f"Total Auto Events      : {data.get('total_auto_events')}")
    lines.append(f"High Impact Events     : {data.get('high_impact_events')}")
    lines.append(f"Official Tier Events   : {data.get('official_tier_events')}")
    if data.get("top_events"):
        lines.append("\nTop Events:")
        for e in data.get("top_events", [])[:8]:
            lines.append(f"- {e.get('impact')} | {e.get('direction')} | {e.get('event_type')} | {e.get('source_id')} | {e.get('title')}")
    if data.get("source_health"):
        lines.append("\nSource Health:")
        for s in data.get("source_health", [])[:12]:
            err = f" | err={s.get('error')}" if s.get("error") and not compact else ""
            lines.append(f"- {s.get('source_id')}: {s.get('status')} | items={s.get('fetched_items')} | events={s.get('significant_events')} | {s.get('reliability_tier')}{err}")
    if data.get("blockers"):
        lines.append("\nBlockers:")
        lines.extend([f"⛔ {b}" for b in data.get("blockers", [])])
    if data.get("recommendations"):
        lines.append("\nRecommendations:")
        lines.extend([f"→ {r}" for r in data.get("recommendations", [])])
    if data.get("warnings"):
        lines.append("\nWarnings:")
        lines.extend([f"⚠️ {w}" for w in data.get("warnings", [])])
    lines.append(sep)
    return "\n".join(lines)


def save_auto_event_report(report: EventCollectionReport) -> Tuple[Path, Path, Path]:
    EVENT_DIR.mkdir(parents=True, exist_ok=True)
    SUITE_DIR.mkdir(parents=True, exist_ok=True)
    data = asdict(report)
    json_path = EVENT_DIR / f"auto_event_collector_{report.run_id}.json"
    md_path = EVENT_DIR / f"auto_event_collector_report_{report.run_id}.md"
    health_csv = EVENT_DIR / f"auto_event_source_health_{report.run_id}.csv"
    write_json(json_path, data)
    write_text(md_path, format_auto_event_console(report, compact=False))
    if pd is not None:
        save_dataframe_csv(health_csv, pd.DataFrame(report.source_health))
    else:
        with health_csv.open("w", newline="", encoding="utf-8-sig") as f:
            if report.source_health:
                writer = csv.DictWriter(f, fieldnames=list(report.source_health[0].keys()))
                writer.writeheader(); writer.writerows(report.source_health)
    write_json(SUITE_DIR / f"auto_event_collector_{report.run_id}.json", data)
    return json_path, md_path, health_csv
