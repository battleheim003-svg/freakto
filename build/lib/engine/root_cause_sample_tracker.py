"""
Freakto v8.2.0 - Root Cause Sample Accumulator & Maturity Tracker

Research-only tracker that answers:
- How many evaluated Root Cause samples do we have?
- Which Root Cause classes are approaching validation readiness?
- How many more forward decisions are needed before any gate/research promotion?

This module never creates Paper/Live trades and never sends orders.
"""
from __future__ import annotations

import csv
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from engine.research_utils import LOG_DIR, RESEARCH_DIR, run_id, safe_float, utc_now_iso, write_json, write_text, save_dataframe_csv, read_csv_df
from engine.root_cause_forward_validation import run_root_cause_forward_validation

VERSION = "v8.2.0"
ROOT_CAUSE_DIR = LOG_DIR / "root_cause"
SUITE_DIR = RESEARCH_DIR / "v6_suite"
EVALUATIONS_FILE = LOG_DIR / "decision_evaluations.csv"
SAMPLE_OBSERVATIONS_FILE = ROOT_CAUSE_DIR / "root_cause_sample_tracker_observations.csv"

HORIZONS = ["4h", "12h", "24h"]
CORRECT_COLUMNS = {
    "4h": "root_cause_direction_correct_after_4h",
    "12h": "root_cause_direction_correct_after_12h",
    "24h": "root_cause_direction_correct_after_24h",
}
SIGNED_RETURN_COLUMNS = {
    "4h": "root_cause_signed_return_after_4h_pct",
    "12h": "root_cause_signed_return_after_12h_pct",
    "24h": "root_cause_signed_return_after_24h_pct",
}


@dataclass
class RootCauseSampleBucket:
    root_cause_primary: str
    root_cause_direction: str
    decision_rows: int
    evaluated_cells: int
    samples_4h: int
    hit_rate_4h: float
    avg_signed_return_4h_pct: float
    samples_12h: int
    hit_rate_12h: float
    avg_signed_return_12h_pct: float
    samples_24h: int
    hit_rate_24h: float
    avg_signed_return_24h_pct: float
    avg_probability_pct: float
    evidence_quality_mode: str
    confidence_mode: str
    maturity_level: str
    sample_gap_to_min: int
    sample_gap_to_research: int
    sample_gap_to_candidate: int
    provisional_verdict: str


@dataclass
class RootCauseSampleTrackerReport:
    run_id: str
    generated_utc: str
    version: str
    status: str
    evaluations_file: str
    evaluation_rows: int
    complete_rows: int
    root_cause_rows: int
    evaluated_cells: int
    unique_root_causes: int
    min_cells: int
    research_cells: int
    candidate_cells: int
    estimated_more_root_cause_decisions_for_min: int
    estimated_more_root_cause_decisions_for_research: int
    estimated_more_root_cause_decisions_for_candidate: int
    validation_status: str
    validation_candidates: int
    validation_promising_low_sample: int
    buckets: List[Dict[str, Any]] = field(default_factory=list)
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


def _to_bool(value: Any) -> Optional[bool]:
    text = _norm(value).lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


def _mean(values: List[float]) -> float:
    clean = []
    for v in values:
        try:
            f = float(v)
            if not math.isnan(f):
                clean.append(f)
        except Exception:
            pass
    return round(sum(clean) / len(clean), 4) if clean else 0.0


def _pct(n: int, d: int) -> float:
    return round((n / d) * 100.0, 2) if d else 0.0


def _mode(values: List[str], default: str = "UNKNOWN") -> str:
    clean = [_upper(v) for v in values if _upper(v)]
    if not clean:
        return default
    counts: Dict[str, int] = {}
    for v in clean:
        counts[v] = counts.get(v, 0) + 1
    return sorted(counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)[0][0]


def _root_cause_mask(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty or "root_cause_primary" not in df.columns or "root_cause_direction" not in df.columns:
        return pd.Series([], dtype=bool)
    cause = df["root_cause_primary"].fillna("").astype(str).str.strip().str.upper()
    direction = df["root_cause_direction"].fillna("").astype(str).str.strip().str.upper()
    return (cause != "") & (~cause.isin(["NAN", "NONE", "NULL", "UNKNOWN", "UNKNOWN_OR_INSUFFICIENT_EVIDENCE"])) & direction.isin(["BULLISH", "BEARISH"])


def _horizon_stats(df: pd.DataFrame, horizon: str) -> Tuple[int, float, float]:
    c_col = CORRECT_COLUMNS[horizon]
    r_col = SIGNED_RETURN_COLUMNS[horizon]
    if c_col not in df.columns:
        return 0, 0.0, 0.0
    correct_values = [_to_bool(v) for v in df[c_col].tolist()]
    valid = [v for v in correct_values if v is not None]
    n = len(valid)
    hit = _pct(sum(1 for v in valid if v), n)
    returns = []
    if r_col in df.columns:
        for v in df[r_col].tolist():
            f = safe_float(v, None)
            if f is not None:
                returns.append(float(f))
    return n, hit, _mean(returns)


def _count_evaluated_cells(df: pd.DataFrame) -> int:
    total = 0
    for h in HORIZONS:
        col = CORRECT_COLUMNS[h]
        if col in df.columns:
            total += sum(1 for v in df[col].tolist() if _to_bool(v) is not None)
    return int(total)


def _build_bucket(cause: str, direction: str, df: pd.DataFrame, *, min_cells: int, research_cells: int, candidate_cells: int) -> RootCauseSampleBucket:
    s4, h4, a4 = _horizon_stats(df, "4h")
    s12, h12, a12 = _horizon_stats(df, "12h")
    s24, h24, a24 = _horizon_stats(df, "24h")
    cells = s4 + s12 + s24
    prob_values = []
    if "root_cause_probability_pct" in df.columns:
        for v in df["root_cause_probability_pct"].tolist():
            f = safe_float(v, None)
            if f is not None:
                prob_values.append(float(f))
    q_mode = _mode(df.get("root_cause_evidence_quality", pd.Series(dtype=str)).tolist(), "UNKNOWN")
    c_mode = _mode(df.get("root_cause_confidence", pd.Series(dtype=str)).tolist(), "UNKNOWN")
    if cells >= candidate_cells:
        maturity = "CANDIDATE_SAMPLE_READY"
    elif cells >= research_cells:
        maturity = "RESEARCH_SAMPLE_READY"
    elif cells >= min_cells:
        maturity = "MIN_SAMPLE_READY"
    elif cells > 0:
        maturity = "LOW_SAMPLE_ACCUMULATING"
    else:
        maturity = "NO_EVALUATED_CELLS"

    # Conservative provisional verdict; real promotion still belongs to
    # root_cause_forward_validation after enough samples.
    if cells < min_cells:
        verdict = "LOW_SAMPLE_KEEP_COLLECTING"
    elif s24 >= min_cells and h24 >= 55 and a24 > 0:
        verdict = "PROMISING_RESEARCH_WATCHLIST"
    elif s24 >= min_cells and (h24 < 45 or a24 < 0):
        verdict = "WEAK_OR_NEGATIVE_PROVISIONAL"
    else:
        verdict = "MIXED_PROVISIONAL"

    return RootCauseSampleBucket(
        root_cause_primary=cause,
        root_cause_direction=direction,
        decision_rows=int(len(df)),
        evaluated_cells=cells,
        samples_4h=s4,
        hit_rate_4h=h4,
        avg_signed_return_4h_pct=a4,
        samples_12h=s12,
        hit_rate_12h=h12,
        avg_signed_return_12h_pct=a12,
        samples_24h=s24,
        hit_rate_24h=h24,
        avg_signed_return_24h_pct=a24,
        avg_probability_pct=_mean(prob_values),
        evidence_quality_mode=q_mode,
        confidence_mode=c_mode,
        maturity_level=maturity,
        sample_gap_to_min=max(0, min_cells - cells),
        sample_gap_to_research=max(0, research_cells - cells),
        sample_gap_to_candidate=max(0, candidate_cells - cells),
        provisional_verdict=verdict,
    )


def run_root_cause_sample_tracker(*, min_cells: int = 10, research_cells: int = 30, candidate_cells: int = 90) -> RootCauseSampleTrackerReport:
    rid = run_id("root_cause_samples")
    warnings = [
        "Root Cause Sample Tracker فقط بلوغ نمونه‌ها را می‌سنجد؛ Paper/Live فعال نمی‌کند.",
        "Promotion واقعی فقط بعد از Forward validation پایدار و sample کافی مجاز است.",
    ]
    recommendations = [
        "چرخه Forward را هر 4 ساعت یا با GitHub Actions اجرا کن تا Root Cause rows بیشتر شود.",
        "پس از هر root_cause_dashboard.py، decision_evaluator.py و سپس root_cause_forward_validation_dashboard.py را اجرا کن.",
        "تا وقتی حداقل 30-50 تصمیم دارای Root Cause جمع نشده، نتیجه فقط Research/Shadow بماند.",
    ]
    blockers: List[str] = []
    df = read_csv_df(EVALUATIONS_FILE)
    if df.empty:
        blockers.append("logs/decision_evaluations.csv موجود نیست یا خالی است؛ ابتدا decision_evaluator.py را اجرا کن.")
        validation = run_root_cause_forward_validation(min_samples=min_cells)
        return RootCauseSampleTrackerReport(
            run_id=rid,
            generated_utc=utc_now_iso(),
            version=VERSION,
            status="NO_DECISION_EVALUATIONS",
            evaluations_file=str(EVALUATIONS_FILE),
            evaluation_rows=0,
            complete_rows=0,
            root_cause_rows=0,
            evaluated_cells=0,
            unique_root_causes=0,
            min_cells=min_cells,
            research_cells=research_cells,
            candidate_cells=candidate_cells,
            estimated_more_root_cause_decisions_for_min=max(0, math.ceil(min_cells / 3)),
            estimated_more_root_cause_decisions_for_research=max(0, math.ceil(research_cells / 3)),
            estimated_more_root_cause_decisions_for_candidate=max(0, math.ceil(candidate_cells / 3)),
            validation_status=validation.status,
            validation_candidates=validation.research_candidates,
            validation_promising_low_sample=validation.promising_low_sample,
            blockers=blockers,
            warnings=warnings,
            recommendations=recommendations,
        )

    complete_rows = int((df.get("evaluation_status", pd.Series(dtype=str)).fillna("").astype(str).str.upper() == "COMPLETE").sum()) if "evaluation_status" in df.columns else int(len(df))
    mask = _root_cause_mask(df)
    rc = df[mask].copy() if len(mask) else pd.DataFrame()
    evaluated_cells = _count_evaluated_cells(rc) if not rc.empty else 0
    grouped: List[RootCauseSampleBucket] = []
    if not rc.empty:
        rc["_cause"] = rc["root_cause_primary"].map(_upper)
        rc["_direction"] = rc["root_cause_direction"].map(_upper)
        for (cause, direction), g in rc.groupby(["_cause", "_direction"]):
            grouped.append(_build_bucket(cause, direction, g, min_cells=min_cells, research_cells=research_cells, candidate_cells=candidate_cells))
    grouped = sorted(grouped, key=lambda b: (b.evaluated_cells, b.samples_24h, b.avg_signed_return_24h_pct), reverse=True)

    validation = run_root_cause_forward_validation(min_samples=min_cells)
    if not rc.empty and evaluated_cells < min_cells:
        status = "ROOT_CAUSE_SAMPLE_COLLECTION_ACTIVE_LOW_SAMPLE"
        blockers.append(f"Root Cause evaluated cells کمتر از حداقل است: {evaluated_cells}/{min_cells}")
    elif validation.research_candidates:
        status = "ROOT_CAUSE_VALIDATION_RESEARCH_CANDIDATES_FOUND"
    elif validation.promising_low_sample:
        status = "ROOT_CAUSE_PROMISING_LOW_SAMPLE_TRACKING"
    elif evaluated_cells >= candidate_cells:
        status = "ROOT_CAUSE_SAMPLE_TARGET_REACHED_MIXED"
    elif evaluated_cells >= research_cells:
        status = "ROOT_CAUSE_RESEARCH_SAMPLE_READY"
    elif evaluated_cells >= min_cells:
        status = "ROOT_CAUSE_MIN_SAMPLE_READY"
    else:
        status = "NO_ROOT_CAUSE_SAMPLES_YET"
        blockers.append("هنوز هیچ Root Cause row قابل ارزیابی وجود ندارد.")

    remaining_min = max(0, min_cells - evaluated_cells)
    remaining_research = max(0, research_cells - evaluated_cells)
    remaining_candidate = max(0, candidate_cells - evaluated_cells)
    # One new COMPLETE root-cause decision can add up to 3 evaluated cells.
    est_min = math.ceil(remaining_min / 3) if remaining_min else 0
    est_research = math.ceil(remaining_research / 3) if remaining_research else 0
    est_candidate = math.ceil(remaining_candidate / 3) if remaining_candidate else 0

    return RootCauseSampleTrackerReport(
        run_id=rid,
        generated_utc=utc_now_iso(),
        version=VERSION,
        status=status,
        evaluations_file=str(EVALUATIONS_FILE),
        evaluation_rows=int(len(df)),
        complete_rows=complete_rows,
        root_cause_rows=int(len(rc)),
        evaluated_cells=evaluated_cells,
        unique_root_causes=len(grouped),
        min_cells=min_cells,
        research_cells=research_cells,
        candidate_cells=candidate_cells,
        estimated_more_root_cause_decisions_for_min=est_min,
        estimated_more_root_cause_decisions_for_research=est_research,
        estimated_more_root_cause_decisions_for_candidate=est_candidate,
        validation_status=validation.status,
        validation_candidates=validation.research_candidates,
        validation_promising_low_sample=validation.promising_low_sample,
        buckets=[asdict(b) for b in grouped],
        blockers=blockers,
        warnings=warnings,
        recommendations=recommendations,
    )


def format_root_cause_sample_console(report: RootCauseSampleTrackerReport, compact: bool = True) -> str:
    sep = "=" * 110
    lines = [sep, f"🧫 Freakto Root Cause Sample Accumulator {VERSION}", sep]
    lines.append(f"Status                 : {report.status}")
    lines.append(f"Run ID                 : {report.run_id}")
    lines.append(f"Evaluations File       : {report.evaluations_file}")
    lines.append(f"Rows / Complete        : {report.evaluation_rows} / {report.complete_rows}")
    lines.append(f"Root Cause Rows        : {report.root_cause_rows}")
    lines.append(f"Evaluated Cells        : {report.evaluated_cells}")
    lines.append(f"Unique Root Causes     : {report.unique_root_causes}")
    lines.append(f"Validation Status      : {report.validation_status}")
    lines.append(f"Candidates / Promising : {report.validation_candidates} / {report.validation_promising_low_sample}")
    lines.append(f"Min/Research/Candidate : {report.min_cells} / {report.research_cells} / {report.candidate_cells} cells")
    lines.append(f"More decisions needed  : min={report.estimated_more_root_cause_decisions_for_min} | research={report.estimated_more_root_cause_decisions_for_research} | candidate={report.estimated_more_root_cause_decisions_for_candidate}")
    if report.buckets:
        lines.append("\nRoot Cause Buckets:")
        for b in report.buckets[:10]:
            lines.append(
                f"- {b.get('root_cause_primary')} | {b.get('root_cause_direction')} | "
                f"rows={b.get('decision_rows')} cells={b.get('evaluated_cells')} | "
                f"n24={b.get('samples_24h')} hit24={b.get('hit_rate_24h')}% avg24={b.get('avg_signed_return_24h_pct')}% | "
                f"maturity={b.get('maturity_level')} | {b.get('provisional_verdict')}"
            )
    if not compact and report.buckets:
        lines.append("\nSample Gaps:")
        for b in report.buckets[:10]:
            lines.append(
                f"- {b.get('root_cause_primary')}: gap_min={b.get('sample_gap_to_min')} | "
                f"gap_research={b.get('sample_gap_to_research')} | gap_candidate={b.get('sample_gap_to_candidate')}"
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


def _append_observation(report: RootCauseSampleTrackerReport) -> Path:
    ROOT_CAUSE_DIR.mkdir(parents=True, exist_ok=True)
    best = report.buckets[0] if report.buckets else {}
    row = {
        "run_id": report.run_id,
        "generated_utc": report.generated_utc,
        "version": report.version,
        "status": report.status,
        "evaluation_rows": report.evaluation_rows,
        "complete_rows": report.complete_rows,
        "root_cause_rows": report.root_cause_rows,
        "evaluated_cells": report.evaluated_cells,
        "unique_root_causes": report.unique_root_causes,
        "validation_status": report.validation_status,
        "top_cause": best.get("root_cause_primary", ""),
        "top_direction": best.get("root_cause_direction", ""),
        "top_cells": best.get("evaluated_cells", ""),
        "top_hit_rate_24h": best.get("hit_rate_24h", ""),
        "top_avg_signed_return_24h_pct": best.get("avg_signed_return_24h_pct", ""),
        "top_maturity": best.get("maturity_level", ""),
        "more_decisions_for_research": report.estimated_more_root_cause_decisions_for_research,
    }
    exists = SAMPLE_OBSERVATIONS_FILE.exists() and SAMPLE_OBSERVATIONS_FILE.stat().st_size > 0
    with SAMPLE_OBSERVATIONS_FILE.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    return SAMPLE_OBSERVATIONS_FILE


def save_root_cause_sample_report(report: RootCauseSampleTrackerReport):
    ROOT_CAUSE_DIR.mkdir(parents=True, exist_ok=True)
    SUITE_DIR.mkdir(parents=True, exist_ok=True)
    data = asdict(report)
    json_path = ROOT_CAUSE_DIR / f"root_cause_sample_tracker_{report.run_id}.json"
    md_path = ROOT_CAUSE_DIR / f"root_cause_sample_tracker_report_{report.run_id}.md"
    buckets_csv = ROOT_CAUSE_DIR / f"root_cause_sample_buckets_{report.run_id}.csv"
    write_json(json_path, data)
    write_text(md_path, format_root_cause_sample_console(report, compact=False))
    save_dataframe_csv(buckets_csv, pd.DataFrame(report.buckets))
    obs = _append_observation(report)
    write_json(SUITE_DIR / f"root_cause_sample_tracker_{report.run_id}.json", data)
    return json_path, md_path, buckets_csv, obs
