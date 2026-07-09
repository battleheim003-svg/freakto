"""
Freakto v7.1.0 - Narrative/Decision Conflict Scoring

Research-only layer that compares the current market narrative with the
Decision Engine bias. It does not create Paper/Live trades and never sends
orders. The output is a *decision context adjustment* used for logging,
forward research, and dashboards.
"""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

from engine.research_utils import LOG_DIR, RESEARCH_DIR, run_id, safe_float, safe_int, utc_now_iso, write_json, write_text, save_dataframe_csv

VERSION = "v7.1.0"
NARRATIVE_DECISION_DIR = LOG_DIR / "narrative"
SUITE_DIR = RESEARCH_DIR / "v6_suite"
DECISIONS_FILE = LOG_DIR / "decisions.csv"
NARRATIVE_OBSERVATIONS_CSV = NARRATIVE_DECISION_DIR / "market_narrative_observations.csv"
NARRATIVE_DECISION_OBSERVATIONS_CSV = NARRATIVE_DECISION_DIR / "narrative_decision_observations.csv"


@dataclass
class NarrativeDecisionConflictReport:
    run_id: str
    generated_utc: str
    version: str
    status: str
    symbol: str
    timeframe: str
    decision_id: str
    decision_side: str
    decision_score: int
    decision_actionability: str
    narrative_label: str
    narrative_direction: str
    narrative_confidence: str
    narrative_theme: str
    narrative_score: float
    narrative_event_risk: str
    narrative_technical_conflict: str
    narrative_alignment: str
    narrative_conflict_score: int
    narrative_adjustment: int
    narrative_adjusted_score: int
    narrative_action_override: str
    narrative_decision_verdict: str
    narrative_notes: str
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    latest_narrative: Dict[str, Any] = field(default_factory=dict)
    latest_decision: Dict[str, Any] = field(default_factory=dict)


def _norm(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return default
    return text


def _upper(value: Any, default: str = "") -> str:
    return _norm(value, default).upper().replace("-", "_").replace(" ", "_")


def _clamp_int(value: float, low: int = 0, high: int = 100) -> int:
    try:
        return max(low, min(high, int(round(float(value)))))
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


def _decision_direction(side: str) -> str:
    s = _upper(side, "NEUTRAL")
    if s == "LONG":
        return "BULLISH"
    if s == "SHORT":
        return "BEARISH"
    return "NEUTRAL"


def _narrative_direction(value: str) -> str:
    d = _upper(value, "MIXED_OR_NEUTRAL")
    if d in {"BULLISH", "BEARISH"}:
        return d
    return "MIXED_OR_NEUTRAL"


def _severity_weight(value: str, *, high: int, medium: int, low: int = 0) -> int:
    v = _upper(value, "LOW")
    if v == "HIGH":
        return high
    if v == "MEDIUM":
        return medium
    return low


def _extract_narrative_from_report(report: Any = None) -> Dict[str, Any]:
    if report is None:
        row = _latest_row(NARRATIVE_OBSERVATIONS_CSV)
        if row:
            return row
        try:
            from engine.market_narrative import run_market_narrative
            generated = run_market_narrative()
            return asdict(generated)
        except Exception:
            return {}
    if isinstance(report, dict):
        return report
    try:
        return asdict(report)
    except Exception:
        return dict(getattr(report, "__dict__", {}) or {})


def _narrative_fields(narrative: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "label": _upper(narrative.get("narrative_label"), "NO_CLEAR_MARKET_NARRATIVE"),
        "direction": _narrative_direction(narrative.get("dominant_direction") or narrative.get("narrative_direction")),
        "confidence": _upper(narrative.get("narrative_confidence"), "LOW"),
        "theme": _upper(narrative.get("dominant_theme") or narrative.get("narrative_theme"), "NO_THEME"),
        "score": safe_float(narrative.get("net_direction_score") or narrative.get("narrative_score"), 0.0) or 0.0,
        "event_risk": _upper(narrative.get("event_risk") or narrative.get("narrative_event_risk"), "LOW"),
        "technical_conflict": _upper(narrative.get("technical_event_conflict") or narrative.get("narrative_technical_conflict"), "LOW"),
        "status": _upper(narrative.get("status"), "UNKNOWN"),
    }


def score_narrative_decision_conflict(
    *,
    decision_side: str,
    decision_score: Any = 0,
    decision_actionability: str = "",
    symbol: str = "BTC/USDT",
    timeframe: str = "4h",
    decision_id: str = "",
    narrative: Optional[Dict[str, Any]] = None,
    latest_decision: Optional[Dict[str, Any]] = None,
) -> NarrativeDecisionConflictReport:
    """Score how supportive or conflicting the narrative is for a decision.

    This is intentionally conservative. A supportive narrative can only add a
    small research boost, while conflicting/high-risk narratives can downgrade
    strongly. It never changes orders, paper trades, or live execution.
    """
    rid = run_id("narrative_decision")
    generated = utc_now_iso()
    latest_decision = latest_decision or {}
    narrative = narrative or {}
    nf = _narrative_fields(narrative)

    side_u = _upper(decision_side, "NEUTRAL")
    decision_dir = _decision_direction(side_u)
    base_score = _clamp_int(safe_float(decision_score, 0) or 0)
    narrative_dir = nf["direction"]

    blockers: List[str] = []
    warnings = [
        "Narrative/Decision Conflict Scoring فقط research-level است و هیچ Paper/Live فعال نمی‌کند.",
        "این امتیاز نباید به‌تنهایی باعث ورود شود؛ فقط برای کاهش/افزایش احتیاط در Forward Research است.",
    ]
    recommendations = [
        "اگر conflict بالا باشد، تصمیم فقط Watchlist/Research بماند تا Forward outcome تأیید شود.",
        "برای ارتقا به Gate، narrative_adjustment باید با outcomeهای بعدی در decision_evaluations.csv validate شود.",
    ]

    if not narrative:
        blockers.append("هیچ market narrative قابل استفاده‌ای پیدا نشد؛ market_narrative_dashboard.py --compact را قبل از این مرحله اجرا کن.")
    if side_u not in {"LONG", "SHORT", "NEUTRAL"}:
        side_u = "NEUTRAL"
        decision_dir = "NEUTRAL"

    # Alignment state.
    if decision_dir == "NEUTRAL":
        alignment = "CONTEXT_ONLY"
    elif narrative_dir == "MIXED_OR_NEUTRAL":
        alignment = "MIXED_OR_NEUTRAL_NARRATIVE"
    elif decision_dir == narrative_dir:
        alignment = "ALIGNED"
    else:
        alignment = "CONFLICTING"

    conflict = 0
    adjustment = 0
    notes: List[str] = []

    label = nf["label"]
    if alignment == "CONTEXT_ONLY":
        conflict = 0
        adjustment = 0
        notes.append("Decision neutral است؛ narrative فقط context پژوهشی است.")
    elif alignment == "ALIGNED":
        conflict = 10
        boost = 5 if nf["confidence"] == "HIGH" else 3 if nf["confidence"] == "MEDIUM" else 1
        adjustment += boost
        notes.append("Narrative با جهت تصمیم هم‌جهت است؛ فقط boost کوچک research-level داده شد.")
    elif alignment == "CONFLICTING":
        conflict = 62
        adjustment -= 14
        notes.append("Narrative با جهت تصمیم در تضاد است؛ confidence باید کاهش یابد.")
    else:
        conflict = 38
        adjustment -= 4
        notes.append("Narrative جهت روشن ندارد یا mixed است؛ تصمیم باید محتاط‌تر تفسیر شود.")

    if "MIXED" in label or "CONFLICT" in label:
        conflict = max(conflict, 52)
        adjustment -= 7
        notes.append("خود narrative برچسب conflict/mixed دارد.")
    if nf["event_risk"] == "HIGH":
        conflict += 10 if alignment != "ALIGNED" else 5
        adjustment -= 5
        notes.append("Event risk بالاست؛ حتی narrative هم‌جهت هم باید با احتیاط دیده شود.")
    elif nf["event_risk"] == "MEDIUM":
        conflict += 4
        adjustment -= 2
    if nf["technical_conflict"] == "HIGH":
        conflict += 14
        adjustment -= 10
        notes.append("Causal/technical conflict بالاست.")
    elif nf["technical_conflict"] == "MEDIUM":
        conflict += 7
        adjustment -= 4
    if nf["confidence"] == "HIGH" and alignment == "CONFLICTING":
        conflict += 8
        adjustment -= 5
        notes.append("تضاد با narrative پر confidence رخ داده است.")
    if abs(float(nf["score"])) < 6 and alignment != "CONTEXT_ONLY":
        adjustment -= 2
        notes.append("قدرت net narrative پایین است؛ حمایت روایی ضعیف است.")

    conflict = _clamp_int(conflict)
    adjustment = max(-35, min(10, int(adjustment)))
    adjusted = _clamp_int(base_score + adjustment)

    if blockers:
        status = "NARRATIVE_DECISION_CONTEXT_MISSING"
        verdict = "NARRATIVE_CONTEXT_NOT_AVAILABLE"
        override = "NO_OVERRIDE"
    elif alignment == "CONTEXT_ONLY":
        status = "NARRATIVE_CONTEXT_ONLY"
        verdict = "NEUTRAL_DECISION_CONTEXT_ONLY"
        override = "NO_OVERRIDE"
    elif conflict >= 75:
        status = "NARRATIVE_DECISION_HIGH_CONFLICT"
        verdict = "HIGH_CONFLICT_WATCHLIST_ONLY"
        override = "WATCHLIST_ONLY_RESEARCH"
    elif conflict >= 55:
        status = "NARRATIVE_DECISION_CONFLICT"
        verdict = "DOWNGRADE_CONFIDENCE_RESEARCH_ONLY"
        override = "DOWNGRADE_OR_WAIT"
    elif alignment == "ALIGNED" and adjusted >= base_score:
        status = "NARRATIVE_DECISION_ALIGNED"
        verdict = "NARRATIVE_SUPPORTS_DECISION_RESEARCH_ONLY"
        override = "NO_OVERRIDE_SUPPORTIVE_CONTEXT"
    else:
        status = "NARRATIVE_DECISION_CAUTION"
        verdict = "CAUTION_RESEARCH_ONLY"
        override = "NO_OVERRIDE_CAUTION"

    if _upper(decision_actionability) in {"NOT_ACTIONABLE", "WATCHLIST", "NEUTRAL"} and override.startswith("NO_OVERRIDE"):
        notes.append("Decision Engine خودش actionability را پایین نگه داشته؛ narrative فقط context اضافه می‌کند.")

    return NarrativeDecisionConflictReport(
        run_id=rid,
        generated_utc=generated,
        version=VERSION,
        status=status,
        symbol=symbol,
        timeframe=timeframe,
        decision_id=decision_id,
        decision_side=side_u,
        decision_score=base_score,
        decision_actionability=_norm(decision_actionability),
        narrative_label=nf["label"],
        narrative_direction=narrative_dir,
        narrative_confidence=nf["confidence"],
        narrative_theme=nf["theme"],
        narrative_score=round(float(nf["score"]), 4),
        narrative_event_risk=nf["event_risk"],
        narrative_technical_conflict=nf["technical_conflict"],
        narrative_alignment=alignment,
        narrative_conflict_score=conflict,
        narrative_adjustment=adjustment,
        narrative_adjusted_score=adjusted,
        narrative_action_override=override,
        narrative_decision_verdict=verdict,
        narrative_notes=" | ".join(notes[:8]),
        blockers=blockers,
        warnings=warnings,
        recommendations=recommendations,
        latest_narrative=narrative,
        latest_decision=latest_decision,
    )


def attach_narrative_decision_conflict_to_opportunity(opportunity: Any, narrative_report: Any = None, *, symbol: str = "BTC/USDT", timeframe: str = "4h") -> NarrativeDecisionConflictReport:
    raw = getattr(opportunity, "raw", None)
    if raw is None:
        raw = {}
        setattr(opportunity, "raw", raw)
    narrative = _extract_narrative_from_report(narrative_report)
    report = score_narrative_decision_conflict(
        decision_side=getattr(opportunity, "side", raw.get("side", "NEUTRAL")),
        decision_score=getattr(opportunity, "score", raw.get("score", 0)),
        decision_actionability=getattr(opportunity, "actionability_label", raw.get("actionability", "")),
        symbol=getattr(opportunity, "symbol", symbol),
        timeframe=getattr(opportunity, "timeframe", timeframe),
        decision_id=raw.get("decision_id", ""),
        narrative=narrative,
    )
    raw.update({
        "narrative_alignment": report.narrative_alignment,
        "narrative_conflict_score": report.narrative_conflict_score,
        "narrative_adjustment": report.narrative_adjustment,
        "narrative_adjusted_score": report.narrative_adjusted_score,
        "narrative_action_override": report.narrative_action_override,
        "narrative_decision_verdict": report.narrative_decision_verdict,
        "narrative_decision_notes": report.narrative_notes,
    })
    return report


def run_latest_decision_narrative_conflict(*, symbol: str = "BTC/USDT", timeframe: str = "4h") -> NarrativeDecisionConflictReport:
    latest_decision = _latest_row(DECISIONS_FILE)
    narrative = _extract_narrative_from_report(None)
    if not latest_decision:
        return score_narrative_decision_conflict(
            decision_side="NEUTRAL",
            decision_score=0,
            decision_actionability="",
            symbol=symbol,
            timeframe=timeframe,
            decision_id="",
            narrative=narrative,
            latest_decision={},
        )
    return score_narrative_decision_conflict(
        decision_side=latest_decision.get("side", "NEUTRAL"),
        decision_score=latest_decision.get("score", 0),
        decision_actionability=latest_decision.get("actionability") or latest_decision.get("actionability_label", ""),
        symbol=latest_decision.get("symbol", symbol),
        timeframe=latest_decision.get("timeframe", timeframe),
        decision_id=latest_decision.get("decision_id", ""),
        narrative=narrative,
        latest_decision=latest_decision,
    )


def format_narrative_decision_console(report: NarrativeDecisionConflictReport, compact: bool = True) -> str:
    sep = "=" * 110
    lines = [sep, f"🧭 Freakto Narrative/Decision Conflict Scoring {VERSION}", sep]
    lines.append(f"Status                 : {report.status}")
    lines.append(f"Run ID                 : {report.run_id}")
    lines.append(f"Symbol / TF            : {report.symbol} | {report.timeframe}")
    lines.append(f"Decision ID            : {report.decision_id or '---'}")
    lines.append(f"Decision Side/Score    : {report.decision_side} | {report.decision_score}")
    lines.append(f"Decision Actionability : {report.decision_actionability or '---'}")
    lines.append("")
    lines.append("Narrative Context:")
    lines.append(f"- Label                : {report.narrative_label}")
    lines.append(f"- Direction            : {report.narrative_direction}")
    lines.append(f"- Confidence           : {report.narrative_confidence}")
    lines.append(f"- Theme                : {report.narrative_theme}")
    lines.append(f"- Narrative Score      : {report.narrative_score}")
    lines.append(f"- Event Risk           : {report.narrative_event_risk}")
    lines.append(f"- Tech/Event Conflict  : {report.narrative_technical_conflict}")
    lines.append("")
    lines.append("Decision Impact:")
    lines.append(f"- Alignment            : {report.narrative_alignment}")
    lines.append(f"- Conflict Score       : {report.narrative_conflict_score}/100")
    lines.append(f"- Score Adjustment     : {report.narrative_adjustment}")
    lines.append(f"- Adjusted Score       : {report.narrative_adjusted_score}/100")
    lines.append(f"- Action Override      : {report.narrative_action_override}")
    lines.append(f"- Verdict              : {report.narrative_decision_verdict}")
    lines.append(f"- Notes                : {report.narrative_notes}")
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


def _append_observation(report: NarrativeDecisionConflictReport) -> Path:
    NARRATIVE_DECISION_DIR.mkdir(parents=True, exist_ok=True)
    row = {
        "run_id": report.run_id,
        "generated_utc": report.generated_utc,
        "version": report.version,
        "status": report.status,
        "symbol": report.symbol,
        "timeframe": report.timeframe,
        "decision_id": report.decision_id,
        "decision_side": report.decision_side,
        "decision_score": report.decision_score,
        "narrative_label": report.narrative_label,
        "narrative_direction": report.narrative_direction,
        "narrative_confidence": report.narrative_confidence,
        "narrative_theme": report.narrative_theme,
        "narrative_score": report.narrative_score,
        "narrative_event_risk": report.narrative_event_risk,
        "narrative_alignment": report.narrative_alignment,
        "narrative_conflict_score": report.narrative_conflict_score,
        "narrative_adjustment": report.narrative_adjustment,
        "narrative_adjusted_score": report.narrative_adjusted_score,
        "narrative_action_override": report.narrative_action_override,
        "narrative_decision_verdict": report.narrative_decision_verdict,
    }
    exists = NARRATIVE_DECISION_OBSERVATIONS_CSV.exists() and NARRATIVE_DECISION_OBSERVATIONS_CSV.stat().st_size > 0
    with NARRATIVE_DECISION_OBSERVATIONS_CSV.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    return NARRATIVE_DECISION_OBSERVATIONS_CSV


def save_narrative_decision_report(report: NarrativeDecisionConflictReport) -> Tuple[Path, Path, Path]:
    NARRATIVE_DECISION_DIR.mkdir(parents=True, exist_ok=True)
    SUITE_DIR.mkdir(parents=True, exist_ok=True)
    data = asdict(report)
    json_path = NARRATIVE_DECISION_DIR / f"narrative_decision_{report.run_id}.json"
    md_path = NARRATIVE_DECISION_DIR / f"narrative_decision_report_{report.run_id}.md"
    write_json(json_path, data)
    write_text(md_path, format_narrative_decision_console(report, compact=False))
    obs = _append_observation(report)
    write_json(SUITE_DIR / f"narrative_decision_{report.run_id}.json", data)
    return json_path, md_path, obs
