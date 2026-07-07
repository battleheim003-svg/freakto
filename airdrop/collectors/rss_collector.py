from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

from airdrop.collectors.base import BaseCollector
from airdrop.http_client import HttpClient
from airdrop.models import AirdropCandidate, normalize_slug


class RssAirdropCollector(BaseCollector):
    """Optional generic RSS collector for news/airdrop feeds.

    Provide feed URLs via AIRDROP_RSS_FEEDS. This collector is intentionally
    conservative: it only creates WATCHLIST-style candidates, because RSS posts
    are not official proof of an airdrop.
    """

    name = "rss_feed"

    def __init__(self, feed_urls: list[str], timeout: int = 20, max_items_per_feed: int = 20):
        self.feed_urls = [u.strip() for u in feed_urls if u.strip()]
        self.client = HttpClient(timeout=timeout, headers={"Accept": "application/rss+xml,application/atom+xml,text/xml,*/*"})
        self.max_items_per_feed = max_items_per_feed

    def collect(self) -> list[AirdropCandidate]:
        results: list[AirdropCandidate] = []
        for feed_url in self.feed_urls:
            try:
                xml_text = self.client.get_text(feed_url)
                results.extend(self._parse_feed(xml_text, feed_url)[: self.max_items_per_feed])
            except Exception as exc:
                print(f"⚠️ RSS collector failed for {feed_url}: {exc}")
        return results

    def _parse_feed(self, xml_text: str, feed_url: str) -> list[AirdropCandidate]:
        root = ET.fromstring(xml_text)
        items = root.findall(".//item") or root.findall("{http://www.w3.org/2005/Atom}entry")
        candidates: list[AirdropCandidate] = []
        for item in items:
            title = _first_text(item, ["title", "{http://www.w3.org/2005/Atom}title"])
            link = _first_text(item, ["link", "{http://www.w3.org/2005/Atom}link"])
            if not link:
                atom_link = item.find("{http://www.w3.org/2005/Atom}link")
                link = atom_link.attrib.get("href", "") if atom_link is not None else ""
            summary = _first_text(item, ["description", "summary", "{http://www.w3.org/2005/Atom}summary"])
            text = f"{title} {summary}".lower()
            if not any(k in text for k in ["airdrop", "points", "testnet", "quest", "incentive", "tokenless"]):
                continue
            project_name = _guess_project_name(title)
            candidates.append(
                AirdropCandidate(
                    name=project_name,
                    slug=normalize_slug(project_name + "-" + title[:50]),
                    source=self.name,
                    source_url=link or feed_url,
                    official_url="",
                    category="news/watchlist",
                    task_type="research",
                    token_status="unknown",
                    description=_clean(summary or title)[:300],
                    tags=["rss", "watchlist"],
                    raw={"feed_url": feed_url, "title": title, "published": _first_text(item, ["pubDate", "published", "updated"])},
                )
            )
        return candidates


def _first_text(element: ET.Element, names: list[str]) -> str:
    for name in names:
        found = element.find(name)
        if found is not None and found.text:
            return found.text.strip()
    return ""


def _clean(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value or "").replace("\n", " ").strip()


def _guess_project_name(title: str) -> str:
    title = _clean(title)
    parts = re.split(r"[:\-|–—]", title, maxsplit=1)
    return (parts[0] or title or "Unknown RSS Opportunity").strip()[:80]
