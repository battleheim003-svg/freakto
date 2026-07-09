"""
Freakto v7.0.0 - Market Narrative Engine

Research-only narrative layer that turns cleaned event/causal context into a
compact market story. It does not create Paper/Live trades and never sends
orders. The goal is to explain *why* market conditions may be moving: macro,
regulation, exchange/company catalysts, protocol/security, liquidity, or mixed
conflict.
"""
from __future__ import annotations

import csv
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

from engine.research_utils import LOG_DIR, RESEARCH_DIR, run_id, safe_float, utc_now_iso, write_json, write_text, save_dataframe_csv

VERSION = "v7.0.0"
NARRATIVE_DIR = LOG_DIR / "narrative"
SUITE_DIR = RESEARCH_DIR / "v6_suite"
AUTO_EVENTS_FILE = Path("data") / "auto_events.csv"
MANUAL_EVENTS_FILE = Path("data") / "manual_events.csv"
CAUSAL_OBSERVATIONS_FILE = LOG_DIR / "causal" / "causal_observations.csv"
NARRATIVE_OBSERVATIONS_CSV = NARRATIVE_DIR / "market_narrative_observations.csv"

THEME_ALIASES = {
    "macro": "MACRO_POLICY",
    "regulatory": "REGULATORY_RISK",
    "exchange_listing": "EXCHANGE_CATALYSTS",
    "exchange": "EXCHANGE_CATALYSTS",
    "exchange_company": "EXCHANGE_CATALYSTS",
    "protocol": "PROTOCOL_OR_SECURITY",
    "security": "PROTOCOL_OR_SECURITY",
    "liquidity": "LIQUIDITY_FLOW",
    "defi_liquidity": "LIQUIDITY_FLOW",
    "media": "MEDIA_CONTEXT",
}

TIER_WEIGHT = {
    "TIER_0_MANUAL_CURATED": 1.20,
    "TIER_1_OFFICIAL_REGULATOR": 1.15,
    "TIER_1_OFFICIAL_MACRO": 1.15,
    "TIER_1_OFFICIAL_EXCHANGE_NEWS": 1.10,
    "TIER_1_OFFICIAL_PROTOCOL": 1.10,
    "TIER_2_OFFICIAL_COMPANY_BLOG": 0.70,
    "TIER_2_REPUTABLE_MEDIA": 0.65,
    "TIER_3_AGGREGATOR_OR_SENTIMENT": 0.35,
}
CONF_WEIGHT = {"HIGH": 1.0, "MEDIUM": 0.70, "LOW": 0.40}
IMPACT_WEIGHT = {"HIGH": 1.0, "MEDIUM": 0.55, "LOW": 0.25}

@dataclass
class NarrativeDriver:
    theme: str
    title: str
    source_id: str
    source_tier: str
    direction: str
    impact: str
    confidence: str
    weight: float
    timestamp_utc: str
    source_url: str = ""
    event_type: str = ""
    event_quality: str = ""

@dataclass
class MarketNarrativeReport:
    run_id: str
    generated_utc: str
    version: str
    status: str
    symbol: str
    timeframe: str
    lookback_hours: int
    auto_events_loaded: int
    manual_events_loaded: int
    accepted_events: int
    noise_filtered_events: int
    narrative_label: str
    narrative_confidence: str
    net_direction_score: float
    dominant_direction: str
    dominant_theme: str
    event_risk: str
    technical_event_conflict: str
    narrative_summary: str
    driver_count: int
    top_drivers: List[Dict[str, Any]] = field(default_factory=list)
    theme_scores: List[Dict[str, Any]] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    latest_causal_context: Dict[str, Any] = field(default_factory=dict)
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
    if pd is not None:
        try:
            dt = pd.to_datetime(text, utc=True, errors="coerce")
            if not pd.isna(dt):
                return dt.to_pydatetime().astimezone(timezone.utc)
        except Exception:
            return None
    return None


def _read_csv_rows(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open("r", newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def _direction_sign(direction: str) -> int:
    d = _upper(direction, "NEUTRAL")
    if d in {"BULLISH", "LONG", "POSITIVE", "UP"}:
        return 1
    if d in {"BEARISH", "SHORT", "NEGATIVE", "DOWN"}:
        return -1
    return 0


def _theme(row: Dict[str, Any]) -> str:
    raw = _norm(row.get("event_type") or row.get("source_category"), "unknown").lower()
    return THEME_ALIASES.get(raw, raw.upper() if raw else "UNKNOWN")


def _row_is_noise(row: Dict[str, Any]) -> Tuple[bool, str]:
    title = _norm(row.get("title") or row.get("description")).lower()
    source_id = _norm(row.get("source_id"))
    url = _norm(row.get("source_url")).lower()
    quality = _upper(row.get("event_quality"))
    if quality.startswith("REJECTED"):
        return True, quality
    if source_id == "coinbase_blog" and "/blog" not in url:
        return True, "coinbase_non_blog_product_or_nav_link"
    bad = ["developer platform", "payments", "verified pools", "asset listings", "list your asset", "trusted by institutions", "privacy policy", "terms of use"]
    if any(x in title for x in bad):
        return True, "static_product_or_navigation_title"
    return False, ""


def _event_weight(row: Dict[str, Any], now: datetime) -> float:
    sign = _direction_sign(row.get("direction"))
    if sign == 0:
        return 0.0
    tier_w = TIER_WEIGHT.get(_upper(row.get("source_tier")), 0.50)
    conf_w = CONF_WEIGHT.get(_upper(row.get("confidence")), 0.50)
    impact_w = IMPACT_WEIGHT.get(_upper(row.get("impact")), 0.30)
    ts = _parse_dt(row.get("timestamp_utc")) or now
    age_hours = max(0.0, (now - ts).total_seconds() / 3600.0)
    recency_w = max(0.35, math.exp(-age_hours / 168.0))
    return round(sign * 10.0 * tier_w * conf_w * impact_w * recency_w, 4)


def _load_latest_causal() -> Dict[str, Any]:
    rows = _read_csv_rows(CAUSAL_OBSERVATIONS_FILE)
    return rows[-1] if rows else {}


def _drivers_from_rows(rows: List[Dict[str, Any]], *, symbol: str, lookback_hours: int) -> Tuple[List[NarrativeDriver], int]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=lookback_hours)
    drivers: List[NarrativeDriver] = []
    noise = 0
    symbol_u = symbol.upper()
    for row in rows:
        event_symbol = _norm(row.get("symbol"), "ALL").upper()
        if event_symbol not in {"ALL", symbol_u, symbol_u.replace("-", "/")}:
            continue
        ts = _parse_dt(row.get("timestamp_utc"))
        if ts is not None and ts < cutoff:
            continue
        is_noise, _ = _row_is_noise(row)
        if is_noise:
            noise += 1
            continue
        w = _event_weight(row, now)
        if abs(w) <= 0:
            # Neutral events can increase risk, but they are not directional drivers.
            continue
        drivers.append(NarrativeDriver(
            theme=_theme(row),
            title=_norm(row.get("title") or row.get("description"))[:260],
            source_id=_norm(row.get("source_id"), "manual_events"),
            source_tier=_norm(row.get("source_tier"), row.get("reliability_tier") or "TIER_0_MANUAL_CURATED"),
            direction=_upper(row.get("direction"), "NEUTRAL"),
            impact=_upper(row.get("impact"), "LOW"),
            confidence=_upper(row.get("confidence"), "LOW"),
            weight=w,
            timestamp_utc=(ts.isoformat() if ts else _norm(row.get("timestamp_utc"))),
            source_url=_norm(row.get("source_url")),
            event_type=_norm(row.get("event_type")),
            event_quality=_norm(row.get("event_quality")),
        ))
    drivers.sort(key=lambda d: abs(d.weight), reverse=True)
    return drivers, noise


def _manual_to_auto_shape(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for r in rows:
        row = dict(r)
        row.setdefault("source_id", "manual_events")
        row.setdefault("source_name", r.get("source_name", "Manual Curated Event"))
        row.setdefault("source_tier", "TIER_0_MANUAL_CURATED")
        row.setdefault("title", r.get("description", "Manual event"))
        row.setdefault("event_quality", "CURATED_MANUAL_EVENT")
        out.append(row)
    return out


def run_market_narrative(*, symbol: str = "BTC/USDT", timeframe: str = "4h", lookback_hours: int = 168) -> MarketNarrativeReport:
    rid = run_id("market_narrative")
    generated = utc_now_iso()
    auto_rows = _read_csv_rows(AUTO_EVENTS_FILE)
    manual_rows = _manual_to_auto_shape(_read_csv_rows(MANUAL_EVENTS_FILE))
    drivers, noise_auto = _drivers_from_rows(auto_rows, symbol=symbol, lookback_hours=lookback_hours)
    manual_drivers, noise_manual = _drivers_from_rows(manual_rows, symbol=symbol, lookback_hours=lookback_hours)
    all_drivers = sorted(drivers + manual_drivers, key=lambda d: abs(d.weight), reverse=True)
    noise_count = noise_auto + noise_manual

    theme_map: Dict[str, Dict[str, Any]] = {}
    for d in all_drivers:
        bucket = theme_map.setdefault(d.theme, {"theme": d.theme, "score": 0.0, "drivers": 0, "bullish": 0, "bearish": 0})
        bucket["score"] += d.weight
        bucket["drivers"] += 1
        if d.weight > 0:
            bucket["bullish"] += 1
        elif d.weight < 0:
            bucket["bearish"] += 1
    theme_scores = []
    for b in theme_map.values():
        b = dict(b)
        b["score"] = round(b["score"], 4)
        b["abs_score"] = round(abs(b["score"]), 4)
        theme_scores.append(b)
    theme_scores.sort(key=lambda x: x["abs_score"], reverse=True)

    net = round(sum(d.weight for d in all_drivers), 4)
    bull_strength = sum(max(0, d.weight) for d in all_drivers)
    bear_strength = abs(sum(min(0, d.weight) for d in all_drivers))
    dominant_direction = "BULLISH" if net > 3 else "BEARISH" if net < -3 else "MIXED_OR_NEUTRAL"
    dominant_theme = theme_scores[0]["theme"] if theme_scores else "NO_THEME"

    contradictions = []
    if bull_strength >= 8 and bear_strength >= 8:
        contradictions.append(f"همزمان eventهای bullish و bearish قوی دیده شد: bull={round(bull_strength,2)}, bear={round(bear_strength,2)}")
    causal = _load_latest_causal()
    causal_conflict = _upper(causal.get("technical_event_conflict"), "LOW")
    if causal_conflict in {"HIGH", "MEDIUM"}:
        contradictions.append(f"Causal Intelligence تضاد {causal_conflict} با context تکنیکال گزارش کرده است.")

    event_risk = "LOW"
    if any(_upper(d.impact) == "HIGH" and d.theme in {"REGULATORY_RISK", "MACRO_POLICY", "PROTOCOL_OR_SECURITY"} for d in all_drivers[:8]):
        event_risk = "HIGH"
    elif all_drivers:
        event_risk = "MEDIUM"

    if not all_drivers:
        label = "NO_CLEAR_MARKET_NARRATIVE"
        conf = "LOW"
    elif contradictions:
        label = "MIXED_NARRATIVE_CONFLICT"
        conf = "MEDIUM" if len(all_drivers) >= 4 else "LOW"
    elif dominant_theme == "REGULATORY_RISK" and dominant_direction == "BEARISH":
        label = "REGULATORY_RISK_OFF"
        conf = "HIGH" if abs(net) >= 12 else "MEDIUM"
    elif dominant_theme == "MACRO_POLICY":
        label = "MACRO_POLICY_DOMINANT"
        conf = "HIGH" if abs(net) >= 12 else "MEDIUM"
    elif dominant_theme == "EXCHANGE_CATALYSTS" and dominant_direction == "BULLISH":
        label = "EXCHANGE_CATALYST_RISK_ON"
        conf = "MEDIUM"
    elif dominant_theme == "PROTOCOL_OR_SECURITY":
        label = "PROTOCOL_SECURITY_DRIVER"
        conf = "MEDIUM"
    else:
        label = "EVENT_CONTEXT_DOMINANT"
        conf = "MEDIUM" if len(all_drivers) >= 3 else "LOW"

    status = "MARKET_NARRATIVE_READY"
    blockers: List[str] = []
    if not auto_rows and not manual_rows:
        status = "NO_EVENT_LEDGER"
        blockers.append("هیچ auto_events/manual_events برای ساخت روایت بازار وجود ندارد.")
    elif not all_drivers:
        status = "MARKET_NARRATIVE_NO_DIRECTIONAL_DRIVERS"
    elif contradictions:
        status = "MARKET_NARRATIVE_WITH_CONFLICTS"

    summary = _build_summary(label, dominant_direction, dominant_theme, net, event_risk, all_drivers)
    warnings = [
        "Market Narrative فقط روایت پژوهشی می‌سازد؛ سیگنال خرید/فروش مستقل نیست.",
        "اگر event sourceها نویز HTML/marketing بدهند، v7 آن‌ها را فیلتر می‌کند اما همچنان باید source health بررسی شود.",
    ]
    recommendations = [
        "automatic_event_collector_dashboard.py --compact باید قبل از market_narrative_dashboard.py اجرا شود.",
        "اگر Narrative و Technical conflict بالا باشد، تصمیم فقط Research/Watchlist بماند.",
        "برای ارتقا به Gate، narrative باید در Forward با outcomeهای بعدی validate شود.",
    ]
    return MarketNarrativeReport(
        run_id=rid,
        generated_utc=generated,
        version=VERSION,
        status=status,
        symbol=symbol,
        timeframe=timeframe,
        lookback_hours=lookback_hours,
        auto_events_loaded=len(auto_rows),
        manual_events_loaded=len(manual_rows),
        accepted_events=len(all_drivers),
        noise_filtered_events=noise_count,
        narrative_label=label,
        narrative_confidence=conf,
        net_direction_score=net,
        dominant_direction=dominant_direction,
        dominant_theme=dominant_theme,
        event_risk=event_risk,
        technical_event_conflict=causal_conflict,
        narrative_summary=summary,
        driver_count=len(all_drivers),
        top_drivers=[asdict(d) for d in all_drivers[:12]],
        theme_scores=theme_scores[:12],
        contradictions=contradictions,
        latest_causal_context=causal,
        blockers=blockers,
        warnings=warnings,
        recommendations=recommendations,
    )


def _build_summary(label: str, direction: str, theme: str, net: float, risk: str, drivers: List[NarrativeDriver]) -> str:
    if not drivers:
        return "روایت قابل اتکا از eventهای فعلی ساخته نشد؛ داده‌ها یا خنثی‌اند یا فیلتر نویز حذفشان کرده است."
    top = drivers[0]
    return (
        f"Narrative={label}; direction={direction}; theme={theme}; net_score={net}; risk={risk}. "
        f"محرک اصلی فعلی از {top.source_id} است: {top.title[:120]}"
    )


def format_market_narrative_console(report: MarketNarrativeReport, compact: bool = True) -> str:
    data = asdict(report)
    sep = "=" * 110
    lines = [sep, f"🧭 Freakto Market Narrative Engine {VERSION}", sep]
    lines.append(f"Status                 : {data.get('status')}")
    lines.append(f"Run ID                 : {data.get('run_id')}")
    lines.append(f"Symbol / TF            : {data.get('symbol')} | {data.get('timeframe')}")
    lines.append(f"Lookback Hours         : {data.get('lookback_hours')}")
    lines.append(f"Auto / Manual Events   : {data.get('auto_events_loaded')} / {data.get('manual_events_loaded')}")
    lines.append(f"Accepted / Noise       : {data.get('accepted_events')} / {data.get('noise_filtered_events')}")
    lines.append("")
    lines.append("Market Narrative:")
    lines.append(f"- Label                : {data.get('narrative_label')}")
    lines.append(f"- Confidence           : {data.get('narrative_confidence')}")
    lines.append(f"- Direction            : {data.get('dominant_direction')}")
    lines.append(f"- Dominant Theme       : {data.get('dominant_theme')}")
    lines.append(f"- Net Direction Score  : {data.get('net_direction_score')}")
    lines.append(f"- Event Risk           : {data.get('event_risk')}")
    lines.append(f"- Tech/Event Conflict  : {data.get('technical_event_conflict')}")
    lines.append(f"- Summary              : {data.get('narrative_summary')}")
    if data.get("theme_scores"):
        lines.append("\nTheme Scores:")
        for r in data.get("theme_scores", [])[:8]:
            lines.append(f"- {r.get('theme')}: score={r.get('score')} | drivers={r.get('drivers')} | bull={r.get('bullish')} | bear={r.get('bearish')}")
    if data.get("top_drivers"):
        lines.append("\nTop Narrative Drivers:")
        for d in data.get("top_drivers", [])[:8]:
            lines.append(f"- {d.get('direction')} | w={d.get('weight')} | {d.get('theme')} | {d.get('source_id')} | {d.get('title')}")
    if data.get("contradictions"):
        lines.append("\nContradictions:")
        lines.extend([f"⚠️ {c}" for c in data.get("contradictions", [])])
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


def _append_observation(report: MarketNarrativeReport) -> Path:
    NARRATIVE_DIR.mkdir(parents=True, exist_ok=True)
    row = {
        "run_id": report.run_id,
        "generated_utc": report.generated_utc,
        "version": report.version,
        "status": report.status,
        "symbol": report.symbol,
        "timeframe": report.timeframe,
        "narrative_label": report.narrative_label,
        "narrative_confidence": report.narrative_confidence,
        "dominant_direction": report.dominant_direction,
        "dominant_theme": report.dominant_theme,
        "net_direction_score": report.net_direction_score,
        "event_risk": report.event_risk,
        "technical_event_conflict": report.technical_event_conflict,
        "accepted_events": report.accepted_events,
        "noise_filtered_events": report.noise_filtered_events,
    }
    exists = NARRATIVE_OBSERVATIONS_CSV.exists() and NARRATIVE_OBSERVATIONS_CSV.stat().st_size > 0
    with NARRATIVE_OBSERVATIONS_CSV.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    return NARRATIVE_OBSERVATIONS_CSV


def save_market_narrative_report(report: MarketNarrativeReport) -> Tuple[Path, Path, Path, Path]:
    NARRATIVE_DIR.mkdir(parents=True, exist_ok=True)
    SUITE_DIR.mkdir(parents=True, exist_ok=True)
    data = asdict(report)
    json_path = NARRATIVE_DIR / f"market_narrative_{report.run_id}.json"
    md_path = NARRATIVE_DIR / f"market_narrative_report_{report.run_id}.md"
    drivers_csv = NARRATIVE_DIR / f"market_narrative_drivers_{report.run_id}.csv"
    write_json(json_path, data)
    write_text(md_path, format_market_narrative_console(report, compact=False))
    if pd is not None:
        save_dataframe_csv(drivers_csv, pd.DataFrame(report.top_drivers))
    else:
        with drivers_csv.open("w", newline="", encoding="utf-8-sig") as f:
            if report.top_drivers:
                writer = csv.DictWriter(f, fieldnames=list(report.top_drivers[0].keys()))
                writer.writeheader(); writer.writerows(report.top_drivers)
    obs = _append_observation(report)
    write_json(SUITE_DIR / f"market_narrative_{report.run_id}.json", data)
    return json_path, md_path, drivers_csv, obs


def attach_market_narrative_to_opportunity(opportunity: Any, *, symbol: str = "BTC/USDT", timeframe: str = "4h") -> MarketNarrativeReport:
    report = run_market_narrative(symbol=symbol, timeframe=timeframe)
    raw = getattr(opportunity, "raw", None)
    if raw is None:
        raw = {}
        setattr(opportunity, "raw", raw)
    raw.update({
        "market_narrative_label": report.narrative_label,
        "market_narrative_confidence": report.narrative_confidence,
        "market_narrative_direction": report.dominant_direction,
        "market_narrative_theme": report.dominant_theme,
        "market_narrative_score": report.net_direction_score,
        "market_narrative_event_risk": report.event_risk,
        "market_narrative_conflict": report.technical_event_conflict,
        "market_narrative_summary": report.narrative_summary,
    })
    return report
