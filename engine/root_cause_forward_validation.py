"""
Freakto v8.1.0 - Root Cause Forward Validation

Research-only validation layer for the Root Cause Discovery Engine.

It asks a simple but important question:
When Freakto labels a probable root cause (for example MACRO_POLICY_PRESSURE
with BEARISH direction), did the next candles move in the same direction?

This module never creates Paper/Live trades and never sends orders. It only
reads decision_evaluations.csv and writes validation artifacts.
"""
from __future__ import annotations

import csv
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from engine.research_utils import LOG_DIR, RESEARCH_DIR, run_id, safe_float, safe_int, utc_now_iso, write_json, write_text, save_dataframe_csv, read_csv_df

VERSION = "v8.1.0"
ROOT_CAUSE_DIR = LOG_DIR / "root_cause"
SUITE_DIR = RESEARCH_DIR / "v6_suite"
EVALUATIONS_FILE = LOG_DIR / "decision_evaluations.csv"
ROOT_CAUSE_OBSERVATIONS_FILE = ROOT_CAUSE_DIR / "root_cause_observations.csv"
ROOT_CAUSE_FORWARD_OBSERVATIONS_FILE = ROOT_CAUSE_DIR / "root_cause_forward_validation_observations.csv"

HORIZONS = {
    "4h": "market_return_after_4h_pct",
    "12h": "market_return_after_12h_pct",
    "24h": "market_return_after_24h_pct",
}
LEGACY_HORIZONS = {
    "4h": "return_after_4h_pct",
    "12h": "return_after_12h_pct",
    "24h": "return_after_24h_pct",
}
DIRECTION_SIGN = {"BULLISH": 1, "BEARISH": -1}


@dataclass
class RootCauseForwardRow:
    decision_id: str
    candle_timestamp: str
    symbol: str
    timeframe: str
    side: str
    root_cause_primary: str
    root_cause_direction: str
    root_cause_probability_pct: float
    root_cause_confidence: str
    root_cause_evidence_quality: str
    root_cause_verdict: str
    evaluation_status: str
    return_after_4h_pct: Optional[float] = None
    return_after_12h_pct: Optional[float] = None
    return_after_24h_pct: Optional[float] = None
    signed_return_after_4h_pct: Optional[float] = None
    signed_return_after_12h_pct: Optional[float] = None
    signed_return_after_24h_pct: Optional[float] = None
    direction_correct_4h: Optional[bool] = None
    direction_correct_12h: Optional[bool] = None
    direction_correct_24h: Optional[bool] = None


@dataclass
class RootCauseForwardAggregate:
    root_cause_primary: str
    root_cause_direction: str
    samples_total: int
    evidence_quality_mode: str
    confidence_mode: str
    avg_probability_pct: float
    samples_4h: int
    hit_rate_4h: float
    avg_signed_return_4h_pct: float
    median_signed_return_4h_pct: float
    samples_12h: int
    hit_rate_12h: float
    avg_signed_return_12h_pct: float
    median_signed_return_12h_pct: float
    samples_24h: int
    hit_rate_24h: float
    avg_signed_return_24h_pct: float
    median_signed_return_24h_pct: float
    validation_score: float
    verdict: str


@dataclass
class RootCauseForwardValidationReport:
    run_id: str
    generated_utc: str
    version: str
    status: str
    horizon: str
    min_samples: int
    min_abs_return_pct: float
    evaluations_file: str
    evaluation_rows: int
    root_cause_rows: int
    evaluated_cells: int
    complete_rows: int
    eligible_causes: int
    research_candidates: int
    promising_low_sample: int
    top_validated_causes: List[Dict[str, Any]] = field(default_factory=list)
    validation_rows: List[Dict[str, Any]] = field(default_factory=list)
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


def _mode(values: List[str], default: str = "") -> str:
    cleaned = [_upper(v) for v in values if _upper(v)]
    if not cleaned:
        return default
    counts: Dict[str, int] = {}
    for v in cleaned:
        counts[v] = counts.get(v, 0) + 1
    return sorted(counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)[0][0]


def _mean(values: List[float]) -> float:
    clean = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    return round(sum(clean) / len(clean), 4) if clean else 0.0


def _median(values: List[float]) -> float:
    clean = sorted([float(v) for v in values if v is not None and not math.isnan(float(v))])
    if not clean:
        return 0.0
    mid = len(clean) // 2
    if len(clean) % 2:
        return round(clean[mid], 4)
    return round((clean[mid - 1] + clean[mid]) / 2, 4)


def _pct(n: int, d: int) -> float:
    return round((n / d) * 100.0, 2) if d else 0.0


def _to_float(value: Any) -> Optional[float]:
    val = safe_float(value, None)
    return val


def _get_market_return(row: Dict[str, Any], horizon: str) -> Tuple[Optional[float], bool]:
    """Return actual market move if available.

    v8.1 decision_evaluator writes market_return_after_* columns. Older logs do
    not have them. For NEUTRAL decisions the legacy return_after_* was raw
    market return, so it is safe. For LONG/SHORT older rows are side-adjusted;
    those are returned with legacy=True so the report can warn.
    """
    col = HORIZONS[horizon]
    val = _to_float(row.get(col))
    if val is not None:
        return val, False
    legacy_col = LEGACY_HORIZONS[horizon]
    legacy_val = _to_float(row.get(legacy_col))
    if legacy_val is None:
        return None, False
    side = _upper(row.get("side"), "NEUTRAL")
    if side == "NEUTRAL":
        return legacy_val, False
    return legacy_val, True


def _direction_correct(direction: str, market_return: Optional[float], min_abs_return_pct: float) -> Optional[bool]:
    sign = DIRECTION_SIGN.get(_upper(direction))
    if sign is None or market_return is None:
        return None
    if abs(float(market_return)) < min_abs_return_pct:
        return None
    return bool(float(market_return) * sign > 0)


def _signed_return(direction: str, market_return: Optional[float]) -> Optional[float]:
    sign = DIRECTION_SIGN.get(_upper(direction))
    if sign is None or market_return is None:
        return None
    return round(float(market_return) * sign, 4)


def _prepare_rows(df: pd.DataFrame, min_abs_return_pct: float) -> Tuple[List[RootCauseForwardRow], List[str]]:
    rows: List[RootCauseForwardRow] = []
    warnings: List[str] = []
    legacy_side_adjusted_count = 0
    if df is None or df.empty:
        return rows, warnings
    for _, item in df.iterrows():
        raw = item.to_dict()
        cause = _upper(raw.get("root_cause_primary"), "")
        direction = _upper(raw.get("root_cause_direction"), "")
        if not cause or cause in {"UNKNOWN", "UNKNOWN_OR_INSUFFICIENT_EVIDENCE"}:
            continue
        if direction not in DIRECTION_SIGN:
            continue
        market_returns: Dict[str, Optional[float]] = {}
        signed: Dict[str, Optional[float]] = {}
        correct: Dict[str, Optional[bool]] = {}
        for h in HORIZONS:
            r, legacy = _get_market_return(raw, h)
            if legacy:
                legacy_side_adjusted_count += 1
            market_returns[h] = r
            signed[h] = _signed_return(direction, r)
            correct[h] = _direction_correct(direction, r, min_abs_return_pct)
        if all(v is None for v in market_returns.values()):
            continue
        rows.append(RootCauseForwardRow(
            decision_id=_norm(raw.get("decision_id")),
            candle_timestamp=_norm(raw.get("candle_timestamp")),
            symbol=_norm(raw.get("symbol"), "UNKNOWN"),
            timeframe=_norm(raw.get("timeframe"), ""),
            side=_upper(raw.get("side"), "NEUTRAL"),
            root_cause_primary=cause,
            root_cause_direction=direction,
            root_cause_probability_pct=round(safe_float(raw.get("root_cause_probability_pct"), 0.0) or 0.0, 4),
            root_cause_confidence=_upper(raw.get("root_cause_confidence"), ""),
            root_cause_evidence_quality=_upper(raw.get("root_cause_evidence_quality"), ""),
            root_cause_verdict=_upper(raw.get("root_cause_verdict"), ""),
            evaluation_status=_upper(raw.get("evaluation_status"), ""),
            return_after_4h_pct=market_returns["4h"],
            return_after_12h_pct=market_returns["12h"],
            return_after_24h_pct=market_returns["24h"],
            signed_return_after_4h_pct=signed["4h"],
            signed_return_after_12h_pct=signed["12h"],
            signed_return_after_24h_pct=signed["24h"],
            direction_correct_4h=correct["4h"],
            direction_correct_12h=correct["12h"],
            direction_correct_24h=correct["24h"],
        ))
    if legacy_side_adjusted_count:
        warnings.append(
            "برخی ردیف‌های قدیمی market_return_after_* ندارند؛ برای LONG/SHORT ممکن است return قدیمی side-adjusted باشد. از این نسخه به بعد decision_evaluator ستون raw market return می‌سازد."
        )
    return rows, warnings


def _aggregate(rows: List[RootCauseForwardRow], min_samples: int) -> List[RootCauseForwardAggregate]:
    groups: Dict[Tuple[str, str], List[RootCauseForwardRow]] = {}
    for r in rows:
        groups.setdefault((r.root_cause_primary, r.root_cause_direction), []).append(r)
    aggs: List[RootCauseForwardAggregate] = []
    for (cause, direction), items in groups.items():
        horizon_stats: Dict[str, Dict[str, Any]] = {}
        score_parts: List[float] = []
        for h in HORIZONS:
            signed_vals = [getattr(r, f"signed_return_after_{h}_pct") for r in items]
            signed_vals = [v for v in signed_vals if v is not None]
            correct_vals = [getattr(r, f"direction_correct_{h}") for r in items]
            correct_vals = [v for v in correct_vals if v is not None]
            samples = len(correct_vals)
            hit = _pct(sum(1 for v in correct_vals if v is True), samples)
            avg = _mean(signed_vals)
            med = _median(signed_vals)
            horizon_stats[h] = {"samples": samples, "hit": hit, "avg": avg, "med": med}
            if samples:
                score_parts.append((hit - 50.0) * 0.35 + avg * 8.0 + min(10.0, samples / max(min_samples, 1) * 10.0))
        validation_score = round(sum(score_parts) / len(score_parts), 4) if score_parts else 0.0
        primary_h = horizon_stats.get("24h") or horizon_stats.get("12h") or horizon_stats.get("4h")
        max_samples = max(horizon_stats[h]["samples"] for h in HORIZONS)
        avg_hit = _mean([horizon_stats[h]["hit"] for h in HORIZONS if horizon_stats[h]["samples"]])
        avg_signed = _mean([horizon_stats[h]["avg"] for h in HORIZONS if horizon_stats[h]["samples"]])
        if max_samples < min_samples:
            if avg_hit >= 58 and avg_signed > 0:
                verdict = "FORWARD_PROMISING_LOW_SAMPLE"
            else:
                verdict = "LOW_SAMPLE"
        elif avg_hit >= 58 and avg_signed > 0:
            verdict = "ROOT_CAUSE_FORWARD_RESEARCH_CANDIDATE"
        elif avg_hit >= 52 and avg_signed >= 0:
            verdict = "MIXED_BUT_POSITIVE_FORWARD_EDGE"
        else:
            verdict = "WEAK_OR_NEGATIVE_FORWARD_EVIDENCE"
        aggs.append(RootCauseForwardAggregate(
            root_cause_primary=cause,
            root_cause_direction=direction,
            samples_total=len(items),
            evidence_quality_mode=_mode([r.root_cause_evidence_quality for r in items], "UNKNOWN"),
            confidence_mode=_mode([r.root_cause_confidence for r in items], "UNKNOWN"),
            avg_probability_pct=_mean([r.root_cause_probability_pct for r in items]),
            samples_4h=horizon_stats["4h"]["samples"],
            hit_rate_4h=horizon_stats["4h"]["hit"],
            avg_signed_return_4h_pct=horizon_stats["4h"]["avg"],
            median_signed_return_4h_pct=horizon_stats["4h"]["med"],
            samples_12h=horizon_stats["12h"]["samples"],
            hit_rate_12h=horizon_stats["12h"]["hit"],
            avg_signed_return_12h_pct=horizon_stats["12h"]["avg"],
            median_signed_return_12h_pct=horizon_stats["12h"]["med"],
            samples_24h=horizon_stats["24h"]["samples"],
            hit_rate_24h=horizon_stats["24h"]["hit"],
            avg_signed_return_24h_pct=horizon_stats["24h"]["avg"],
            median_signed_return_24h_pct=horizon_stats["24h"]["med"],
            validation_score=validation_score,
            verdict=verdict,
        ))
    return sorted(aggs, key=lambda a: (a.verdict == "ROOT_CAUSE_FORWARD_RESEARCH_CANDIDATE", a.validation_score, a.samples_total), reverse=True)


def run_root_cause_forward_validation(*, horizon: str = "24h", min_samples: int = 10, min_abs_return_pct: float = 0.0) -> RootCauseForwardValidationReport:
    rid = run_id("root_cause_forward")
    blockers: List[str] = []
    warnings: List[str] = [
        "Root Cause Forward Validation فقط رابطه علت‌های پژوهشی با outcome بعدی را می‌سنجد؛ سیگنال خرید/فروش نیست.",
        "این validation باید چند هفته/ماه sample جمع کند تا قابل اتکا شود.",
    ]
    recommendations: List[str] = [
        "ابتدا decision_evaluator.py را اجرا کن تا market_return_after_* برای تصمیم‌ها ساخته شود.",
        "Root Causeهایی که hit-rate پایدار و sample کافی دارند بعداً می‌توانند وارد Root-Cause Gate Simulator شوند.",
        "تا قبل از sample کافی، نتیجه فقط Research/Shadow بماند و Paper/Live فعال نشود.",
    ]
    df = read_csv_df(EVALUATIONS_FILE)
    if df.empty:
        blockers.append("logs/decision_evaluations.csv پیدا نشد یا خالی است؛ اول decision_evaluator.py را اجرا کن.")
        return RootCauseForwardValidationReport(
            run_id=rid, generated_utc=utc_now_iso(), version=VERSION, status="NO_FORWARD_EVALUATIONS",
            horizon=horizon, min_samples=min_samples, min_abs_return_pct=min_abs_return_pct,
            evaluations_file=str(EVALUATIONS_FILE), evaluation_rows=0, root_cause_rows=0, evaluated_cells=0,
            complete_rows=0, eligible_causes=0, research_candidates=0, promising_low_sample=0,
            blockers=blockers, warnings=warnings, recommendations=recommendations,
        )
    rows, prep_warnings = _prepare_rows(df, min_abs_return_pct=min_abs_return_pct)
    warnings.extend(prep_warnings)
    aggs = _aggregate(rows, min_samples=min_samples)
    evaluated_cells = 0
    for r in rows:
        for h in HORIZONS:
            if getattr(r, f"direction_correct_{h}") is not None:
                evaluated_cells += 1
    complete_rows = 0
    if "evaluation_status" in df.columns:
        complete_rows = int((df["evaluation_status"].fillna("").astype(str).str.upper() == "COMPLETE").sum())
    candidates = sum(1 for a in aggs if a.verdict == "ROOT_CAUSE_FORWARD_RESEARCH_CANDIDATE")
    promising = sum(1 for a in aggs if a.verdict == "FORWARD_PROMISING_LOW_SAMPLE")
    if not rows:
        status = "NO_ROOT_CAUSE_ROWS_EVALUATED"
        blockers.append("هیچ ردیف decision_evaluations با root_cause_primary/root_cause_direction قابل ارزیابی پیدا نشد.")
    elif candidates:
        status = "ROOT_CAUSE_FORWARD_CANDIDATES_FOUND"
    elif promising:
        status = "ROOT_CAUSE_FORWARD_PROMISING_LOW_SAMPLE"
    elif evaluated_cells < min_samples:
        status = "ROOT_CAUSE_FORWARD_LOW_SAMPLE"
        blockers.append(f"تعداد سلول‌های ارزیابی‌شده کمتر از حداقل sample است: {evaluated_cells}/{min_samples}")
    else:
        status = "ROOT_CAUSE_FORWARD_MIXED_OR_WEAK"
    return RootCauseForwardValidationReport(
        run_id=rid,
        generated_utc=utc_now_iso(),
        version=VERSION,
        status=status,
        horizon=horizon,
        min_samples=min_samples,
        min_abs_return_pct=min_abs_return_pct,
        evaluations_file=str(EVALUATIONS_FILE),
        evaluation_rows=int(len(df)),
        root_cause_rows=len(rows),
        evaluated_cells=evaluated_cells,
        complete_rows=complete_rows,
        eligible_causes=len(aggs),
        research_candidates=candidates,
        promising_low_sample=promising,
        top_validated_causes=[asdict(a) for a in aggs[:20]],
        validation_rows=[asdict(r) for r in rows],
        blockers=blockers,
        warnings=warnings,
        recommendations=recommendations,
    )


def format_root_cause_forward_console(report: RootCauseForwardValidationReport, compact: bool = True) -> str:
    sep = "=" * 110
    lines = [sep, f"🧪 Freakto Root Cause Forward Validation {VERSION}", sep]
    lines.append(f"Status                 : {report.status}")
    lines.append(f"Run ID                 : {report.run_id}")
    lines.append(f"Evaluations File       : {report.evaluations_file}")
    lines.append(f"Rows / Complete        : {report.evaluation_rows} / {report.complete_rows}")
    lines.append(f"Root Cause Rows        : {report.root_cause_rows}")
    lines.append(f"Evaluated Cells        : {report.evaluated_cells}")
    lines.append(f"Eligible Causes        : {report.eligible_causes}")
    lines.append(f"Research Candidates    : {report.research_candidates}")
    lines.append(f"Promising Low Sample   : {report.promising_low_sample}")
    lines.append(f"Min Samples / Deadzone : {report.min_samples} / {report.min_abs_return_pct}%")
    if report.top_validated_causes:
        lines.append("\nTop Root-Cause Forward Results:")
        for c in report.top_validated_causes[:10]:
            lines.append(
                f"- {c.get('root_cause_primary')} | {c.get('root_cause_direction')} | "
                f"n24={c.get('samples_24h')} hit24={c.get('hit_rate_24h')}% avg24={c.get('avg_signed_return_24h_pct')}% | "
                f"n12={c.get('samples_12h')} hit12={c.get('hit_rate_12h')}% | "
                f"score={c.get('validation_score')} | {c.get('verdict')}"
            )
    if not compact and report.validation_rows:
        lines.append("\nRecent Validation Rows:")
        for r in report.validation_rows[-10:]:
            lines.append(
                f"- {r.get('decision_id')} | {r.get('root_cause_primary')} {r.get('root_cause_direction')} | "
                f"4h={r.get('return_after_4h_pct')} correct={r.get('direction_correct_4h')} | "
                f"12h={r.get('return_after_12h_pct')} correct={r.get('direction_correct_12h')} | "
                f"24h={r.get('return_after_24h_pct')} correct={r.get('direction_correct_24h')}"
            )
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


def _append_observation(report: RootCauseForwardValidationReport) -> Path:
    ROOT_CAUSE_DIR.mkdir(parents=True, exist_ok=True)
    best = report.top_validated_causes[0] if report.top_validated_causes else {}
    row = {
        "run_id": report.run_id,
        "generated_utc": report.generated_utc,
        "version": report.version,
        "status": report.status,
        "evaluation_rows": report.evaluation_rows,
        "root_cause_rows": report.root_cause_rows,
        "evaluated_cells": report.evaluated_cells,
        "eligible_causes": report.eligible_causes,
        "research_candidates": report.research_candidates,
        "promising_low_sample": report.promising_low_sample,
        "top_cause": best.get("root_cause_primary", ""),
        "top_direction": best.get("root_cause_direction", ""),
        "top_hit_rate_24h": best.get("hit_rate_24h", ""),
        "top_avg_signed_return_24h_pct": best.get("avg_signed_return_24h_pct", ""),
        "top_verdict": best.get("verdict", ""),
    }
    exists = ROOT_CAUSE_FORWARD_OBSERVATIONS_FILE.exists() and ROOT_CAUSE_FORWARD_OBSERVATIONS_FILE.stat().st_size > 0
    with ROOT_CAUSE_FORWARD_OBSERVATIONS_FILE.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    return ROOT_CAUSE_FORWARD_OBSERVATIONS_FILE


def save_root_cause_forward_report(report: RootCauseForwardValidationReport) -> Tuple[Path, Path, Path, Path, Path]:
    ROOT_CAUSE_DIR.mkdir(parents=True, exist_ok=True)
    SUITE_DIR.mkdir(parents=True, exist_ok=True)
    data = asdict(report)
    json_path = ROOT_CAUSE_DIR / f"root_cause_forward_validation_{report.run_id}.json"
    md_path = ROOT_CAUSE_DIR / f"root_cause_forward_validation_report_{report.run_id}.md"
    causes_csv = ROOT_CAUSE_DIR / f"root_cause_forward_summary_{report.run_id}.csv"
    rows_csv = ROOT_CAUSE_DIR / f"root_cause_forward_rows_{report.run_id}.csv"
    write_json(json_path, data)
    write_text(md_path, format_root_cause_forward_console(report, compact=False))
    save_dataframe_csv(causes_csv, pd.DataFrame(report.top_validated_causes))
    save_dataframe_csv(rows_csv, pd.DataFrame(report.validation_rows))
    obs = _append_observation(report)
    write_json(SUITE_DIR / f"root_cause_forward_validation_{report.run_id}.json", data)
    return json_path, md_path, causes_csv, rows_csv, obs
