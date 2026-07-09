"""
engine/forward_regime_labeling.py

Freakto v6.2.1 - Forward Regime Label Injection Patch

Purpose:
- Make sure every new Forward decision log carries a usable regime context.
- Backfill/repair legacy decisions.csv rows that were recorded before regime
  fields were consistently logged.
- Propagate regime context into decision_evaluations.csv so readiness metrics,
  regime matrix, and Regime Shadow Gates can measure known-regime samples.

Safety:
This module never creates trades and never sends orders. It only enriches local
research logs with decision-time metadata. It never uses return/target/stop/MFE
outcomes to infer a regime label.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from engine.csv_utils import read_csv_dicts_lenient, rewrite_csv_with_header

VERSION = "v6.2.1"
LOG_DIR = Path("logs")
DECISIONS_FILE = LOG_DIR / "decisions.csv"
EVALUATIONS_FILE = LOG_DIR / "decision_evaluations.csv"
RESEARCH_DIR = LOG_DIR / "research" / "v6_suite"

KNOWN_REGIMES = {"TRENDING_BULL", "TRENDING_BEAR", "SIDEWAYS", "VOLATILE", "QUIET"}
UNKNOWN_VALUES = {"", "UNKNOWN", "NAN", "NONE", "NULL", "نامشخص"}
REGIME_AUX_COLUMNS = [
    "regime_label",
    "regime_confidence",
    "regime_adjustment",
    "regime_source",
    "regime_label_quality",
    "trend_state",
    "volatility_state",
    "market_phase",
]


@dataclass
class RegimeInference:
    label: str
    confidence: int
    adjustment: int
    source: str
    quality: str
    trend_state: str
    volatility_state: str
    market_phase: str
    reasons: List[str] = field(default_factory=list)


@dataclass
class ForwardRegimeLabelReport:
    run_id: str
    generated_utc: str
    status: str
    apply_changes: bool
    decisions_path: str
    evaluations_path: str
    decision_rows: int
    known_before: int
    unknown_before: int
    known_after: int
    unknown_after: int
    injected_decision_rows: int
    preserved_decision_rows: int
    direct_engine_rows: int
    text_inferred_rows: int
    proxy_inferred_rows: int
    evaluation_rows: int
    patched_evaluation_rows: int
    evaluation_known_after: int
    label_counts: Dict[str, int]
    evaluation_label_counts: Dict[str, int]
    backup_paths: List[str]
    blockers: List[str]
    recommendations: List[str]
    warnings: List[str]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_run_id() -> str:
    return "forward_regime_label_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _norm_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return text


def _norm_label(value: object) -> str:
    text = _norm_text(value).upper().replace("-", "_").replace(" ", "_")
    if text in UNKNOWN_VALUES:
        return "UNKNOWN"
    # Older/regression labels sometimes used broad states.
    aliases = {
        "BULL": "TRENDING_BULL",
        "BULLISH": "TRENDING_BULL",
        "BEAR": "TRENDING_BEAR",
        "BEARISH": "TRENDING_BEAR",
        "TRENDING": "TRENDING_BULL",
        "RANGING": "SIDEWAYS",
        "RANGE": "SIDEWAYS",
        "CHOP": "SIDEWAYS",
        "CHOPPY": "SIDEWAYS",
        "HIGH_VOL": "VOLATILE",
        "LOW_VOL": "QUIET",
    }
    text = aliases.get(text, text)
    return text if text in KNOWN_REGIMES else "UNKNOWN"


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        text = _norm_text(value).replace(",", "")
        if not text:
            return default
        return float(text)
    except Exception:
        return default


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(round(_safe_float(value, float(default))))
    except Exception:
        return default


def _risk_norm(value: object) -> str:
    text = _norm_text(value).lower().replace("_", " ").replace("-", " ")
    if not text:
        return "UNKNOWN"
    if "medium" in text or "متوسط" in text or "مدیوم" in text:
        return "MEDIUM"
    if "high" in text or "زیاد" in text or "بالا" in text:
        return "HIGH"
    if "low" in text or "کم" in text or "پایین" in text or "conservative" in text:
        return "LOW"
    return text.upper()


def _trend_state(label: str, row: Optional[dict] = None) -> str:
    if label == "TRENDING_BULL":
        return "BULLISH"
    if label == "TRENDING_BEAR":
        return "BEARISH"
    if label == "SIDEWAYS":
        return "SIDEWAYS"
    if label == "VOLATILE":
        return "VOLATILE"
    if label == "QUIET":
        return "QUIET"
    row = row or {}
    side = _norm_text(row.get("side")).upper()
    trend_score = _safe_float(row.get("trend_score"), 0)
    long_score = _safe_float(row.get("long_score"), 0)
    short_score = _safe_float(row.get("short_score"), 0)
    if side == "LONG" and (trend_score >= 15 or long_score > short_score):
        return "BULLISH_PROXY"
    if side == "SHORT" and (trend_score >= 15 or short_score > long_score):
        return "BEARISH_PROXY"
    return "UNKNOWN"


def _volatility_state(label: str, risk_label: object = "") -> str:
    if label == "VOLATILE":
        return "HIGH_VOL"
    if label == "QUIET":
        return "LOW_VOL"
    risk = _risk_norm(risk_label)
    if risk == "HIGH":
        return "ELEVATED_RISK_VOL"
    if risk == "LOW":
        return "NORMAL_OR_LOW_VOL"
    return "NORMAL_VOL"


def _market_phase(trend_state: str, volatility_state: str) -> str:
    if trend_state == "UNKNOWN" and volatility_state == "NORMAL_VOL":
        return "UNKNOWN"
    return f"{trend_state}__{volatility_state}"


def infer_regime_for_decision(row: dict) -> RegimeInference:
    """Infer missing regime using only decision-time fields.

    Priority:
    1) Existing engine-provided regime_label.
    2) Regime text already present in reasons/warnings.
    3) Conservative proxy from side/component scores.

    No outcome fields are read here.
    """
    existing = _norm_label(row.get("regime_label"))
    existing_conf = _safe_int(row.get("regime_confidence"), 0)
    if existing != "UNKNOWN":
        conf = existing_conf if existing_conf > 0 else 75
        trend = _trend_state(existing, row)
        vol = _volatility_state(existing, row.get("risk_label"))
        return RegimeInference(
            label=existing,
            confidence=conf,
            adjustment=_safe_int(row.get("regime_adjustment"), 0),
            source=_norm_text(row.get("regime_source")) or "decision_engine_raw",
            quality=_norm_text(row.get("regime_label_quality")) or "DIRECT_ENGINE",
            trend_state=_norm_text(row.get("trend_state")) or trend,
            volatility_state=_norm_text(row.get("volatility_state")) or vol,
            market_phase=_norm_text(row.get("market_phase")) or _market_phase(trend, vol),
            reasons=["regime_label already existed on decision row"],
        )

    text_blob = " ".join([
        _norm_text(row.get("reasons")),
        _norm_text(row.get("warnings")),
        _norm_text(row.get("regime_reasons")),
        _norm_text(row.get("regime_warnings")),
    ]).lower()
    text_rules = [
        ("TRENDING_BEAR", ["trending_bear", "bear", "bearish", "نزولی", "شورت را تأیید", "bias شورت"]),
        ("TRENDING_BULL", ["trending_bull", "bull", "bullish", "صعودی", "لانگ را تأیید", "bias لانگ"]),
        ("SIDEWAYS", ["sideways", "range", "ranging", "رنج", "خنثی"]),
        ("VOLATILE", ["volatile", "high volatility", "پرنوسان", "نوسان شدید"]),
        ("QUIET", ["quiet", "low volatility", "کم‌نوسان", "نوسان پایین"]),
    ]
    for label, needles in text_rules:
        if any(n.lower() in text_blob for n in needles):
            trend = _trend_state(label, row)
            vol = _volatility_state(label, row.get("risk_label"))
            return RegimeInference(
                label=label,
                confidence=55,
                adjustment=5 if label in {"TRENDING_BULL", "TRENDING_BEAR"} else (-5 if label == "SIDEWAYS" else (-4 if label == "VOLATILE" else -2)),
                source="decision_text_inference",
                quality="TEXT_INFERRED",
                trend_state=trend,
                volatility_state=vol,
                market_phase=_market_phase(trend, vol),
                reasons=["inferred from decision reasons/warnings text"],
            )

    side = _norm_text(row.get("side")).upper()
    trend_score = _safe_float(row.get("trend_score"), 0)
    structure_score = _safe_float(row.get("structure_score"), 0)
    long_score = _safe_float(row.get("long_score"), 0)
    short_score = _safe_float(row.get("short_score"), 0)
    momentum_score = _safe_float(row.get("momentum_score"), 0)
    score = _safe_float(row.get("score"), 0)
    risk = _risk_norm(row.get("risk_label"))
    diff = long_score - short_score

    # Conservative proxy: only label a trending regime when side and component
    # evidence point in the same direction. It is better to leave UNKNOWN than
    # to create false regime certainty.
    if side == "SHORT" and (short_score >= 55 or diff <= -8 or (trend_score >= 15 and structure_score >= 8)):
        label = "TRENDING_BEAR"
        conf = 45 if score >= 60 else 35
        trend = _trend_state(label, row)
        vol = _volatility_state(label, row.get("risk_label"))
        return RegimeInference(label, conf, 5, "decision_feature_proxy", "LOW_CONF_PROXY", trend, vol, _market_phase(trend, vol), ["proxy from SHORT side and component scores"])
    if side == "LONG" and (long_score >= 55 or diff >= 8 or (trend_score >= 15 and structure_score >= 8)):
        label = "TRENDING_BULL"
        conf = 45 if score >= 60 else 35
        trend = _trend_state(label, row)
        vol = _volatility_state(label, row.get("risk_label"))
        return RegimeInference(label, conf, 5, "decision_feature_proxy", "LOW_CONF_PROXY", trend, vol, _market_phase(trend, vol), ["proxy from LONG side and component scores"])
    if trend_score <= 5 and momentum_score <= 5 and structure_score <= 5 and side in {"LONG", "SHORT", "NEUTRAL"}:
        label = "SIDEWAYS"
        trend = _trend_state(label, row)
        vol = _volatility_state(label, row.get("risk_label"))
        return RegimeInference(label, 30, -5, "decision_feature_proxy", "LOW_CONF_PROXY", trend, vol, _market_phase(trend, vol), ["proxy from weak trend/momentum/structure scores"])
    if risk == "HIGH" and side == "NEUTRAL":
        label = "VOLATILE"
        trend = _trend_state(label, row)
        vol = _volatility_state(label, row.get("risk_label"))
        return RegimeInference(label, 30, -4, "decision_feature_proxy", "LOW_CONF_PROXY", trend, vol, _market_phase(trend, vol), ["proxy from high risk neutral decision"])

    trend = _trend_state("UNKNOWN", row)
    vol = _volatility_state("UNKNOWN", row.get("risk_label"))
    return RegimeInference("UNKNOWN", 0, 0, "unresolved", "UNKNOWN", trend, vol, _market_phase(trend, vol), ["not enough decision-time evidence for regime"])


def metadata_for_existing_label(label: object, risk_label: object = "") -> Dict[str, str]:
    norm = _norm_label(label)
    trend = _trend_state(norm)
    vol = _volatility_state(norm, risk_label)
    return {
        "regime_label": norm,
        "trend_state": trend,
        "volatility_state": vol,
        "market_phase": _market_phase(trend, vol),
    }


def _header_with_columns(old_header: List[str], required: List[str]) -> List[str]:
    merged = list(old_header)
    for col in required:
        if col not in merged:
            merged.append(col)
    return merged


def _label_counts(rows: List[dict], col: str = "regime_label") -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        label = _norm_label(row.get(col))
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _known_unknown(rows: List[dict], col: str = "regime_label") -> Tuple[int, int]:
    known = 0
    unknown = 0
    for row in rows:
        label = _norm_label(row.get(col))
        if label == "UNKNOWN":
            unknown += 1
        else:
            known += 1
    return known, unknown


def _copy_regime_to_evaluations(eval_rows: List[dict], decision_rows: List[dict]) -> Tuple[List[dict], int]:
    if not eval_rows or not decision_rows:
        return eval_rows, 0
    by_id = {_norm_text(r.get("decision_id")): r for r in decision_rows if _norm_text(r.get("decision_id"))}
    patched = 0
    for row in eval_rows:
        did = _norm_text(row.get("decision_id"))
        source = by_id.get(did)
        if not source:
            continue
        before = {col: _norm_text(row.get(col)) for col in REGIME_AUX_COLUMNS}
        for col in REGIME_AUX_COLUMNS:
            val = _norm_text(source.get(col))
            current = _norm_text(row.get(col))
            should_copy = False
            if val:
                if col == "regime_label":
                    should_copy = (not current) or (_norm_label(current) == "UNKNOWN")
                else:
                    should_copy = not current
            if should_copy:
                row[col] = val
        after = {col: _norm_text(row.get(col)) for col in REGIME_AUX_COLUMNS}
        if after != before:
            patched += 1
    return eval_rows, patched


def run_forward_regime_labeling(*, apply_changes: bool = True) -> ForwardRegimeLabelReport:
    run = make_run_id()
    generated = utc_now_iso()
    backups: List[str] = []
    blockers: List[str] = []
    recommendations: List[str] = []
    warnings: List[str] = [
        "Regime injection فقط از داده‌های لحظه تصمیم استفاده می‌کند؛ outcome/return/target/stop استفاده نمی‌شود.",
        "برچسب‌های LOW_CONF_PROXY برای Research هستند و باید در Forward واقعی بیشتر validate شوند.",
    ]

    if not DECISIONS_FILE.exists():
        return ForwardRegimeLabelReport(
            run_id=run,
            generated_utc=generated,
            status="NO_FORWARD_DECISIONS_LOG",
            apply_changes=apply_changes,
            decisions_path=str(DECISIONS_FILE),
            evaluations_path=str(EVALUATIONS_FILE),
            decision_rows=0,
            known_before=0,
            unknown_before=0,
            known_after=0,
            unknown_after=0,
            injected_decision_rows=0,
            preserved_decision_rows=0,
            direct_engine_rows=0,
            text_inferred_rows=0,
            proxy_inferred_rows=0,
            evaluation_rows=0,
            patched_evaluation_rows=0,
            evaluation_known_after=0,
            label_counts={},
            evaluation_label_counts={},
            backup_paths=[],
            blockers=[f"فایل decisions.csv پیدا نشد: {DECISIONS_FILE}"],
            recommendations=["ابتدا monitor.py --once یا forward_test_dashboard.py --cycle را اجرا کن."],
            warnings=warnings,
        )

    old_header, rows = read_csv_dicts_lenient(DECISIONS_FILE)
    rows = [dict(r) for r in rows]
    known_before, unknown_before = _known_unknown(rows)

    injected = preserved = direct = text_inf = proxy_inf = 0
    for row in rows:
        before_label = _norm_label(row.get("regime_label"))
        inference = infer_regime_for_decision(row)
        if before_label != "UNKNOWN":
            preserved += 1
        elif inference.label != "UNKNOWN":
            injected += 1
        if inference.quality == "DIRECT_ENGINE":
            direct += 1
        elif inference.quality == "TEXT_INFERRED":
            text_inf += 1
        elif inference.quality == "LOW_CONF_PROXY":
            proxy_inf += 1

        row["regime_label"] = inference.label
        row["regime_confidence"] = str(inference.confidence)
        row["regime_adjustment"] = str(inference.adjustment)
        row["regime_source"] = inference.source
        row["regime_label_quality"] = inference.quality
        row["trend_state"] = inference.trend_state
        row["volatility_state"] = inference.volatility_state
        row["market_phase"] = inference.market_phase

    known_after, unknown_after = _known_unknown(rows)
    label_counts = _label_counts(rows)

    eval_rows: List[dict] = []
    eval_header: List[str] = []
    patched_evals = 0
    eval_known_after = 0
    eval_counts: Dict[str, int] = {}
    if EVALUATIONS_FILE.exists():
        eval_header, eval_rows = read_csv_dicts_lenient(EVALUATIONS_FILE)
        eval_rows = [dict(r) for r in eval_rows]
        eval_rows, patched_evals = _copy_regime_to_evaluations(eval_rows, rows)
        eval_known_after, _ = _known_unknown(eval_rows)
        eval_counts = _label_counts(eval_rows)

    if apply_changes:
        DECISIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        backup = DECISIONS_FILE.with_suffix(f".csv.bak_v621_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}")
        backup.write_bytes(DECISIONS_FILE.read_bytes())
        backups.append(str(backup))
        new_header = _header_with_columns(old_header, REGIME_AUX_COLUMNS)
        rewrite_csv_with_header(DECISIONS_FILE, new_header, rows)

        if EVALUATIONS_FILE.exists() and eval_rows:
            ebackup = EVALUATIONS_FILE.with_suffix(f".csv.bak_v621_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}")
            ebackup.write_bytes(EVALUATIONS_FILE.read_bytes())
            backups.append(str(ebackup))
            new_eheader = _header_with_columns(eval_header, REGIME_AUX_COLUMNS)
            rewrite_csv_with_header(EVALUATIONS_FILE, new_eheader, eval_rows)

    status = "FORWARD_REGIME_LABELING_READY"
    if known_after < 30:
        status = "FORWARD_REGIME_LABELING_BUILDING"
        blockers.append(f"Known Forward regime rows هنوز کمتر از 30 است: {known_after}")
    if unknown_after > 0:
        recommendations.append(f"هنوز {unknown_after} تصمیم Forward بدون regime قابل‌اعتماد مانده؛ اجرای‌های جدید بعد از v6.2.1 باید این عدد را کاهش دهد.")
    if injected > 0:
        recommendations.append(f"{injected} ردیف legacy با regime proxy/text پر شد؛ برای تصمیم نهایی فقط DIRECT_ENGINE و Forward جدید را جدی‌تر بگیر.")
    recommendations.append("بعد از اجرای cycle جدید، regime_shadow_gate_dashboard.py --compact را دوباره بررسی کن.")

    return ForwardRegimeLabelReport(
        run_id=run,
        generated_utc=generated,
        status=status,
        apply_changes=apply_changes,
        decisions_path=str(DECISIONS_FILE),
        evaluations_path=str(EVALUATIONS_FILE),
        decision_rows=len(rows),
        known_before=known_before,
        unknown_before=unknown_before,
        known_after=known_after,
        unknown_after=unknown_after,
        injected_decision_rows=injected,
        preserved_decision_rows=preserved,
        direct_engine_rows=direct,
        text_inferred_rows=text_inf,
        proxy_inferred_rows=proxy_inf,
        evaluation_rows=len(eval_rows),
        patched_evaluation_rows=patched_evals,
        evaluation_known_after=eval_known_after,
        label_counts=label_counts,
        evaluation_label_counts=eval_counts,
        backup_paths=backups,
        blockers=blockers,
        recommendations=recommendations,
        warnings=warnings,
    )


def format_forward_regime_label_console(report: ForwardRegimeLabelReport, *, compact: bool = False) -> str:
    sep = "=" * 110
    lines = [sep, f"🧬 Freakto Forward Regime Label Injection Patch {VERSION}", sep]
    lines.extend([
        f"Status                 : {report.status}",
        f"Run ID                 : {report.run_id}",
        f"Apply Changes          : {report.apply_changes}",
        f"Decision Rows          : {report.decision_rows}",
        f"Known Before / After   : {report.known_before} / {report.known_after}",
        f"Unknown Before / After : {report.unknown_before} / {report.unknown_after}",
        f"Injected Decision Rows : {report.injected_decision_rows}",
        f"Preserved Direct Rows  : {report.preserved_decision_rows}",
        f"Direct/Text/Proxy      : {report.direct_engine_rows} / {report.text_inferred_rows} / {report.proxy_inferred_rows}",
        f"Evaluation Rows        : {report.evaluation_rows}",
        f"Patched Evaluations    : {report.patched_evaluation_rows}",
        f"Eval Known After       : {report.evaluation_known_after}",
    ])
    if report.label_counts:
        lines.append("\nDecision Regime Counts:")
        for label, count in list(report.label_counts.items())[:10]:
            lines.append(f"- {label}: {count}")
    if not compact and report.evaluation_label_counts:
        lines.append("\nEvaluation Regime Counts:")
        for label, count in list(report.evaluation_label_counts.items())[:10]:
            lines.append(f"- {label}: {count}")
    if report.backup_paths and not compact:
        lines.append("\nBackups:")
        for path in report.backup_paths:
            lines.append(f"- {path}")
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


def save_forward_regime_labeling(report: ForwardRegimeLabelReport) -> Tuple[Path, Path]:
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    json_path = RESEARCH_DIR / f"forward_regime_labeling_{report.run_id}.json"
    md_path = RESEARCH_DIR / f"forward_regime_labeling_report_{report.run_id}.md"
    json_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(format_forward_regime_label_console(report, compact=False), encoding="utf-8")
    return json_path, md_path
