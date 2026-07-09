
"""
Freakto v8.0.0 - Root Cause Discovery Engine

Research-only layer that estimates *probable* root causes behind the current
market context/decision by combining cleaned events, causal context, market
narrative, narrative/decision conflict, and internal market features.

It is deliberately conservative: it produces weighted hypotheses and evidence,
not factual claims of causation. It never creates Paper/Live trades and never
sends orders.
"""
from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

from engine.research_utils import LOG_DIR, RESEARCH_DIR, run_id, safe_float, safe_int, utc_now_iso, write_json, write_text, save_dataframe_csv

VERSION = "v8.1.0"
ROOT_CAUSE_DIR = LOG_DIR / "root_cause"
NARRATIVE_DIR = LOG_DIR / "narrative"
CAUSAL_DIR = LOG_DIR / "causal"
SUITE_DIR = RESEARCH_DIR / "v6_suite"

AUTO_EVENTS_FILE = Path("data") / "auto_events.csv"
MANUAL_EVENTS_FILE = Path("data") / "manual_events.csv"
DECISIONS_FILE = LOG_DIR / "decisions.csv"
CAUSAL_OBSERVATIONS_FILE = CAUSAL_DIR / "causal_observations.csv"
NARRATIVE_OBSERVATIONS_FILE = NARRATIVE_DIR / "market_narrative_observations.csv"
NARRATIVE_DECISION_FILE = NARRATIVE_DIR / "narrative_decision_observations.csv"
ROOT_CAUSE_OBSERVATIONS_FILE = ROOT_CAUSE_DIR / "root_cause_observations.csv"

CAUSE_LABELS = {
    "MACRO_POLICY_PRESSURE": "سیاست پولی/کلان، سخنرانی‌ها، FOMC، CPI، ریسک بانکی یا liquidity macro.",
    "REGULATORY_RISK": "فشار نظارتی، enforcement، fraud، litigation یا headlineهای ریسک‌زای قانون‌گذاری.",
    "REGULATORY_ACCESS_OR_MODERNIZATION": "رویدادهای مثبت/خنثی درباره market access، ETF، IPO modernization یا دسترسی عمومی.",
    "EXCHANGE_MARKET_ACCESS": "رویدادهای exchange، listing، derivatives، product launch یا market access مربوط به صرافی‌ها.",
    "PROTOCOL_UPGRADE_OR_SECURITY": "رویدادهای protocol، upgrade، security، exploit یا foundation announcement.",
    "TECHNICAL_STRUCTURE_MOMENTUM": "علت درون‌بازاری از ساختار، trend، momentum یا شکست تکنیکال.",
    "LIQUIDITY_VOLUME_FLOW": "جریان حجم/نقدینگی، جهش volume، TVL/stablecoin/liquidity یا فشار flow.",
    "DERIVATIVES_LEVERAGE_FLOW": "funding، open interest، premium، liquidation یا leverage-related movement.",
    "MIXED_EVENT_CONFLICT": "چند علت متضاد همزمان دیده شده و علت غالب هنوز قطعی نیست.",
    "UNKNOWN_OR_INSUFFICIENT_EVIDENCE": "شواهد کافی برای نسبت دادن حرکت به علت مشخص وجود ندارد.",
}

DIRECTION_SIGN = {"BULLISH": 1, "BEARISH": -1, "NEUTRAL": 0, "MIXED": 0, "MIXED_OR_NEUTRAL": 0}
TIER_WEIGHT = {
    "TIER_0_MANUAL_CURATED": 1.20,
    "TIER_1_OFFICIAL_REGULATOR": 1.15,
    "TIER_1_OFFICIAL_MACRO": 1.15,
    "TIER_1_OFFICIAL_EXCHANGE_NEWS": 1.10,
    "TIER_1_OFFICIAL_PROTOCOL": 1.10,
    "TIER_2_OFFICIAL_COMPANY_BLOG": 0.70,
    "TIER_2_REPUTABLE_MEDIA": 0.65,
    "TIER_2_MARKET_AGGREGATOR": 0.55,
    "TIER_3_AGGREGATOR_OR_SENTIMENT": 0.35,
}
IMPACT_WEIGHT = {"HIGH": 1.00, "MEDIUM": 0.55, "LOW": 0.25}
CONF_WEIGHT = {"HIGH": 1.00, "MEDIUM": 0.70, "LOW": 0.40}


@dataclass
class CauseEvidence:
    cause: str
    source: str
    direction: str
    weight: float
    quality: str
    title: str
    note: str
    timestamp_utc: str = ""
    source_url: str = ""


@dataclass
class RootCauseCandidate:
    cause: str
    description: str
    direction: str
    evidence_score: float
    probability_pct: float
    evidence_count: int
    official_evidence_count: int
    strongest_source: str
    verdict: str
    evidence: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class RootCauseReport:
    run_id: str
    generated_utc: str
    version: str
    status: str
    symbol: str
    timeframe: str
    lookback_hours: int
    latest_decision_id: str
    decision_side: str
    decision_score: int
    narrative_label: str
    narrative_direction: str
    narrative_theme: str
    narrative_confidence: str
    narrative_score: float
    causal_primary_cause: str
    causal_verdict: str
    catalyst_score: int
    primary_root_cause: str
    root_cause_direction: str
    root_cause_confidence: str
    root_cause_probability_pct: float
    root_cause_evidence_quality: str
    root_cause_verdict: str
    root_cause_summary: str
    evidence_total: int
    official_evidence_total: int
    accepted_event_rows: int
    top_causes: List[Dict[str, Any]] = field(default_factory=list)
    root_cause_evidence: List[Dict[str, Any]] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    latest_decision: Dict[str, Any] = field(default_factory=dict)
    latest_narrative: Dict[str, Any] = field(default_factory=dict)
    latest_causal: Dict[str, Any] = field(default_factory=dict)
    latest_narrative_decision: Dict[str, Any] = field(default_factory=dict)


def _norm(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return default
    return text


def _upper(value: Any, default: str = "") -> str:
    return _norm(value, default).upper().replace("-", "_").replace(" ", "_")


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    try:
        return max(low, min(high, float(value)))
    except Exception:
        return low


def _read_csv_rows(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open("r", newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def _latest_row(path: Path) -> Dict[str, Any]:
    rows = _read_csv_rows(path)
    return rows[-1] if rows else {}


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


def _recency_multiplier(ts: str, lookback_hours: int) -> float:
    dt = _parse_dt(ts)
    if not dt:
        return 0.75
    age_hours = max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0)
    if age_hours <= 24:
        return 1.0
    if age_hours <= 72:
        return 0.85
    if age_hours <= lookback_hours:
        return 0.65
    return 0.25


def _symbol_matches(row_symbol: str, symbol: str) -> bool:
    rs = _upper(row_symbol, "ALL")
    s = _upper(symbol, "BTC/USDT")
    base = s.split("/")[0]
    return rs in {"", "ALL", "GLOBAL", s, base}


def _event_base_weight(row: Dict[str, Any], lookback_hours: int) -> float:
    tier = _upper(row.get("source_tier"), "TIER_3_AGGREGATOR_OR_SENTIMENT")
    impact = _upper(row.get("impact"), "MEDIUM")
    conf = _upper(row.get("confidence"), "MEDIUM")
    score = safe_float(row.get("auto_score"), 0.0) or 0.0
    ts = row.get("timestamp_utc") or row.get("collected_utc") or row.get("generated_utc")
    base = 10.0 * TIER_WEIGHT.get(tier, 0.45) * IMPACT_WEIGHT.get(impact, 0.45) * CONF_WEIGHT.get(conf, 0.65)
    # A small boost for rule-based event score without letting keyword score dominate.
    if score > 0:
        base += min(5.0, score / 5.0)
    return round(base * _recency_multiplier(ts, lookback_hours), 4)


def _dir(row: Dict[str, Any], default: str = "NEUTRAL") -> str:
    d = _upper(row.get("direction"), default)
    if d in {"BULLISH", "BEARISH", "NEUTRAL"}:
        return d
    return default


def _classify_event(row: Dict[str, Any]) -> str:
    title = (_norm(row.get("title")) + " " + _norm(row.get("description")) + " " + _norm(row.get("event_type")) + " " + _norm(row.get("tags"))).lower()
    source_id = _norm(row.get("source_id")).lower()
    tier = _norm(row.get("source_tier")).lower()
    category = _norm(row.get("source_category")).lower()

    if any(k in title for k in ["fomc", "federal reserve", "monetary policy", "interest rate", "inflation", "cpi", "aml", "bank", "minutes", "waller", "powell", "treasury", "dollar"]):
        return "MACRO_POLICY_PRESSURE"
    if any(k in title for k in ["enforcement", "fraud", "litigation", "lawsuit", "charged", "sanction", "anti-money laundering", "retail fraud", "risk warning"]):
        return "REGULATORY_RISK"
    if any(k in title for k in ["etf", "ipo", "market access", "modernizing", "expanding access", "roundtable", "approval"]):
        return "REGULATORY_ACCESS_OR_MODERNIZATION"
    if any(k in source_id for k in ["binance", "coinbase"]) or any(k in title for k in ["listing", "perpetual", "futures", "exchange", "derivatives", "launch"]):
        return "EXCHANGE_MARKET_ACCESS"
    if any(k in source_id for k in ["ethereum", "foundation"]) or any(k in title for k in ["upgrade", "hard fork", "security", "exploit", "vulnerability", "protocol", "mainnet", "ethereum"]):
        return "PROTOCOL_UPGRADE_OR_SECURITY"
    if any(k in title for k in ["tvl", "stablecoin", "liquidity", "inflow", "outflow", "reserves"]):
        return "LIQUIDITY_VOLUME_FLOW"
    if any(k in title for k in ["funding", "open interest", "liquidation", "premium", "leverage"]):
        return "DERIVATIVES_LEVERAGE_FLOW"
    if "official_macro" in tier or "macro" in category:
        return "MACRO_POLICY_PRESSURE"
    if "official_regulator" in tier or "regulator" in category:
        return "REGULATORY_RISK"
    return "UNKNOWN_OR_INSUFFICIENT_EVIDENCE"


def _quality(row: Dict[str, Any]) -> str:
    tier = _upper(row.get("source_tier"), "")
    if tier.startswith("TIER_1") or tier == "TIER_0_MANUAL_CURATED":
        return "HIGH"
    if tier.startswith("TIER_2"):
        return "MEDIUM"
    return "LOW"


def _event_evidence(symbol: str, lookback_hours: int) -> List[CauseEvidence]:
    rows = []
    for r in _read_csv_rows(AUTO_EVENTS_FILE):
        rr = dict(r)
        rr.setdefault("source_id", rr.get("source_name", "auto_events"))
        rows.append(rr)
    for r in _read_csv_rows(MANUAL_EVENTS_FILE):
        rr = dict(r)
        rr.setdefault("source_id", "manual_events")
        rr.setdefault("source_name", r.get("source_name", "Manual Curated Event"))
        rr.setdefault("source_tier", "TIER_0_MANUAL_CURATED")
        rr.setdefault("title", r.get("description", "Manual curated event"))
        rr.setdefault("event_quality", "CURATED_MANUAL_EVENT")
        rows.append(rr)

    out: List[CauseEvidence] = []
    now = datetime.now(timezone.utc)
    for r in rows:
        if not _symbol_matches(r.get("symbol", "ALL"), symbol):
            continue
        ts = r.get("timestamp_utc") or r.get("collected_utc") or ""
        dt = _parse_dt(ts)
        if dt and (now - dt) > timedelta(hours=lookback_hours):
            continue
        cause = _classify_event(r)
        if cause == "UNKNOWN_OR_INSUFFICIENT_EVIDENCE":
            continue
        weight = _event_base_weight(r, lookback_hours)
        if weight <= 0:
            continue
        direction = _dir(r)
        # Regulatory access can be neutral unless explicitly bullish/bearish.
        if cause == "REGULATORY_ACCESS_OR_MODERNIZATION" and direction == "NEUTRAL":
            direction = "BULLISH"
        out.append(CauseEvidence(
            cause=cause,
            source=_norm(r.get("source_id") or r.get("source_name"), "event"),
            direction=direction,
            weight=round(weight, 4),
            quality=_quality(r),
            title=_norm(r.get("title") or r.get("description"), "Untitled event")[:220],
            note=f"event_type={_norm(r.get('event_type'))}; tier={_norm(r.get('source_tier'))}; impact={_norm(r.get('impact'))}",
            timestamp_utc=ts,
            source_url=_norm(r.get("source_url")),
        ))
    return out


def _latest_decision_evidence(decision: Dict[str, Any]) -> List[CauseEvidence]:
    evidence: List[CauseEvidence] = []
    if not decision:
        return evidence
    side = _upper(decision.get("side"), "NEUTRAL")
    direction = "BULLISH" if side == "LONG" else "BEARISH" if side == "SHORT" else "NEUTRAL"
    trend = safe_float(decision.get("trend_score"), 0.0) or 0.0
    momentum = safe_float(decision.get("momentum_score"), 0.0) or 0.0
    structure = safe_float(decision.get("structure_score"), 0.0) or 0.0
    volume = safe_float(decision.get("volume_score"), 0.0) or 0.0
    score = safe_float(decision.get("score"), 0.0) or 0.0
    regime = _upper(decision.get("regime_label"), "UNKNOWN")
    if structure >= 10 or momentum >= 20 or trend >= 20:
        evidence.append(CauseEvidence(
            cause="TECHNICAL_STRUCTURE_MOMENTUM",
            source="decision_engine_features",
            direction=direction,
            weight=round(min(18.0, 4.0 + structure * 0.9 + momentum * 0.25 + trend * 0.15), 4),
            quality="MEDIUM",
            title="Decision Engine structure/trend/momentum evidence",
            note=f"trend={trend}; momentum={momentum}; structure={structure}; score={score}; regime={regime}",
        ))
    if volume >= 10:
        evidence.append(CauseEvidence(
            cause="LIQUIDITY_VOLUME_FLOW",
            source="decision_engine_volume",
            direction=direction,
            weight=round(min(15.0, 3.0 + volume * 0.9), 4),
            quality="MEDIUM",
            title="Volume/flow evidence from Decision Engine",
            note=f"volume_score={volume}; side={side}; regime={regime}",
        ))
    # Placeholder hooks for future derivatives/on-chain integrations. If the columns exist, use them.
    oi_change = safe_float(decision.get("open_interest_change_pct"), None)
    funding = safe_float(decision.get("funding_rate"), None)
    if oi_change is not None or funding is not None:
        weight = 5.0 + min(8.0, abs(oi_change or 0.0) * 0.4) + min(5.0, abs(funding or 0.0) * 1000)
        evidence.append(CauseEvidence(
            cause="DERIVATIVES_LEVERAGE_FLOW",
            source="derivatives_features",
            direction=direction,
            weight=round(weight, 4),
            quality="MEDIUM",
            title="Derivatives leverage/funding evidence",
            note=f"oi_change_pct={oi_change}; funding_rate={funding}",
        ))
    return evidence


def _narrative_evidence(narrative: Dict[str, Any]) -> List[CauseEvidence]:
    if not narrative:
        return []
    theme = _upper(narrative.get("dominant_theme") or narrative.get("narrative_theme"), "")
    label = _upper(narrative.get("narrative_label"), "")
    direction = _upper(narrative.get("dominant_direction") or narrative.get("narrative_direction"), "NEUTRAL")
    score = abs(safe_float(narrative.get("net_direction_score") or narrative.get("narrative_score"), 0.0) or 0.0)
    conf = _upper(narrative.get("narrative_confidence"), "LOW")
    risk = _upper(narrative.get("event_risk"), "LOW")
    cause = "UNKNOWN_OR_INSUFFICIENT_EVIDENCE"
    if theme == "MACRO_POLICY":
        cause = "MACRO_POLICY_PRESSURE"
    elif theme == "REGULATORY_RISK":
        cause = "REGULATORY_RISK" if direction != "BULLISH" else "REGULATORY_ACCESS_OR_MODERNIZATION"
    elif theme == "EXCHANGE_CATALYSTS":
        cause = "EXCHANGE_MARKET_ACCESS"
    elif theme == "PROTOCOL_OR_SECURITY":
        cause = "PROTOCOL_UPGRADE_OR_SECURITY"
    elif theme == "LIQUIDITY_FLOW":
        cause = "LIQUIDITY_VOLUME_FLOW"
    if cause == "UNKNOWN_OR_INSUFFICIENT_EVIDENCE":
        return []
    weight = min(20.0, 4.0 + score * 0.35 + (6 if conf == "HIGH" else 3 if conf == "MEDIUM" else 1))
    if risk == "HIGH":
        weight += 2.0
    if "MIXED" in label or "CONFLICT" in label:
        # Add both theme evidence and conflict evidence.
        return [
            CauseEvidence(cause=cause, source="market_narrative", direction=direction, weight=round(weight, 4), quality="MEDIUM", title=f"Market narrative theme: {theme}", note=f"label={label}; score={score}; confidence={conf}; risk={risk}"),
            CauseEvidence(cause="MIXED_EVENT_CONFLICT", source="market_narrative", direction="NEUTRAL", weight=round(min(15.0, weight * 0.75), 4), quality="MEDIUM", title="Narrative has mixed/conflicting drivers", note=f"label={label}; theme={theme}"),
        ]
    return [CauseEvidence(cause=cause, source="market_narrative", direction=direction, weight=round(weight, 4), quality="MEDIUM", title=f"Market narrative theme: {theme}", note=f"label={label}; score={score}; confidence={conf}; risk={risk}")]


def _causal_evidence(causal: Dict[str, Any]) -> List[CauseEvidence]:
    if not causal:
        return []
    primary = _upper(causal.get("primary_cause"), "")
    verdict = _upper(causal.get("causal_verdict"), "")
    catalyst = safe_float(causal.get("catalyst_score"), 0.0) or 0.0
    direction = _upper(causal.get("dominant_direction") or causal.get("causal_alignment"), "NEUTRAL")
    if direction not in {"BULLISH", "BEARISH", "NEUTRAL"}:
        direction = "NEUTRAL"
    cause = "UNKNOWN_OR_INSUFFICIENT_EVIDENCE"
    if "MACRO" in primary:
        cause = "MACRO_POLICY_PRESSURE"
    elif "REGUL" in primary or "SEC" in primary:
        cause = "REGULATORY_RISK"
    elif "EXTERNAL" in primary or "CONSENSUS" in primary:
        cause = "MIXED_EVENT_CONFLICT"
    elif "VOLUME" in primary or "LIQUID" in primary:
        cause = "LIQUIDITY_VOLUME_FLOW"
    elif "STRUCTURE" in primary or "TECH" in primary:
        cause = "TECHNICAL_STRUCTURE_MOMENTUM"
    if cause == "UNKNOWN_OR_INSUFFICIENT_EVIDENCE" and catalyst <= 0:
        return []
    weight = min(18.0, 4.0 + catalyst * 0.12)
    if "WEAK" in verdict or "RISKY" in verdict:
        weight *= 0.75
    return [CauseEvidence(cause=cause, source="causal_intelligence", direction=direction, weight=round(weight, 4), quality="MEDIUM", title=f"Causal context: {primary or 'UNKNOWN'}", note=f"verdict={verdict}; catalyst={catalyst}")]


def _build_candidates(evidence: List[CauseEvidence]) -> List[RootCauseCandidate]:
    buckets: Dict[str, Dict[str, Any]] = {}
    for e in evidence:
        if e.cause == "UNKNOWN_OR_INSUFFICIENT_EVIDENCE":
            continue
        b = buckets.setdefault(e.cause, {"score": 0.0, "evidence": [], "official": 0, "dir_score": 0.0, "sources": {}})
        b["score"] += max(0.0, float(e.weight))
        b["evidence"].append(e)
        if e.quality == "HIGH":
            b["official"] += 1
        b["dir_score"] += float(e.weight) * DIRECTION_SIGN.get(_upper(e.direction, "NEUTRAL"), 0)
        b["sources"][e.source] = b["sources"].get(e.source, 0.0) + float(e.weight)
    total = sum(max(0.0, b["score"]) for b in buckets.values())
    candidates: List[RootCauseCandidate] = []
    for cause, b in buckets.items():
        score = round(float(b["score"]), 4)
        prob = round(score / total * 100.0, 2) if total > 0 else 0.0
        dir_score = float(b["dir_score"])
        if dir_score > 2:
            direction = "BULLISH"
        elif dir_score < -2:
            direction = "BEARISH"
        else:
            direction = "MIXED_OR_NEUTRAL"
        strongest_source = ""
        if b["sources"]:
            strongest_source = sorted(b["sources"].items(), key=lambda kv: kv[1], reverse=True)[0][0]
        if prob >= 45 and b["official"] >= 2:
            verdict = "PRIMARY_PROBABLE_CAUSE"
        elif prob >= 25:
            verdict = "SUPPORTING_CAUSE"
        else:
            verdict = "WEAK_SUPPORTING_CAUSE"
        candidates.append(RootCauseCandidate(
            cause=cause,
            description=CAUSE_LABELS.get(cause, cause),
            direction=direction,
            evidence_score=score,
            probability_pct=prob,
            evidence_count=len(b["evidence"]),
            official_evidence_count=int(b["official"]),
            strongest_source=strongest_source,
            verdict=verdict,
            evidence=[asdict(x) for x in sorted(b["evidence"], key=lambda x: abs(float(x.weight)), reverse=True)[:8]],
        ))
    candidates.sort(key=lambda c: c.evidence_score, reverse=True)
    return candidates


def _latest_decision() -> Dict[str, Any]:
    return _latest_row(DECISIONS_FILE)


def _latest_narrative() -> Dict[str, Any]:
    return _latest_row(NARRATIVE_OBSERVATIONS_FILE)


def _latest_causal() -> Dict[str, Any]:
    row = _latest_row(CAUSAL_OBSERVATIONS_FILE)
    # Observations may store flat context fields; dashboards can also write JSON snapshots separately.
    return row


def _latest_narrative_decision() -> Dict[str, Any]:
    return _latest_row(NARRATIVE_DECISION_FILE)


def run_root_cause_discovery(*, symbol: str = "BTC/USDT", timeframe: str = "4h", lookback_hours: int = 168) -> RootCauseReport:
    rid = run_id("root_cause")
    generated = utc_now_iso()
    decision = _latest_decision()
    narrative = _latest_narrative()
    causal = _latest_causal()
    narrative_decision = _latest_narrative_decision()

    evidence: List[CauseEvidence] = []
    event_evidence = _event_evidence(symbol, lookback_hours)
    evidence.extend(event_evidence)
    evidence.extend(_narrative_evidence(narrative))
    evidence.extend(_causal_evidence(causal))
    evidence.extend(_latest_decision_evidence(decision))

    candidates = _build_candidates(evidence)
    blockers: List[str] = []
    contradictions: List[str] = []
    warnings = [
        "Root Cause Discovery احتمالات علّی پژوهشی می‌سازد؛ علت قطعی یا سیگنال خرید/فروش نیست.",
        "این ماژول از outcome/return آینده برای تشخیص علت استفاده نمی‌کند تا leakage ایجاد نشود.",
        "تا وقتی علت‌ها با forward outcomes اعتبارسنجی نشوند، Paper/Live نباید از آن‌ها استفاده کند.",
    ]
    recommendations = [
        "automatic_event_collector، causal_intelligence، market_narrative و narrative_decision را قبل از root_cause اجرا کن.",
        "اگر primary_root_cause چند هفته متوالی با outcome مثبت/منفی همبستگی داشت، بعداً می‌تواند وارد Root-Cause Gate Simulator شود.",
        "برای افزایش دقت، داده‌های derivatives/on-chain/ETF flow را به evidence registry اضافه کن.",
    ]

    accepted_events = len(event_evidence)
    official_total = sum(1 for e in evidence if e.quality == "HIGH")
    if not evidence:
        blockers.append("هیچ evidence قابل استفاده‌ای برای root-cause discovery پیدا نشد.")
    if not event_evidence:
        blockers.append("هیچ event evidence معتبر در lookback فعلی پیدا نشد.")
    if not narrative:
        blockers.append("market narrative موجود نیست؛ market_narrative_dashboard.py --compact را اجرا کن.")
    if not causal:
        blockers.append("causal observations موجود نیست؛ causal_intelligence_dashboard.py --compact را اجرا کن.")

    primary = candidates[0] if candidates else None
    # Contradiction detection: strong bullish and bearish cause groups at the same time.
    bull = sum(c.evidence_score for c in candidates if c.direction == "BULLISH")
    bear = sum(c.evidence_score for c in candidates if c.direction == "BEARISH")
    if bull >= 15 and bear >= 15:
        contradictions.append(f"شواهد bullish و bearish همزمان قوی‌اند: bull={round(bull,2)}, bear={round(bear,2)}")
    if primary and len(candidates) > 1 and candidates[1].probability_pct >= max(20.0, primary.probability_pct * 0.65):
        contradictions.append("علت دوم از نظر وزن به علت اول نزدیک است؛ root cause هنوز تک‌علتی نیست.")

    if not primary:
        status = "ROOT_CAUSE_INSUFFICIENT_EVIDENCE"
        confidence = "LOW"
        label = "UNKNOWN_OR_INSUFFICIENT_EVIDENCE"
        direction = "MIXED_OR_NEUTRAL"
        prob = 0.0
        quality = "LOW"
        verdict = "NO_PROBABLE_ROOT_CAUSE"
    else:
        label = primary.cause
        direction = primary.direction
        prob = primary.probability_pct
        if contradictions:
            status = "ROOT_CAUSE_MIXED_WITH_CONTRADICTIONS"
            confidence = "MEDIUM" if prob >= 35 and primary.official_evidence_count >= 2 else "LOW"
            verdict = "PROBABLE_CAUSE_BUT_CONFLICTED"
        elif prob >= 55 and primary.official_evidence_count >= 2 and primary.evidence_score >= 35:
            status = "ROOT_CAUSE_PRIMARY_PROBABLE"
            confidence = "HIGH"
            verdict = "PRIMARY_PROBABLE_ROOT_CAUSE"
        elif prob >= 35 and primary.evidence_score >= 20:
            status = "ROOT_CAUSE_RESEARCH_CANDIDATE"
            confidence = "MEDIUM"
            verdict = "ROOT_CAUSE_CANDIDATE_RESEARCH_ONLY"
        else:
            status = "ROOT_CAUSE_WEAK_OR_DISTRIBUTED"
            confidence = "LOW"
            verdict = "WEAK_OR_DISTRIBUTED_ROOT_CAUSE"
        high = sum(1 for e in evidence if e.quality == "HIGH")
        medium = sum(1 for e in evidence if e.quality == "MEDIUM")
        if high >= 4:
            quality = "HIGH"
        elif high + medium >= 3:
            quality = "MEDIUM"
        else:
            quality = "LOW"

    decision_side = _upper(decision.get("side"), "NEUTRAL") if decision else "NEUTRAL"
    decision_score = safe_int(decision.get("score"), 0) if decision else 0
    root_summary = _build_summary(label, direction, confidence, prob, candidates, contradictions)

    return RootCauseReport(
        run_id=rid,
        generated_utc=generated,
        version=VERSION,
        status=status,
        symbol=symbol,
        timeframe=timeframe,
        lookback_hours=lookback_hours,
        latest_decision_id=_norm(decision.get("decision_id")) if decision else "",
        decision_side=decision_side,
        decision_score=decision_score,
        narrative_label=_upper(narrative.get("narrative_label"), "UNKNOWN") if narrative else "UNKNOWN",
        narrative_direction=_upper(narrative.get("dominant_direction") or narrative.get("narrative_direction"), "UNKNOWN") if narrative else "UNKNOWN",
        narrative_theme=_upper(narrative.get("dominant_theme") or narrative.get("narrative_theme"), "UNKNOWN") if narrative else "UNKNOWN",
        narrative_confidence=_upper(narrative.get("narrative_confidence"), "UNKNOWN") if narrative else "UNKNOWN",
        narrative_score=round(safe_float(narrative.get("net_direction_score") or narrative.get("narrative_score"), 0.0) or 0.0, 4) if narrative else 0.0,
        causal_primary_cause=_upper(causal.get("primary_cause"), "UNKNOWN") if causal else "UNKNOWN",
        causal_verdict=_upper(causal.get("causal_verdict"), "UNKNOWN") if causal else "UNKNOWN",
        catalyst_score=safe_int(causal.get("catalyst_score"), 0) if causal else 0,
        primary_root_cause=label,
        root_cause_direction=direction,
        root_cause_confidence=confidence,
        root_cause_probability_pct=round(prob, 2),
        root_cause_evidence_quality=quality,
        root_cause_verdict=verdict,
        root_cause_summary=root_summary,
        evidence_total=len(evidence),
        official_evidence_total=official_total,
        accepted_event_rows=accepted_events,
        top_causes=[asdict(c) for c in candidates[:8]],
        root_cause_evidence=[asdict(e) for e in sorted(evidence, key=lambda e: abs(float(e.weight)), reverse=True)[:30]],
        blockers=blockers,
        contradictions=contradictions,
        warnings=warnings,
        recommendations=recommendations,
        latest_decision=decision,
        latest_narrative=narrative,
        latest_causal=causal,
        latest_narrative_decision=narrative_decision,
    )


def _build_summary(label: str, direction: str, confidence: str, prob: float, candidates: List[RootCauseCandidate], contradictions: List[str]) -> str:
    if not candidates:
        return "علت غالب قابل اتکا پیدا نشد؛ داده‌ها برای root-cause discovery کافی نیستند."
    top = candidates[0]
    top_ev = top.evidence[0] if top.evidence else {}
    summary = (
        f"Probable root cause={label}; direction={direction}; confidence={confidence}; share={round(prob,2)}%. "
        f"قوی‌ترین evidence از {top.strongest_source or top_ev.get('source','UNKNOWN')} است: {top_ev.get('title','')[:140]}"
    )
    if contradictions:
        summary += " | هشدار: شواهد متضاد همزمان وجود دارد."
    return summary


def format_root_cause_console(report: RootCauseReport, compact: bool = True) -> str:
    sep = "=" * 110
    lines = [sep, f"🧬 Freakto Root Cause Discovery Engine {VERSION}", sep]
    lines.append(f"Status                 : {report.status}")
    lines.append(f"Run ID                 : {report.run_id}")
    lines.append(f"Symbol / TF            : {report.symbol} | {report.timeframe}")
    lines.append(f"Lookback Hours         : {report.lookback_hours}")
    lines.append(f"Decision Side/Score    : {report.decision_side} | {report.decision_score}")
    lines.append(f"Narrative              : {report.narrative_label} | {report.narrative_direction} | {report.narrative_theme}")
    lines.append(f"Causal Context         : {report.causal_primary_cause} | catalyst={report.catalyst_score}/100")
    lines.append("")
    lines.append("Root Cause:")
    lines.append(f"- Primary              : {report.primary_root_cause}")
    lines.append(f"- Direction            : {report.root_cause_direction}")
    lines.append(f"- Confidence           : {report.root_cause_confidence}")
    lines.append(f"- Probability Share    : {report.root_cause_probability_pct}%")
    lines.append(f"- Evidence Quality     : {report.root_cause_evidence_quality}")
    lines.append(f"- Verdict              : {report.root_cause_verdict}")
    lines.append(f"- Summary              : {report.root_cause_summary}")
    lines.append(f"- Evidence Total       : {report.evidence_total} | official={report.official_evidence_total} | event_rows={report.accepted_event_rows}")
    if report.top_causes:
        lines.append("\nTop Cause Hypotheses:")
        for c in report.top_causes[:8]:
            lines.append(f"- {c.get('cause')}: p={c.get('probability_pct')}% | score={c.get('evidence_score')} | dir={c.get('direction')} | evidence={c.get('evidence_count')} | verdict={c.get('verdict')}")
    if report.root_cause_evidence and not compact:
        lines.append("\nEvidence:")
        for e in report.root_cause_evidence[:12]:
            lines.append(f"- {e.get('cause')} | {e.get('direction')} | w={e.get('weight')} | {e.get('source')} | {e.get('title')}")
    if report.contradictions:
        lines.append("\nContradictions:")
        lines.extend([f"⚠️ {c}" for c in report.contradictions])
    if report.blockers:
        lines.append("\nBlockers:")
        lines.extend([f"⛔ {b}" for b in report.blockers])
    if report.recommendations:
        lines.append("\nRecommendations:")
        lines.extend([f"→ {r}" for r in report.recommendations])
    if report.warnings:
        lines.append("\nWarnings:")
        lines.extend([f"⚠️ {w}" for w in report.warnings])
    lines.append(sep)
    return "\n".join(lines)


def _append_observation(report: RootCauseReport) -> Path:
    ROOT_CAUSE_DIR.mkdir(parents=True, exist_ok=True)
    row = {
        "run_id": report.run_id,
        "generated_utc": report.generated_utc,
        "version": report.version,
        "status": report.status,
        "symbol": report.symbol,
        "timeframe": report.timeframe,
        "decision_id": report.latest_decision_id,
        "decision_side": report.decision_side,
        "decision_score": report.decision_score,
        "primary_root_cause": report.primary_root_cause,
        "root_cause_direction": report.root_cause_direction,
        "root_cause_confidence": report.root_cause_confidence,
        "root_cause_probability_pct": report.root_cause_probability_pct,
        "root_cause_evidence_quality": report.root_cause_evidence_quality,
        "root_cause_verdict": report.root_cause_verdict,
        "evidence_total": report.evidence_total,
        "official_evidence_total": report.official_evidence_total,
        "narrative_label": report.narrative_label,
        "narrative_direction": report.narrative_direction,
        "narrative_theme": report.narrative_theme,
        "causal_primary_cause": report.causal_primary_cause,
        "catalyst_score": report.catalyst_score,
    }
    exists = ROOT_CAUSE_OBSERVATIONS_FILE.exists() and ROOT_CAUSE_OBSERVATIONS_FILE.stat().st_size > 0
    with ROOT_CAUSE_OBSERVATIONS_FILE.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    return ROOT_CAUSE_OBSERVATIONS_FILE


def save_root_cause_report(report: RootCauseReport) -> Tuple[Path, Path, Path, Path]:
    ROOT_CAUSE_DIR.mkdir(parents=True, exist_ok=True)
    SUITE_DIR.mkdir(parents=True, exist_ok=True)
    data = asdict(report)
    json_path = ROOT_CAUSE_DIR / f"root_cause_{report.run_id}.json"
    md_path = ROOT_CAUSE_DIR / f"root_cause_report_{report.run_id}.md"
    causes_csv = ROOT_CAUSE_DIR / f"root_cause_candidates_{report.run_id}.csv"
    write_json(json_path, data)
    write_text(md_path, format_root_cause_console(report, compact=False))
    if pd is not None:
        save_dataframe_csv(causes_csv, pd.DataFrame(report.top_causes))
    else:
        with causes_csv.open("w", newline="", encoding="utf-8-sig") as f:
            if report.top_causes:
                writer = csv.DictWriter(f, fieldnames=list(report.top_causes[0].keys()))
                writer.writeheader(); writer.writerows(report.top_causes)
    obs = _append_observation(report)
    write_json(SUITE_DIR / f"root_cause_{report.run_id}.json", data)
    return json_path, md_path, causes_csv, obs


def attach_root_cause_to_opportunity(opportunity: Any, *, symbol: str = "BTC/USDT", timeframe: str = "4h") -> RootCauseReport:
    report = run_root_cause_discovery(symbol=symbol, timeframe=timeframe)
    raw = getattr(opportunity, "raw", None)
    if raw is None:
        raw = {}
        setattr(opportunity, "raw", raw)
    raw.update({
        "root_cause_primary": report.primary_root_cause,
        "root_cause_direction": report.root_cause_direction,
        "root_cause_confidence": report.root_cause_confidence,
        "root_cause_probability_pct": report.root_cause_probability_pct,
        "root_cause_evidence_quality": report.root_cause_evidence_quality,
        "root_cause_verdict": report.root_cause_verdict,
        "root_cause_evidence_total": report.evidence_total,
        "root_cause_official_evidence_total": report.official_evidence_total,
        "root_cause_top_causes": ";".join([f"{c.get('cause')}:{c.get('probability_pct')}%" for c in report.top_causes[:5]]),
        "root_cause_summary": report.root_cause_summary,
    })
    return report
