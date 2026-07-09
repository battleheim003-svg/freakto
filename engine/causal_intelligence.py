
"""
Freakto v7.0.0 - Causal/Event Intelligence Core

Purpose
-------
Build a research-only causal context layer around Freakto decisions:
- detect internal market causes from the already fetched OHLCV/features
- collect external context from higher-trust public data sources where available
- ingest curated manual events from data/manual_events.csv
- score catalyst alignment/conflict without ever creating Paper/Live trades

Safety
------
This module is read-only for markets and writes only research logs under
logs/causal/ and logs/research/v6_suite/. It never sends orders and never
promotes a signal to Paper/Live.
"""
from __future__ import annotations

import csv
import json
import math
import os
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

from engine.research_utils import (
    DECISIONS,
    LOG_DIR,
    RESEARCH_DIR,
    load_decisions_df,
    read_csv_df,
    run_id,
    safe_float,
    safe_int,
    utc_now_iso,
    write_json,
    write_text,
    save_dataframe_csv,
)

VERSION = "v7.0.0"
CAUSAL_DIR = LOG_DIR / "causal"
CAUSAL_SNAPSHOTS_DIR = CAUSAL_DIR / "source_snapshots"
CAUSAL_EVENTS_FILE = Path("data") / "manual_events.csv"
CAUSAL_EVENTS_EXAMPLE = Path("data") / "manual_events.example.csv"
CAUSAL_AUTO_EVENTS_FILE = Path("data") / "auto_events.csv"
CAUSAL_OBSERVATIONS_CSV = CAUSAL_DIR / "causal_observations.csv"
SUITE_DIR = RESEARCH_DIR / "v6_suite"

SOURCE_TIMEOUT_SECONDS = float(os.getenv("FREAKTO_CAUSAL_TIMEOUT", "12"))
USER_AGENT = os.getenv("FREAKTO_CAUSAL_USER_AGENT", "FreaktoResearchBot/7.0 (+research-only)")

TRUST_ORDER = {
    "TIER_1_OFFICIAL_EXCHANGE": 1,
    "TIER_1_OFFICIAL_EXCHANGE_NEWS": 1,
    "TIER_1_OFFICIAL_REGULATOR": 1,
    "TIER_1_OFFICIAL_PROTOCOL": 1,
    "TIER_1_OFFICIAL_MACRO": 1,
    "TIER_1_PROTOCOL_AGGREGATOR": 1,
    "TIER_2_MARKET_AGGREGATOR": 2,
    "TIER_2_OFFICIAL_COMPANY_BLOG": 2,
    "TIER_2_REPUTABLE_MEDIA": 2,
    "TIER_3_SENTIMENT": 3,
    "TIER_0_MANUAL_CURATED": 0,
}


@dataclass
class CausalSourceResult:
    source_id: str
    name: str
    category: str
    reliability_tier: str
    status: str
    direction: str = "NEUTRAL"
    confidence: str = "LOW"
    signal_score: float = 0.0
    event_risk: str = "LOW"
    summary: str = ""
    url: str = ""
    fields: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
    collected_utc: str = ""


@dataclass
class CausalContext:
    primary_cause: str
    cause_confidence: str
    catalyst_score: int
    event_risk: str
    technical_event_conflict: str
    causal_alignment: str
    causal_verdict: str
    source_count: int
    trusted_source_count: int
    manual_event_count: int
    auto_event_count: int = 0
    top_sources: List[str] = field(default_factory=list)
    internal_causes: List[Dict[str, Any]] = field(default_factory=list)
    external_sources: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class CausalReport:
    run_id: str
    generated_utc: str
    version: str
    status: str
    symbol: str
    timeframe: str
    collect_live: bool
    source_count: int
    successful_sources: int
    failed_sources: int
    trusted_successful_sources: int
    manual_events_loaded: int
    context: Dict[str, Any]
    auto_events_loaded: int = 0
    source_results: List[Dict[str, Any]] = field(default_factory=list)
    source_registry: List[Dict[str, Any]] = field(default_factory=list)
    source_health: List[Dict[str, Any]] = field(default_factory=list)
    latest_decision: Dict[str, Any] = field(default_factory=dict)
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


def _symbol_to_binance(symbol: str) -> str:
    return _upper(symbol).replace("/", "").replace("-", "") or "BTCUSDT"


def _iso_parse(value: Any) -> Optional[datetime]:
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
        dt = pd.to_datetime(text, utc=True, errors="coerce") if pd is not None else None
        if dt is not None and not pd.isna(dt):
            return dt.to_pydatetime().astimezone(timezone.utc)
    except Exception:
        return None
    return None


def _http_get_json(url: str, headers: Optional[Dict[str, str]] = None, timeout: float = SOURCE_TIMEOUT_SECONDS) -> Tuple[Optional[Any], str]:
    req_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        req_headers.update({k: v for k, v in headers.items() if v})
    try:
        req = urllib.request.Request(url, headers=req_headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec - public market data URLs only
            charset = resp.headers.get_content_charset() or "utf-8"
            text = resp.read().decode(charset, errors="replace")
        return json.loads(text), ""
    except Exception as error:
        return None, f"{type(error).__name__}: {error}"


def _source_result(source_id: str, name: str, category: str, reliability_tier: str, status: str, **kwargs) -> CausalSourceResult:
    return CausalSourceResult(
        source_id=source_id,
        name=name,
        category=category,
        reliability_tier=reliability_tier,
        status=status,
        collected_utc=utc_now_iso(),
        **kwargs,
    )


def build_source_registry() -> List[Dict[str, Any]]:
    """Human-readable source registry used by dashboards and runbooks.

    The engine is designed to prefer official or methodology-transparent sources.
    Some sources require optional API keys; missing keys do not fail the workflow.
    """
    registry = [
        {
            "source_id": "coingecko_global",
            "name": "CoinGecko Global Market Data",
            "category": "market_aggregate",
            "reliability_tier": "TIER_2_MARKET_AGGREGATOR",
            "requires_key": False,
            "env_key": "COINGECKO_API_KEY optional",
            "purpose": "Global crypto market cap, 24h volume, BTC/ETH dominance and 24h aggregate change.",
            "why_trusted": "Large independent crypto market data aggregator with documented REST endpoints.",
        },
        {
            "source_id": "defillama_tvl",
            "name": "DefiLlama Total TVL Chart",
            "category": "defi_liquidity",
            "reliability_tier": "TIER_1_PROTOCOL_AGGREGATOR",
            "requires_key": False,
            "env_key": "none",
            "purpose": "DeFi TVL trend as liquidity/risk-appetite context.",
            "why_trusted": "Open-source DeFi analytics API with transparent methodology notes.",
        },
        {
            "source_id": "defillama_stablecoins",
            "name": "DefiLlama Stablecoins",
            "category": "stablecoin_liquidity",
            "reliability_tier": "TIER_1_PROTOCOL_AGGREGATOR",
            "requires_key": False,
            "env_key": "none",
            "purpose": "Stablecoin supply and liquidity context.",
            "why_trusted": "Public stablecoin and DeFi analytics used as a neutral aggregator, not a trading venue.",
        },
        {
            "source_id": "binance_futures_open_interest",
            "name": "Binance USD-M Futures Open Interest",
            "category": "derivatives",
            "reliability_tier": "TIER_1_OFFICIAL_EXCHANGE",
            "requires_key": False,
            "env_key": "none",
            "purpose": "Present open interest for the mapped futures symbol.",
            "why_trusted": "Official Binance Futures market-data endpoint for Binance-listed contracts.",
        },
        {
            "source_id": "binance_futures_premium_funding",
            "name": "Binance USD-M Futures Premium/Funding",
            "category": "derivatives",
            "reliability_tier": "TIER_1_OFFICIAL_EXCHANGE",
            "requires_key": False,
            "env_key": "none",
            "purpose": "Funding-rate and mark/index price context for crowding risk.",
            "why_trusted": "Official Binance Futures premium index endpoint.",
        },
        {
            "source_id": "fred_macro",
            "name": "FRED Macro Snapshot",
            "category": "macro",
            "reliability_tier": "TIER_1_OFFICIAL_MACRO",
            "requires_key": True,
            "env_key": "FRED_API_KEY",
            "purpose": "US rates/dollar-liquidity macro context when API key is configured.",
            "why_trusted": "Federal Reserve Economic Data web service from the St. Louis Fed.",
        },
        {
            "source_id": "alternative_fng",
            "name": "Alternative.me Fear & Greed",
            "category": "sentiment",
            "reliability_tier": "TIER_3_SENTIMENT",
            "requires_key": False,
            "env_key": "none",
            "purpose": "Sentiment/crowding warning only; never used as a standalone bullish/bearish trigger.",
            "why_trusted": "Popular sentiment index but lower tier because methodology is not exchange/official data.",
        },
        {
            "source_id": "auto_event_collector",
            "name": "Automatic Official/Trusted Event Collector",
            "category": "news_event",
            "reliability_tier": "TIER_1_OFFICIAL_EVENT_PIPELINE",
            "requires_key": False,
            "env_key": "none",
            "purpose": "Reads data/auto_events.csv built from official RSS/API feeds such as SEC, Federal Reserve, Ethereum Foundation, Binance/Coinbase announcements, plus optional reputable media.",
            "why_trusted": "Collector prioritizes official feeds and stores source tier, source URL, timestamp, dedup id, direction, impact, and confidence for auditability.",
        },
        {
            "source_id": "manual_events",
            "name": "Curated Manual Event Ledger",
            "category": "news_event",
            "reliability_tier": "TIER_0_MANUAL_CURATED",
            "requires_key": False,
            "env_key": "none",
            "purpose": "High-trust manually entered events from sources such as Reuters, Fed, SEC, ETF issuers, project official posts.",
            "why_trusted": "Human-curated provenance lets you reject low-quality rumor sources.",
        },
    ]
    return registry


def _coin_gecko_headers() -> Dict[str, str]:
    key = os.getenv("COINGECKO_API_KEY", "").strip()
    if not key:
        return {}
    # Works for demo/pro depending on key type; public endpoint ignores if not needed.
    return {"x-cg-demo-api-key": key, "x-cg-pro-api-key": key}


def collect_coingecko_global() -> CausalSourceResult:
    url = "https://api.coingecko.com/api/v3/global"
    payload, error = _http_get_json(url, headers=_coin_gecko_headers())
    if error or not isinstance(payload, dict):
        return _source_result("coingecko_global", "CoinGecko Global Market Data", "market_aggregate", "TIER_2_MARKET_AGGREGATOR", "FAILED", url=url, error=error)
    data = payload.get("data", {}) or {}
    change = safe_float(data.get("market_cap_change_percentage_24h_usd"), 0.0) or 0.0
    btc_dom = safe_float((data.get("market_cap_percentage") or {}).get("btc"), 0.0) or 0.0
    eth_dom = safe_float((data.get("market_cap_percentage") or {}).get("eth"), 0.0) or 0.0
    total_cap = safe_float((data.get("total_market_cap") or {}).get("usd"), 0.0) or 0.0
    total_vol = safe_float((data.get("total_volume") or {}).get("usd"), 0.0) or 0.0
    direction = "NEUTRAL"
    if change >= 1.0:
        direction = "BULLISH"
    elif change <= -1.0:
        direction = "BEARISH"
    confidence = "MEDIUM" if abs(change) >= 1.0 else "LOW"
    summary = f"Global crypto cap 24h change={round(change, 3)}%, BTC dominance={round(btc_dom, 2)}%, volume=${round(total_vol/1e9, 2)}B."
    return _source_result(
        "coingecko_global", "CoinGecko Global Market Data", "market_aggregate", "TIER_2_MARKET_AGGREGATOR", "OK",
        url=url, direction=direction, confidence=confidence, signal_score=max(-18, min(18, change * 3)), summary=summary,
        fields={"market_cap_change_24h_pct": round(change, 4), "btc_dominance_pct": round(btc_dom, 4), "eth_dominance_pct": round(eth_dom, 4), "total_market_cap_usd": total_cap, "total_volume_usd": total_vol},
    )


def collect_defillama_tvl() -> CausalSourceResult:
    url = "https://api.llama.fi/charts"
    payload, error = _http_get_json(url)
    if error or not isinstance(payload, list) or len(payload) < 2:
        return _source_result("defillama_tvl", "DefiLlama Total TVL Chart", "defi_liquidity", "TIER_1_PROTOCOL_AGGREGATOR", "FAILED", url=url, error=error or "unexpected_payload")
    try:
        # API returns historical rows with totalLiquidityUSD. Use last vs approximately 7d ago.
        latest = payload[-1]
        prev = payload[-8] if len(payload) >= 8 else payload[0]
        latest_tvl = safe_float(latest.get("totalLiquidityUSD"), 0.0) or 0.0
        prev_tvl = safe_float(prev.get("totalLiquidityUSD"), 0.0) or 0.0
        change = ((latest_tvl - prev_tvl) / prev_tvl * 100.0) if prev_tvl else 0.0
        direction = "BULLISH" if change >= 1.5 else "BEARISH" if change <= -1.5 else "NEUTRAL"
        summary = f"DeFi TVL approx 7d change={round(change, 3)}%, latest=${round(latest_tvl/1e9, 2)}B."
        return _source_result(
            "defillama_tvl", "DefiLlama Total TVL Chart", "defi_liquidity", "TIER_1_PROTOCOL_AGGREGATOR", "OK",
            url=url, direction=direction, confidence="MEDIUM" if abs(change) >= 1.5 else "LOW", signal_score=max(-14, min(14, change * 2)), summary=summary,
            fields={"latest_tvl_usd": latest_tvl, "approx_7d_change_pct": round(change, 4)},
        )
    except Exception as error:
        return _source_result("defillama_tvl", "DefiLlama Total TVL Chart", "defi_liquidity", "TIER_1_PROTOCOL_AGGREGATOR", "FAILED", url=url, error=f"{type(error).__name__}: {error}")


def collect_defillama_stablecoins() -> CausalSourceResult:
    url = "https://stablecoins.llama.fi/stablecoins?includePrices=true"
    payload, error = _http_get_json(url)
    if error or not isinstance(payload, dict):
        return _source_result("defillama_stablecoins", "DefiLlama Stablecoins", "stablecoin_liquidity", "TIER_1_PROTOCOL_AGGREGATOR", "FAILED", url=url, error=error)
    try:
        pegged = payload.get("peggedAssets", []) or []
        total = 0.0
        for item in pegged:
            circ = item.get("circulating") or {}
            pegged_usd = circ.get("peggedUSD") if isinstance(circ, dict) else None
            total += safe_float(pegged_usd, 0.0) or 0.0
        summary = f"Stablecoin listed circulating supply snapshot=${round(total/1e9, 2)}B across {len(pegged)} assets."
        return _source_result(
            "defillama_stablecoins", "DefiLlama Stablecoins", "stablecoin_liquidity", "TIER_1_PROTOCOL_AGGREGATOR", "OK",
            url=url, direction="NEUTRAL", confidence="LOW", signal_score=0, summary=summary,
            fields={"stablecoin_assets": len(pegged), "listed_circulating_usd": total},
        )
    except Exception as error:
        return _source_result("defillama_stablecoins", "DefiLlama Stablecoins", "stablecoin_liquidity", "TIER_1_PROTOCOL_AGGREGATOR", "FAILED", url=url, error=f"{type(error).__name__}: {error}")


def collect_binance_open_interest(symbol: str) -> CausalSourceResult:
    b_symbol = _symbol_to_binance(symbol)
    url = "https://fapi.binance.com/fapi/v1/openInterest?" + urllib.parse.urlencode({"symbol": b_symbol})
    payload, error = _http_get_json(url)
    if error or not isinstance(payload, dict):
        return _source_result("binance_futures_open_interest", "Binance USD-M Futures Open Interest", "derivatives", "TIER_1_OFFICIAL_EXCHANGE", "FAILED", url=url, error=error)
    oi = safe_float(payload.get("openInterest"), 0.0) or 0.0
    summary = f"{b_symbol} open interest snapshot={round(oi, 4)} contracts/units on Binance USD-M Futures."
    return _source_result(
        "binance_futures_open_interest", "Binance USD-M Futures Open Interest", "derivatives", "TIER_1_OFFICIAL_EXCHANGE", "OK",
        url=url, direction="NEUTRAL", confidence="LOW", signal_score=0, summary=summary,
        fields={"binance_symbol": b_symbol, "open_interest": oi, "time": payload.get("time")},
    )


def collect_binance_premium_funding(symbol: str) -> CausalSourceResult:
    b_symbol = _symbol_to_binance(symbol)
    url = "https://fapi.binance.com/fapi/v1/premiumIndex?" + urllib.parse.urlencode({"symbol": b_symbol})
    payload, error = _http_get_json(url)
    if error or not isinstance(payload, dict):
        return _source_result("binance_futures_premium_funding", "Binance USD-M Futures Premium/Funding", "derivatives", "TIER_1_OFFICIAL_EXCHANGE", "FAILED", url=url, error=error)
    funding = safe_float(payload.get("lastFundingRate"), 0.0) or 0.0
    premium = safe_float(payload.get("estimatedSettlePrice"), 0.0)
    mark = safe_float(payload.get("markPrice"), 0.0) or 0.0
    index = safe_float(payload.get("indexPrice"), 0.0) or 0.0
    premium_pct = ((mark - index) / index * 100.0) if index else 0.0
    event_risk = "LOW"
    direction = "NEUTRAL"
    if funding >= 0.0005:
        event_risk = "MEDIUM"
        direction = "CROWDED_LONG_RISK"
    elif funding <= -0.0005:
        event_risk = "MEDIUM"
        direction = "CROWDED_SHORT_RISK"
    summary = f"{b_symbol} funding={round(funding*100, 4)}%, mark-index premium={round(premium_pct, 4)}%."
    return _source_result(
        "binance_futures_premium_funding", "Binance USD-M Futures Premium/Funding", "derivatives", "TIER_1_OFFICIAL_EXCHANGE", "OK",
        url=url, direction=direction, confidence="MEDIUM" if event_risk != "LOW" else "LOW", signal_score=0, event_risk=event_risk, summary=summary,
        fields={"binance_symbol": b_symbol, "funding_rate": funding, "funding_pct": round(funding*100, 6), "mark_price": mark, "index_price": index, "premium_pct": round(premium_pct, 6), "estimated_settle_price": premium},
    )


def _fred_latest(api_key: str, series_id: str) -> Tuple[Optional[float], str]:
    url = "https://api.stlouisfed.org/fred/series/observations?" + urllib.parse.urlencode({
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1,
    })
    payload, error = _http_get_json(url)
    if error or not isinstance(payload, dict):
        return None, error or "unexpected_payload"
    obs = payload.get("observations", []) or []
    if not obs:
        return None, "no_observation"
    val = safe_float(obs[0].get("value"), None)
    return val, ""


def collect_fred_macro() -> CausalSourceResult:
    api_key = os.getenv("FRED_API_KEY", "").strip()
    if not api_key:
        return _source_result(
            "fred_macro", "FRED Macro Snapshot", "macro", "TIER_1_OFFICIAL_MACRO", "SKIPPED_NO_KEY",
            url="https://fred.stlouisfed.org/docs/api/fred/", summary="FRED_API_KEY is not configured; macro official-source collection skipped.",
        )
    fields = {}
    errors = []
    for sid in ["DGS10", "DFF", "DTWEXBGS"]:
        val, err = _fred_latest(api_key, sid)
        if err:
            errors.append(f"{sid}: {err}")
        fields[sid] = val
    if errors and all(v is None for v in fields.values()):
        return _source_result("fred_macro", "FRED Macro Snapshot", "macro", "TIER_1_OFFICIAL_MACRO", "FAILED", error="; ".join(errors), url="https://fred.stlouisfed.org/docs/api/fred/")
    dgs10 = safe_float(fields.get("DGS10"), 0.0) or 0.0
    dff = safe_float(fields.get("DFF"), 0.0) or 0.0
    dollar = safe_float(fields.get("DTWEXBGS"), 0.0) or 0.0
    risk = "MEDIUM" if dgs10 >= 4.5 or dff >= 5.0 else "LOW"
    summary = f"FRED macro snapshot: 10Y={dgs10}, Fed Funds={dff}, Broad Dollar={dollar}."
    return _source_result(
        "fred_macro", "FRED Macro Snapshot", "macro", "TIER_1_OFFICIAL_MACRO", "OK",
        direction="RISK_OFF_HEADWIND" if risk == "MEDIUM" else "NEUTRAL", confidence="LOW", event_risk=risk, signal_score=-5 if risk == "MEDIUM" else 0, summary=summary, fields=fields,
        url="https://fred.stlouisfed.org/docs/api/fred/",
    )


def collect_alternative_fng() -> CausalSourceResult:
    url = "https://api.alternative.me/fng/?limit=1&format=json"
    payload, error = _http_get_json(url)
    if error or not isinstance(payload, dict):
        return _source_result("alternative_fng", "Alternative.me Fear & Greed", "sentiment", "TIER_3_SENTIMENT", "FAILED", url=url, error=error)
    try:
        row = (payload.get("data") or [{}])[0]
        value = safe_float(row.get("value"), 50.0) or 50.0
        classification = _norm(row.get("value_classification"), "Neutral")
        risk = "MEDIUM" if value >= 75 or value <= 25 else "LOW"
        direction = "SENTIMENT_GREED_RISK" if value >= 75 else "SENTIMENT_FEAR_RISK" if value <= 25 else "NEUTRAL"
        summary = f"Fear & Greed={value} ({classification}); used only as sentiment/crowding context."
        return _source_result(
            "alternative_fng", "Alternative.me Fear & Greed", "sentiment", "TIER_3_SENTIMENT", "OK",
            url=url, direction=direction, confidence="LOW", signal_score=0, event_risk=risk, summary=summary,
            fields={"value": value, "classification": classification, "timestamp": row.get("timestamp")},
        )
    except Exception as error:
        return _source_result("alternative_fng", "Alternative.me Fear & Greed", "sentiment", "TIER_3_SENTIMENT", "FAILED", url=url, error=f"{type(error).__name__}: {error}")


def _ensure_manual_events_example() -> None:
    CAUSAL_EVENTS_EXAMPLE.parent.mkdir(parents=True, exist_ok=True)
    if not CAUSAL_EVENTS_EXAMPLE.exists():
        CAUSAL_EVENTS_EXAMPLE.write_text(
            "timestamp_utc,symbol,event_type,source_name,source_url,impact,direction,confidence,description\n"
            "2026-07-09T12:00:00+00:00,BTC/USDT,macro,Reuters,,high,bullish,medium,Example: dovish macro interpretation supporting risk assets\n"
            "2026-07-09T15:00:00+00:00,ALL,regulatory,SEC,,high,bearish,medium,Example: enforcement headline increasing crypto regulatory risk\n",
            encoding="utf-8",
        )


def load_manual_events(symbol: str, window_hours: int = 72) -> List[CausalSourceResult]:
    _ensure_manual_events_example()
    # The example file is documentation only. Do not treat example rows as real
    # market events, otherwise dashboards would report fake catalysts.
    if not CAUSAL_EVENTS_FILE.exists():
        return []
    path = CAUSAL_EVENTS_FILE
    results: List[CausalSourceResult] = []
    now = datetime.now(timezone.utc)
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row:
                    continue
                ts = _iso_parse(row.get("timestamp_utc") or row.get("timestamp") or row.get("time"))
                if ts and abs((now - ts).total_seconds()) > window_hours * 3600:
                    continue
                event_symbol = _upper(row.get("symbol"), "ALL")
                target = _upper(symbol)
                if event_symbol not in {"ALL", "GLOBAL", target, target.replace("/", "")}:
                    continue
                impact = _upper(row.get("impact"), "LOW")
                direction_raw = _upper(row.get("direction"), "NEUTRAL")
                direction = "BULLISH" if "BULL" in direction_raw or direction_raw in {"UP", "POSITIVE"} else "BEARISH" if "BEAR" in direction_raw or direction_raw in {"DOWN", "NEGATIVE"} else "NEUTRAL"
                score = 0
                if direction == "BULLISH":
                    score = 12 if impact == "HIGH" else 7 if impact == "MEDIUM" else 3
                elif direction == "BEARISH":
                    score = -12 if impact == "HIGH" else -7 if impact == "MEDIUM" else -3
                source_name = _norm(row.get("source_name"), "manual")
                desc = _norm(row.get("description"), "manual event")
                results.append(_source_result(
                    "manual_events", "Curated Manual Event Ledger", "news_event", "TIER_0_MANUAL_CURATED", "OK",
                    direction=direction, confidence=_upper(row.get("confidence"), "MEDIUM"), signal_score=score,
                    event_risk="HIGH" if impact == "HIGH" else "MEDIUM" if impact == "MEDIUM" else "LOW",
                    summary=f"{source_name}: {desc}", url=_norm(row.get("source_url")),
                    fields={"event_type": row.get("event_type", ""), "impact": impact, "event_timestamp_utc": ts.isoformat() if ts else "", "event_symbol": event_symbol},
                ))
    except Exception as error:
        results.append(_source_result("manual_events", "Curated Manual Event Ledger", "news_event", "TIER_0_MANUAL_CURATED", "FAILED", error=f"{type(error).__name__}: {error}"))
    return results


def load_auto_events(symbol: str, window_hours: int = 168) -> List[CausalSourceResult]:
    """Load automatically collected official/trusted events from data/auto_events.csv.

    The collector writes the same core columns as manual_events plus source_tier,
    event_id and auto_score. Rows are still filtered by symbol and recency.
    """
    if not CAUSAL_AUTO_EVENTS_FILE.exists():
        return []
    results: List[CausalSourceResult] = []
    now = datetime.now(timezone.utc)
    try:
        with CAUSAL_AUTO_EVENTS_FILE.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row:
                    continue
                ts = _iso_parse(row.get("timestamp_utc") or row.get("timestamp") or row.get("time"))
                if ts and abs((now - ts).total_seconds()) > window_hours * 3600:
                    continue
                event_symbol = _upper(row.get("symbol"), "ALL")
                target = _upper(symbol)
                if event_symbol not in {"ALL", "GLOBAL", target, target.replace("/", "")}:
                    continue
                impact = _upper(row.get("impact"), "LOW")
                direction = _upper(row.get("direction"), "NEUTRAL")
                if direction not in {"BULLISH", "BEARISH", "NEUTRAL"}:
                    direction = "NEUTRAL"
                score = safe_float(row.get("auto_score"), None)
                if score is None:
                    score = 0
                    if direction == "BULLISH":
                        score = 12 if impact == "HIGH" else 7 if impact == "MEDIUM" else 2
                    elif direction == "BEARISH":
                        score = -12 if impact == "HIGH" else -7 if impact == "MEDIUM" else -2
                source_name = _norm(row.get("source_name") or row.get("source_id"), "auto_event")
                desc = _norm(row.get("description") or row.get("title"), "auto-collected event")
                tier = _norm(row.get("source_tier"), "TIER_2_REPUTABLE_MEDIA")
                results.append(_source_result(
                    "auto_events", "Automatic Official/Trusted Event Ledger", "news_event", tier, "OK",
                    direction=direction,
                    confidence=_upper(row.get("confidence"), "MEDIUM"),
                    signal_score=score,
                    event_risk=_upper(row.get("event_risk"), "HIGH" if impact == "HIGH" else "MEDIUM" if impact == "MEDIUM" else "LOW"),
                    summary=f"{source_name}: {desc}",
                    url=_norm(row.get("source_url")),
                    fields={
                        "event_id": row.get("event_id", ""),
                        "source_id": row.get("source_id", ""),
                        "event_type": row.get("event_type", ""),
                        "impact": impact,
                        "event_timestamp_utc": ts.isoformat() if ts else "",
                        "event_symbol": event_symbol,
                        "tags": row.get("tags", ""),
                        "matched_keywords": row.get("matched_keywords", ""),
                    },
                ))
    except Exception as error:
        results.append(_source_result("auto_events", "Automatic Official/Trusted Event Ledger", "news_event", "TIER_2_REPUTABLE_MEDIA", "FAILED", error=f"{type(error).__name__}: {error}"))
    return results


def collect_external_sources(symbol: str = "BTC/USDT", *, collect_live: bool = True, include_sentiment: bool = True) -> List[CausalSourceResult]:
    results: List[CausalSourceResult] = []
    results.extend(load_manual_events(symbol))
    results.extend(load_auto_events(symbol))
    if not collect_live:
        return results
    collectors = [
        collect_coingecko_global,
        collect_defillama_tvl,
        collect_defillama_stablecoins,
        lambda: collect_binance_open_interest(symbol),
        lambda: collect_binance_premium_funding(symbol),
        collect_fred_macro,
    ]
    if include_sentiment:
        collectors.append(collect_alternative_fng)
    for fn in collectors:
        try:
            results.append(fn())
            # Be gentle with public endpoints.
            time.sleep(float(os.getenv("FREAKTO_CAUSAL_SLEEP", "0.15")))
        except Exception as error:
            results.append(_source_result("unknown", getattr(fn, "__name__", "collector"), "unknown", "TIER_3_SENTIMENT", "FAILED", error=f"{type(error).__name__}: {error}"))
    return results


def _opportunity_component(opportunity: Any, name: str) -> float:
    for component in getattr(opportunity, "components", []) or []:
        if getattr(component, "name", "") == name:
            return safe_float(getattr(component, "points", 0), 0.0) or 0.0
    raw = getattr(opportunity, "raw", {}) or {}
    return safe_float(raw.get(name.lower().replace(" ", "_")), 0.0) or 0.0


def detect_internal_causes(market_df: Any = None, opportunity: Any = None, latest_decision: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    causes: List[Dict[str, Any]] = []
    latest_decision = latest_decision or {}
    side = _upper(getattr(opportunity, "side", latest_decision.get("side", "NEUTRAL")), "NEUTRAL")
    score = safe_float(getattr(opportunity, "score", latest_decision.get("score", 0)), 0.0) or 0.0
    volume_score = _opportunity_component(opportunity, "Volume") if opportunity is not None else safe_float(latest_decision.get("volume_score"), 0.0) or 0.0
    structure_score = _opportunity_component(opportunity, "Structure") if opportunity is not None else safe_float(latest_decision.get("structure_score"), 0.0) or 0.0
    trend_score = _opportunity_component(opportunity, "Trend") if opportunity is not None else safe_float(latest_decision.get("trend_score"), 0.0) or 0.0
    momentum_score = _opportunity_component(opportunity, "Momentum") if opportunity is not None else safe_float(latest_decision.get("momentum_score"), 0.0) or 0.0
    regime = _upper((getattr(opportunity, "raw", {}) or {}).get("regime_label") if opportunity is not None else latest_decision.get("regime_label"), "UNKNOWN")
    mtf_direction = _upper((getattr(opportunity, "raw", {}) or {}).get("mtf_direction") if opportunity is not None else latest_decision.get("mtf_direction"), "")
    mtf_consensus = safe_float((getattr(opportunity, "raw", {}) or {}).get("mtf_consensus") if opportunity is not None else latest_decision.get("mtf_consensus"), 0.0) or 0.0

    if structure_score >= 10 and volume_score >= 7:
        causes.append({"cause": "STRUCTURE_BREAKOUT_WITH_VOLUME", "direction": side, "confidence": "MEDIUM", "score": 22, "detail": "structure_score>=10 and volume support is present"})
    elif structure_score >= 10:
        causes.append({"cause": "STRUCTURE_BREAKOUT_WEAK_VOLUME_CONFIRMATION", "direction": side, "confidence": "LOW", "score": 12, "detail": "structure_score>=10 but volume support is weak/missing"})
    if volume_score >= 10 and structure_score < 10:
        causes.append({"cause": "VOLUME_EXPANSION_WITHOUT_STRUCTURE", "direction": side, "confidence": "LOW", "score": 7, "detail": "volume spike exists but structure did not confirm"})
    if trend_score >= 20 and momentum_score >= 20:
        causes.append({"cause": "TREND_MOMENTUM_ALIGNMENT", "direction": side, "confidence": "MEDIUM", "score": 18, "detail": "trend and momentum components are aligned"})
    if regime == "TRENDING_BULL" and side == "LONG":
        causes.append({"cause": "REGIME_ALIGNED_BULL_LONG", "direction": "BULLISH", "confidence": "MEDIUM", "score": 12, "detail": "TRENDING_BULL regime supports LONG bias"})
    elif regime == "TRENDING_BEAR" and side == "SHORT":
        causes.append({"cause": "REGIME_ALIGNED_BEAR_SHORT", "direction": "BEARISH", "confidence": "MEDIUM", "score": 12, "detail": "TRENDING_BEAR regime supports SHORT bias"})
    elif regime in {"TRENDING_BULL", "TRENDING_BEAR"} and side in {"LONG", "SHORT"}:
        causes.append({"cause": "REGIME_DIRECTION_CONFLICT", "direction": "RISK", "confidence": "MEDIUM", "score": -16, "detail": f"{regime} conflicts with {side}"})
    if mtf_direction and mtf_direction == side and mtf_consensus >= 60:
        causes.append({"cause": "MULTI_TIMEFRAME_ALIGNMENT", "direction": side, "confidence": "MEDIUM", "score": 10, "detail": f"MTF direction={mtf_direction}, consensus={mtf_consensus}%"})
    elif mtf_direction and side in {"LONG", "SHORT"} and mtf_direction not in {side, "NEUTRAL"}:
        causes.append({"cause": "MULTI_TIMEFRAME_CONFLICT", "direction": "RISK", "confidence": "MEDIUM", "score": -14, "detail": f"MTF direction={mtf_direction} conflicts with {side}"})

    if pd is not None and market_df is not None and not getattr(market_df, "empty", True):
        try:
            w = market_df.copy().tail(80)
            row = w.iloc[-1]
            prev = w.iloc[-2]
            close = safe_float(row.get("close"), 0.0) or 0.0
            prev_close = safe_float(prev.get("close"), 0.0) or 0.0
            change = ((close - prev_close) / prev_close * 100.0) if prev_close else 0.0
            atr = safe_float(row.get("atr_pct"), 0.0) or 0.0
            atr_med = safe_float(w.get("atr_pct").tail(30).median() if "atr_pct" in w.columns else 0.0, 0.0) or 0.0
            if atr_med and atr > atr_med * 1.35:
                causes.append({"cause": "VOLATILITY_EXPANSION", "direction": "RISK", "confidence": "MEDIUM", "score": -8, "detail": f"ATR%={round(atr, 3)} vs median={round(atr_med, 3)}"})
            if abs(change) >= 1.2 and volume_score < 5:
                causes.append({"cause": "PRICE_MOVE_WITH_WEAK_VOLUME", "direction": "RISK", "confidence": "LOW", "score": -8, "detail": f"last candle move={round(change, 3)}% with weak volume_score"})
        except Exception:
            pass

    if not causes:
        causes.append({"cause": "NO_CLEAR_INTERNAL_CAUSE", "direction": "NEUTRAL", "confidence": "LOW", "score": 0, "detail": "No strong causal pattern detected from current internal features"})
    return causes


def _direction_sign(direction: str) -> int:
    d = _upper(direction)
    if d in {"BULLISH", "LONG", "UP", "POSITIVE", "TRENDING_BULL"}:
        return 1
    if d in {"BEARISH", "SHORT", "DOWN", "NEGATIVE", "TRENDING_BEAR"}:
        return -1
    if "LONG_RISK" in d:
        return -1
    if "SHORT_RISK" in d:
        return 1
    return 0


def _side_sign(side: str) -> int:
    s = _upper(side)
    if s == "LONG":
        return 1
    if s == "SHORT":
        return -1
    return 0


def _confidence_value(value: str) -> int:
    return {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(_upper(value), 1)


def build_causal_context(
    *,
    symbol: str = "BTC/USDT",
    timeframe: str = "4h",
    market_df: Any = None,
    opportunity: Any = None,
    latest_decision: Optional[Dict[str, Any]] = None,
    collect_live: bool = False,
    external_results: Optional[List[CausalSourceResult]] = None,
) -> CausalContext:
    latest_decision = latest_decision or {}
    side = _upper(getattr(opportunity, "side", latest_decision.get("side", "NEUTRAL")), "NEUTRAL")
    side_s = _side_sign(side)
    internal = detect_internal_causes(market_df=market_df, opportunity=opportunity, latest_decision=latest_decision)
    external = external_results if external_results is not None else collect_external_sources(symbol=symbol, collect_live=collect_live)

    successful = [r for r in external if r.status == "OK"]
    trusted_success = [r for r in successful if TRUST_ORDER.get(r.reliability_tier, 9) <= 2]
    manual_events = [r for r in successful if r.source_id == "manual_events"]
    auto_events = [r for r in successful if r.source_id == "auto_events"]

    auto_event_score = sum(safe_float(r.signal_score, 0.0) or 0.0 for r in auto_events)
    manual_event_score = sum(safe_float(r.signal_score, 0.0) or 0.0 for r in manual_events)
    auto_directional_events = [r for r in auto_events if _direction_sign(r.direction) != 0]
    auto_high_risk_events = [r for r in auto_events if _upper(r.event_risk) == "HIGH"]

    internal_score = sum(safe_float(c.get("score"), 0.0) or 0.0 for c in internal)
    external_score = sum(safe_float(r.signal_score, 0.0) or 0.0 for r in successful)
    raw_catalyst = internal_score + external_score
    catalyst_score = int(max(0, min(100, 50 + raw_catalyst)))

    top_internal = sorted(internal, key=lambda c: abs(safe_float(c.get("score"), 0.0) or 0.0), reverse=True)[0]
    primary_cause = top_internal.get("cause", "UNKNOWN")
    cause_confidence = top_internal.get("confidence", "LOW")
    if trusted_success and abs(external_score) >= 10:
        best_ext = sorted(trusted_success, key=lambda r: abs(safe_float(r.signal_score, 0.0) or 0.0), reverse=True)[0]
        if abs(best_ext.signal_score) > abs(safe_float(top_internal.get("score"), 0.0) or 0.0):
            primary_cause = f"EXTERNAL_{best_ext.source_id.upper()}"
            cause_confidence = best_ext.confidence

    # v7: prefer cleaned automatic multi-source context over a single manual row
    # when the auto ledger has enough directional/high-risk evidence. Manual rows
    # remain important overrides, but they should not permanently dominate the
    # primary cause after the event collector is working.
    if auto_events and (len(auto_directional_events) >= 3 or len(auto_high_risk_events) >= 3):
        if abs(auto_event_score) >= max(8.0, abs(manual_event_score) * 0.60):
            primary_cause = "MULTI_SOURCE_EVENT_CONSENSUS" if len(auto_events) >= 5 else "AUTO_EVENTS_CONTEXT"
            cause_confidence = "HIGH" if len(auto_directional_events) >= 6 or len(auto_high_risk_events) >= 6 else "MEDIUM"

    # Conflict/alignment: compare technical side with external/manual signals.
    external_direction_sum = sum(_direction_sign(r.direction) * _confidence_value(r.confidence) for r in successful)
    internal_direction_sum = sum(_direction_sign(c.get("direction")) * _confidence_value(c.get("confidence", "LOW")) for c in internal)
    conflict = "LOW"
    alignment = "NEUTRAL"
    if side_s != 0:
        if external_direction_sum and (external_direction_sum * side_s) < 0:
            conflict = "HIGH" if abs(external_direction_sum) >= 4 else "MEDIUM"
            alignment = "CONFLICT_WITH_EXTERNAL_CONTEXT"
        elif internal_direction_sum and (internal_direction_sum * side_s) < 0:
            conflict = "MEDIUM"
            alignment = "INTERNAL_CAUSE_CONFLICT"
        elif (external_direction_sum * side_s) > 0 or (internal_direction_sum * side_s) > 0:
            alignment = "ALIGNED_WITH_CAUSAL_CONTEXT"
        else:
            alignment = "NO_STRONG_CAUSAL_ALIGNMENT"
    else:
        alignment = "NEUTRAL_DECISION_CONTEXT_ONLY"

    event_risk = "LOW"
    risk_rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
    for r in successful:
        if risk_rank.get(_upper(r.event_risk), 1) > risk_rank.get(event_risk, 1):
            event_risk = _upper(r.event_risk)
    for c in internal:
        if _upper(c.get("direction")) == "RISK" and abs(safe_float(c.get("score"), 0.0) or 0.0) >= 12:
            event_risk = "MEDIUM" if event_risk == "LOW" else event_risk

    if conflict == "HIGH":
        verdict = "CAUSAL_CONFLICT_RESEARCH_ONLY"
    elif catalyst_score >= 70 and alignment == "ALIGNED_WITH_CAUSAL_CONTEXT" and len(trusted_success) >= 1:
        verdict = "CAUSAL_SUPPORTS_DECISION_RESEARCH_ONLY"
    elif catalyst_score >= 60:
        verdict = "CAUSAL_CONTEXT_PROMISING_BUT_INCOMPLETE"
    elif catalyst_score <= 35:
        verdict = "CAUSAL_CONTEXT_WEAK_OR_RISKY"
    else:
        verdict = "CAUSAL_CONTEXT_NEUTRAL"

    warnings = [
        "Causal Intelligence یک لایه پژوهشی است و به‌تنهایی سیگنال خرید/فروش نمی‌سازد.",
        "جمع‌آوری APIهای عمومی ممکن است با rate limit یا محدودیت منطقه‌ای روبه‌رو شود؛ شکست source نباید چرخه Forward را fail کند.",
    ]
    if conflict in {"HIGH", "MEDIUM"}:
        warnings.append("بین جهت تکنیکال و context بیرونی/علتی تضاد دیده شده؛ confidence تصمیم باید پایین‌تر در نظر گرفته شود.")
    if not trusted_success and collect_live:
        warnings.append("هیچ source قابل‌اعتماد live با موفقیت جمع‌آوری نشد؛ manual_events و داده داخلی اهمیت بیشتری دارند.")

    recommendations = []
    if CAUSAL_EVENTS_FILE.exists():
        recommendations.append("manual_events.csv فعال است؛ رویدادهای high-impact را با source_url معتبر ادامه بده.")
    else:
        recommendations.append("برای خبر/رویدادهای خیلی مهم، data/manual_events.csv را از example بساز و فقط منابع معتبر مثل Fed/SEC/Reuters/official project را وارد کن.")
    if CAUSAL_AUTO_EVENTS_FILE.exists():
        recommendations.append("auto_events.csv فعال است؛ Automatic Event Collector قبل از Causal Intelligence باید اجرا شود.")
    else:
        recommendations.append("برای جمع‌آوری خودکار رویدادها، automatic_event_collector_dashboard.py --compact را اجرا کن.")
    recommendations.append("در v7 نتایج causal/narrative فقط به decision log و research reports اضافه می‌شود؛ هیچ Paper/Live فعال نمی‌شود.")

    top_sources = []
    for r in sorted(successful, key=lambda x: (TRUST_ORDER.get(x.reliability_tier, 9), abs(safe_float(x.signal_score, 0.0) or 0.0)), reverse=False)[:6]:
        top_sources.append(f"{r.source_id}:{r.status}:{r.direction}:{r.confidence}")

    return CausalContext(
        primary_cause=primary_cause,
        cause_confidence=cause_confidence,
        catalyst_score=catalyst_score,
        event_risk=event_risk,
        technical_event_conflict=conflict,
        causal_alignment=alignment,
        causal_verdict=verdict,
        source_count=len(external),
        trusted_source_count=len(trusted_success),
        manual_event_count=len(manual_events),
        auto_event_count=len(auto_events),
        top_sources=top_sources,
        internal_causes=internal,
        external_sources=[asdict(r) for r in external],
        warnings=warnings,
        recommendations=recommendations,
    )


def attach_causal_context(
    opportunity: Any,
    market_df: Any,
    *,
    symbol: str = "BTC/USDT",
    timeframe: str = "4h",
    collect_live: bool = False,
) -> CausalContext:
    """Attach compact causal fields to opportunity.raw for decision_logger."""
    context = build_causal_context(symbol=symbol, timeframe=timeframe, market_df=market_df, opportunity=opportunity, collect_live=collect_live)
    raw = getattr(opportunity, "raw", None)
    if raw is None:
        raw = {}
        setattr(opportunity, "raw", raw)
    raw.update({
        "primary_cause": context.primary_cause,
        "cause_confidence": context.cause_confidence,
        "catalyst_score": context.catalyst_score,
        "event_risk": context.event_risk,
        "technical_event_conflict": context.technical_event_conflict,
        "causal_alignment": context.causal_alignment,
        "causal_verdict": context.causal_verdict,
        "causal_source_count": context.source_count,
        "causal_trusted_source_count": context.trusted_source_count,
        "causal_manual_event_count": context.manual_event_count,
        "causal_auto_event_count": context.auto_event_count,
        "causal_top_sources": " | ".join(context.top_sources[:6]),
        "causal_notes": " | ".join([c.get("cause", "") for c in context.internal_causes[:4]]),
    })
    return context


def _latest_decision_dict() -> Dict[str, Any]:
    df = load_decisions_df()
    if df is None or df.empty:
        return {}
    try:
        return df.tail(1).to_dict(orient="records")[0]
    except Exception:
        return {}


def run_causal_intelligence(
    *,
    symbol: str = "BTC/USDT",
    timeframe: str = "4h",
    market_df: Any = None,
    opportunity: Any = None,
    collect_live: bool = True,
    include_sentiment: bool = True,
) -> CausalReport:
    rid = run_id("causal_intel")
    latest_decision = _latest_decision_dict() if opportunity is None else {}
    external = collect_external_sources(symbol=symbol, collect_live=collect_live, include_sentiment=include_sentiment)
    context = build_causal_context(
        symbol=symbol,
        timeframe=timeframe,
        market_df=market_df,
        opportunity=opportunity,
        latest_decision=latest_decision,
        collect_live=False,
        external_results=external,
    )
    successful = [r for r in external if r.status == "OK"]
    failed = [r for r in external if r.status.startswith("FAILED")]
    trusted_successful = [r for r in successful if TRUST_ORDER.get(r.reliability_tier, 9) <= 2]
    manual_count = sum(1 for r in successful if r.source_id == "manual_events")
    auto_count = sum(1 for r in successful if r.source_id == "auto_events")

    blockers = []
    if collect_live and not trusted_successful:
        blockers.append("هیچ source live قابل‌اعتماد با موفقیت جمع‌آوری نشد؛ network/API key/rate limit را بررسی کن.")
    if context.causal_verdict == "CAUSAL_CONFLICT_RESEARCH_ONLY":
        blockers.append("Causal conflict بالا است؛ هر استفاده عملی باید downgrade شود و فقط Research بماند.")

    status = "CAUSAL_CONTEXT_READY"
    if blockers:
        status = "CAUSAL_CONTEXT_WITH_BLOCKERS"
    elif not collect_live:
        status = "CAUSAL_CONTEXT_INTERNAL_ONLY"
    elif failed and successful:
        status = "CAUSAL_CONTEXT_PARTIAL_SOURCES"

    source_health = [{
        "source_id": r.source_id,
        "status": r.status,
        "tier": r.reliability_tier,
        "category": r.category,
        "direction": r.direction,
        "event_risk": r.event_risk,
        "error": r.error,
    } for r in external]

    report = CausalReport(
        run_id=rid,
        generated_utc=utc_now_iso(),
        version=VERSION,
        status=status,
        symbol=symbol,
        timeframe=timeframe,
        collect_live=collect_live,
        source_count=len(external),
        successful_sources=len(successful),
        failed_sources=len(failed),
        trusted_successful_sources=len(trusted_successful),
        manual_events_loaded=manual_count,
        auto_events_loaded=auto_count,
        context=asdict(context),
        source_results=[asdict(r) for r in external],
        source_registry=build_source_registry(),
        source_health=source_health,
        latest_decision=latest_decision,
        blockers=blockers,
        warnings=context.warnings,
        recommendations=context.recommendations,
    )
    return report


def format_causal_console(report: CausalReport, compact: bool = True) -> str:
    data = asdict(report)
    ctx = data.get("context", {})
    sep = "=" * 110
    lines = [sep, f"🧠 Freakto Causal/Event Intelligence Core {VERSION}", sep]
    lines.append(f"Status                 : {data.get('status')}")
    lines.append(f"Run ID                 : {data.get('run_id')}")
    lines.append(f"Symbol / TF            : {data.get('symbol')} | {data.get('timeframe')}")
    lines.append(f"Collect Live Sources   : {data.get('collect_live')}")
    lines.append(f"Sources OK/Failed      : {data.get('successful_sources')} / {data.get('failed_sources')}")
    lines.append(f"Trusted Sources OK     : {data.get('trusted_successful_sources')}")
    lines.append(f"Manual Events Loaded   : {data.get('manual_events_loaded')}")
    lines.append(f"Auto Events Loaded     : {data.get('auto_events_loaded')}")
    lines.append("")
    lines.append("Causal Context:")
    lines.append(f"- Primary Cause        : {ctx.get('primary_cause')}")
    lines.append(f"- Cause Confidence     : {ctx.get('cause_confidence')}")
    lines.append(f"- Catalyst Score       : {ctx.get('catalyst_score')}/100")
    lines.append(f"- Event Risk           : {ctx.get('event_risk')}")
    lines.append(f"- Technical Conflict   : {ctx.get('technical_event_conflict')}")
    lines.append(f"- Alignment            : {ctx.get('causal_alignment')}")
    lines.append(f"- Verdict              : {ctx.get('causal_verdict')}")
    if ctx.get("internal_causes"):
        lines.append("\nInternal Causes:")
        for c in ctx.get("internal_causes", [])[:8]:
            lines.append(f"- {c.get('cause')}: dir={c.get('direction')} | conf={c.get('confidence')} | score={c.get('score')} | {c.get('detail')}")
    if data.get("source_health"):
        lines.append("\nSource Health:")
        for s in data.get("source_health", [])[:12]:
            status = s.get("status")
            err = f" | err={s.get('error')}" if s.get("error") and not compact else ""
            lines.append(f"- {s.get('source_id')}: {status} | {s.get('tier')} | dir={s.get('direction')} | risk={s.get('event_risk')}{err}")
    if not compact and data.get("source_results"):
        lines.append("\nSource Summaries:")
        for s in data.get("source_results", [])[:12]:
            lines.append(f"- {s.get('source_id')}: {s.get('summary')}")
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


def _append_observation(report: CausalReport) -> Path:
    CAUSAL_DIR.mkdir(parents=True, exist_ok=True)
    ctx = report.context or {}
    row = {
        "run_id": report.run_id,
        "generated_utc": report.generated_utc,
        "version": report.version,
        "status": report.status,
        "symbol": report.symbol,
        "timeframe": report.timeframe,
        "collect_live": report.collect_live,
        "primary_cause": ctx.get("primary_cause", ""),
        "cause_confidence": ctx.get("cause_confidence", ""),
        "catalyst_score": ctx.get("catalyst_score", ""),
        "event_risk": ctx.get("event_risk", ""),
        "technical_event_conflict": ctx.get("technical_event_conflict", ""),
        "causal_alignment": ctx.get("causal_alignment", ""),
        "causal_verdict": ctx.get("causal_verdict", ""),
        "source_count": report.source_count,
        "successful_sources": report.successful_sources,
        "trusted_successful_sources": report.trusted_successful_sources,
        "manual_events_loaded": report.manual_events_loaded,
        "auto_events_loaded": report.auto_events_loaded,
    }
    exists = CAUSAL_OBSERVATIONS_CSV.exists() and CAUSAL_OBSERVATIONS_CSV.stat().st_size > 0
    with CAUSAL_OBSERVATIONS_CSV.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    return CAUSAL_OBSERVATIONS_CSV


def save_causal_report(report: CausalReport) -> Tuple[Path, Path, Path, Path]:
    CAUSAL_DIR.mkdir(parents=True, exist_ok=True)
    CAUSAL_SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    data = asdict(report)
    json_path = CAUSAL_DIR / f"causal_intelligence_{report.run_id}.json"
    md_path = CAUSAL_DIR / f"causal_intelligence_report_{report.run_id}.md"
    source_csv = CAUSAL_DIR / f"causal_source_health_{report.run_id}.csv"
    write_json(json_path, data)
    write_text(md_path, format_causal_console(report, compact=False))
    if pd is not None:
        save_dataframe_csv(source_csv, pd.DataFrame(report.source_health))
    else:
        with source_csv.open("w", newline="", encoding="utf-8-sig") as f:
            if report.source_health:
                writer = csv.DictWriter(f, fieldnames=list(report.source_health[0].keys()))
                writer.writeheader(); writer.writerows(report.source_health)
    obs_path = _append_observation(report)
    # Also store full source payload summaries under research suite folder for GitHub artifact collection.
    SUITE_DIR.mkdir(parents=True, exist_ok=True)
    write_json(SUITE_DIR / f"causal_intelligence_{report.run_id}.json", data)
    return json_path, md_path, source_csv, obs_path
