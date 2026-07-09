"""
Freakto v9.0.0 - Evidence Graph Engine

Research-only graph layer that connects event/narrative/root-cause/decision
metadata to forward outcomes. It does NOT create signals, Paper trades, Live
orders, or recommendations to enter a position.

Goal:
- Turn separate research artifacts into an auditable evidence graph.
- Track which evidence paths are repeatedly helpful or harmful.
- Provide a future foundation for data-driven evidence-weight tuning.
"""
from __future__ import annotations

import csv
import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd

from engine.research_utils import (
    LOG_DIR,
    RESEARCH_DIR,
    read_csv_df,
    run_id,
    safe_float,
    utc_now_iso,
    write_json,
    write_text,
    save_dataframe_csv,
)

VERSION = "v9.0.0"
EVIDENCE_DIR = LOG_DIR / "evidence_graph"
ROOT_CAUSE_DIR = LOG_DIR / "root_cause"
SUITE_DIR = RESEARCH_DIR / "v6_suite"
EVALUATIONS_FILE = LOG_DIR / "decision_evaluations.csv"
OBSERVATIONS_FILE = EVIDENCE_DIR / "evidence_graph_observations.csv"

SOURCE_TOKENS = [
    "federal_reserve_press",
    "federal_reserve_speeches",
    "sec_press_releases",
    "sec_litigation_releases",
    "ethereum_foundation_blog",
    "coinbase_blog",
    "binance_announcements",
    "manual_events",
    "auto_events",
    "coingecko_global",
]

HORIZON = "24h"
MARKET_RETURN_24H = "market_return_after_24h_pct"
SIGNED_RETURN_24H = "root_cause_signed_return_after_24h_pct"
CORRECT_24H = "root_cause_direction_correct_after_24h"


@dataclass
class EvidenceNode:
    node_id: str
    label: str
    node_type: str
    samples: int = 0
    weighted_samples: float = 0.0
    success_count_24h: int = 0
    failure_count_24h: int = 0
    avg_signed_return_24h_pct: float = 0.0
    notes: str = ""


@dataclass
class EvidenceEdge:
    source: str
    target: str
    edge_type: str
    samples: int = 0
    weighted_samples: float = 0.0
    success_count_24h: int = 0
    failure_count_24h: int = 0
    hit_rate_24h: float = 0.0
    avg_signed_return_24h_pct: float = 0.0
    reliability_score: float = 0.0
    verdict: str = ""


@dataclass
class EvidencePath:
    path_id: str
    source_node: str
    narrative_node: str
    root_cause_node: str
    decision_node: str
    outcome_node: str
    samples: int
    weighted_samples: float
    hit_rate_24h: float
    avg_signed_return_24h_pct: float
    reliability_score: float
    verdict: str


@dataclass
class EvidenceGraphReport:
    run_id: str
    generated_utc: str
    version: str
    status: str
    evaluations_file: str
    evaluation_rows: int
    complete_rows: int
    graph_rows: int
    root_cause_rows: int
    nodes_total: int
    edges_total: int
    paths_total: int
    min_samples: int
    research_samples: int
    candidate_samples: int
    graph_maturity: str
    top_nodes: List[Dict[str, Any]] = field(default_factory=list)
    top_edges: List[Dict[str, Any]] = field(default_factory=list)
    top_paths: List[Dict[str, Any]] = field(default_factory=list)
    root_cause_learning_signals: List[Dict[str, Any]] = field(default_factory=list)
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


def _safe_node_part(value: str) -> str:
    text = _upper(value, "UNKNOWN")
    return re.sub(r"[^A-Z0-9_]+", "_", text).strip("_") or "UNKNOWN"


def _to_bool(value: Any) -> Optional[bool]:
    text = _norm(value).lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


def _mean(values: Iterable[float]) -> float:
    clean: List[float] = []
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


def _prob_weight(row: Dict[str, Any]) -> float:
    # Converts root cause probability to a mild sample weight.
    # 54% -> 1.04, 90% -> 1.40. Never lets one row dominate.
    p = safe_float(row.get("root_cause_probability_pct"), 0.0) or 0.0
    return round(0.5 + max(0.0, min(100.0, p)) / 100.0, 4)


def _score_bucket(value: Any) -> str:
    s = safe_float(value, None)
    if s is None:
        return "SCORE_UNKNOWN"
    s = int(round(s))
    lo = int(s // 10 * 10)
    hi = lo + 9
    return f"SCORE_{lo}_{hi}"


def _extract_sources(row: Dict[str, Any]) -> List[str]:
    text = " ".join(
        _norm(row.get(col))
        for col in [
            "root_cause_summary",
            "root_cause_top_causes",
            "market_narrative_summary",
            "causal_top_sources",
            "causal_notes",
        ]
    ).lower()
    found = [s for s in SOURCE_TOKENS if s.lower() in text]
    if not found:
        # Narrative/root cause often aggregate official events without carrying
        # source ids into decision_evaluations. Keep an explicit unknown evidence
        # node instead of inventing a source.
        found = ["unknown_evidence_source"]
    # limit path explosion while preserving the most important tokens
    return found[:4]


def _outcome_label(row: Dict[str, Any]) -> str:
    correct = _to_bool(row.get(CORRECT_24H))
    market = safe_float(row.get(MARKET_RETURN_24H), None)
    if correct is True:
        return "ROOT_CAUSE_HIT_24H"
    if correct is False:
        return "ROOT_CAUSE_MISS_24H"
    if market is None:
        return "OUTCOME_UNKNOWN_24H"
    if market > 0:
        return "MARKET_UP_24H_NO_RC_JUDGEMENT"
    if market < 0:
        return "MARKET_DOWN_24H_NO_RC_JUDGEMENT"
    return "MARKET_FLAT_24H_NO_RC_JUDGEMENT"


def _node(node_type: str, label: str) -> Tuple[str, str]:
    clean = _safe_node_part(label)
    return f"{node_type}:{clean}", clean


def _root_cause_mask(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty or "root_cause_primary" not in df.columns:
        return pd.Series([], dtype=bool)
    cause = df["root_cause_primary"].fillna("").astype(str).str.strip().str.upper()
    return (cause != "") & (~cause.isin(["NAN", "NONE", "NULL", "UNKNOWN", "UNKNOWN_OR_INSUFFICIENT_EVIDENCE"]))


def _prepare_graph_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    w = df.copy()
    if "evaluation_status" in w.columns:
        w = w[w["evaluation_status"].fillna("").astype(str).str.upper() == "COMPLETE"].copy()
    mask = _root_cause_mask(w)
    if len(mask):
        w = w[mask].copy()
    else:
        w = pd.DataFrame()
    return w


def _aggregate_node(node_rows: Dict[str, Dict[str, Any]]) -> List[EvidenceNode]:
    nodes: List[EvidenceNode] = []
    for node_id, meta in node_rows.items():
        returns = meta.get("returns", [])
        nodes.append(EvidenceNode(
            node_id=node_id,
            label=meta.get("label", node_id),
            node_type=meta.get("node_type", "UNKNOWN"),
            samples=int(meta.get("samples", 0)),
            weighted_samples=round(float(meta.get("weighted_samples", 0.0)), 4),
            success_count_24h=int(meta.get("success", 0)),
            failure_count_24h=int(meta.get("failure", 0)),
            avg_signed_return_24h_pct=_mean(returns),
            notes=meta.get("notes", ""),
        ))
    return sorted(nodes, key=lambda n: (n.samples, n.weighted_samples, n.avg_signed_return_24h_pct), reverse=True)


def _edge_verdict(samples: int, hit_rate: float, avg_return: float, *, min_samples: int, research_samples: int) -> str:
    if samples < min_samples:
        return "LOW_SAMPLE_EDGE"
    if samples >= research_samples and hit_rate >= 55 and avg_return > 0:
        return "RESEARCH_POSITIVE_EDGE"
    if samples >= min_samples and hit_rate >= 55 and avg_return > 0:
        return "MIN_SAMPLE_PROMISING_EDGE"
    if samples >= min_samples and (hit_rate < 45 or avg_return < 0):
        return "WEAK_OR_NEGATIVE_EDGE"
    return "MIXED_EDGE"


def _aggregate_edges(edge_rows: Dict[Tuple[str, str, str], Dict[str, Any]], *, min_samples: int, research_samples: int) -> List[EvidenceEdge]:
    edges: List[EvidenceEdge] = []
    for (src, dst, etype), meta in edge_rows.items():
        samples = int(meta.get("samples", 0))
        success = int(meta.get("success", 0))
        failure = int(meta.get("failure", 0))
        returns = meta.get("returns", [])
        hit = _pct(success, success + failure)
        avg_ret = _mean(returns)
        reliability = round((hit - 50.0) / 10.0 + avg_ret + min(samples, 30) / 30.0, 4)
        edges.append(EvidenceEdge(
            source=src,
            target=dst,
            edge_type=etype,
            samples=samples,
            weighted_samples=round(float(meta.get("weighted_samples", 0.0)), 4),
            success_count_24h=success,
            failure_count_24h=failure,
            hit_rate_24h=hit,
            avg_signed_return_24h_pct=avg_ret,
            reliability_score=reliability,
            verdict=_edge_verdict(samples, hit, avg_ret, min_samples=min_samples, research_samples=research_samples),
        ))
    return sorted(edges, key=lambda e: (e.reliability_score, e.samples, e.weighted_samples), reverse=True)


def _build_graph(df: pd.DataFrame, *, min_samples: int, research_samples: int) -> Tuple[List[EvidenceNode], List[EvidenceEdge], List[EvidencePath]]:
    node_rows: Dict[str, Dict[str, Any]] = {}
    edge_rows: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    path_rows: Dict[Tuple[str, str, str, str, str], Dict[str, Any]] = {}

    def add_node(node_id: str, label: str, node_type: str, row: Dict[str, Any], weight: float) -> None:
        item = node_rows.setdefault(node_id, {"label": label, "node_type": node_type, "samples": 0, "weighted_samples": 0.0, "success": 0, "failure": 0, "returns": []})
        item["samples"] += 1
        item["weighted_samples"] += weight
        correct = _to_bool(row.get(CORRECT_24H))
        if correct is True:
            item["success"] += 1
        elif correct is False:
            item["failure"] += 1
        signed = safe_float(row.get(SIGNED_RETURN_24H), None)
        if signed is not None:
            item["returns"].append(float(signed))

    def add_edge(src: str, dst: str, etype: str, row: Dict[str, Any], weight: float) -> None:
        item = edge_rows.setdefault((src, dst, etype), {"samples": 0, "weighted_samples": 0.0, "success": 0, "failure": 0, "returns": []})
        item["samples"] += 1
        item["weighted_samples"] += weight
        correct = _to_bool(row.get(CORRECT_24H))
        if correct is True:
            item["success"] += 1
        elif correct is False:
            item["failure"] += 1
        signed = safe_float(row.get(SIGNED_RETURN_24H), None)
        if signed is not None:
            item["returns"].append(float(signed))

    for _, rec in df.iterrows():
        row = rec.to_dict()
        weight = _prob_weight(row)
        narrative_label = _upper(row.get("market_narrative_label"), "NO_NARRATIVE")
        narrative_dir = _upper(row.get("market_narrative_direction"), "NEUTRAL")
        narrative_theme = _upper(row.get("market_narrative_theme"), "NO_THEME")
        root_cause = _upper(row.get("root_cause_primary"), "UNKNOWN_ROOT_CAUSE")
        root_dir = _upper(row.get("root_cause_direction"), "NEUTRAL")
        decision = f"{_upper(row.get('side'), 'NEUTRAL')}|{_upper(row.get('actionability'), 'UNKNOWN')}|{_score_bucket(row.get('score'))}"
        outcome = _outcome_label(row)

        narrative_id, narrative_clean = _node("NARRATIVE", f"{narrative_label}|{narrative_dir}|{narrative_theme}")
        cause_id, cause_clean = _node("ROOT_CAUSE", f"{root_cause}|{root_dir}")
        decision_id, decision_clean = _node("DECISION_CONTEXT", decision)
        outcome_id, outcome_clean = _node("OUTCOME", outcome)

        for nid, label, ntype in [
            (narrative_id, narrative_clean, "NARRATIVE"),
            (cause_id, cause_clean, "ROOT_CAUSE"),
            (decision_id, decision_clean, "DECISION_CONTEXT"),
            (outcome_id, outcome_clean, "OUTCOME"),
        ]:
            add_node(nid, label, ntype, row, weight)

        sources = _extract_sources(row)
        for src in sources:
            src_id, src_clean = _node("EVIDENCE_SOURCE", src)
            add_node(src_id, src_clean, "EVIDENCE_SOURCE", row, weight)
            add_edge(src_id, narrative_id, "SOURCE_SUPPORTS_NARRATIVE", row, weight)
            add_edge(src_id, cause_id, "SOURCE_SUPPORTS_ROOT_CAUSE", row, weight)
            add_edge(narrative_id, cause_id, "NARRATIVE_SUPPORTS_ROOT_CAUSE", row, weight)
            add_edge(cause_id, decision_id, "ROOT_CAUSE_CONTEXTUALIZES_DECISION", row, weight)
            add_edge(decision_id, outcome_id, "DECISION_OBSERVED_OUTCOME", row, weight)
            add_edge(cause_id, outcome_id, "ROOT_CAUSE_TESTED_BY_OUTCOME", row, weight)
            key = (src_id, narrative_id, cause_id, decision_id, outcome_id)
            p = path_rows.setdefault(key, {"samples": 0, "weighted_samples": 0.0, "success": 0, "failure": 0, "returns": []})
            p["samples"] += 1
            p["weighted_samples"] += weight
            correct = _to_bool(row.get(CORRECT_24H))
            if correct is True:
                p["success"] += 1
            elif correct is False:
                p["failure"] += 1
            signed = safe_float(row.get(SIGNED_RETURN_24H), None)
            if signed is not None:
                p["returns"].append(float(signed))

    nodes = _aggregate_node(node_rows)
    edges = _aggregate_edges(edge_rows, min_samples=min_samples, research_samples=research_samples)
    paths: List[EvidencePath] = []
    for key, meta in path_rows.items():
        src, narrative, cause, decision, outcome = key
        samples = int(meta["samples"])
        success = int(meta["success"])
        failure = int(meta["failure"])
        hit = _pct(success, success + failure)
        avg_ret = _mean(meta.get("returns", []))
        reliability = round((hit - 50.0) / 10.0 + avg_ret + min(samples, 30) / 30.0, 4)
        paths.append(EvidencePath(
            path_id=" -> ".join(key),
            source_node=src,
            narrative_node=narrative,
            root_cause_node=cause,
            decision_node=decision,
            outcome_node=outcome,
            samples=samples,
            weighted_samples=round(float(meta.get("weighted_samples", 0.0)), 4),
            hit_rate_24h=hit,
            avg_signed_return_24h_pct=avg_ret,
            reliability_score=reliability,
            verdict=_edge_verdict(samples, hit, avg_ret, min_samples=min_samples, research_samples=research_samples),
        ))
    paths = sorted(paths, key=lambda p: (p.reliability_score, p.samples, p.weighted_samples), reverse=True)
    return nodes, edges, paths


def _learning_signals(df: pd.DataFrame, *, min_samples: int) -> List[Dict[str, Any]]:
    if df.empty or "root_cause_primary" not in df.columns:
        return []
    work = df.copy()
    work["_cause"] = work["root_cause_primary"].map(_upper)
    work["_direction"] = work.get("root_cause_direction", pd.Series(dtype=str)).map(_upper)
    out: List[Dict[str, Any]] = []
    for (cause, direction), g in work.groupby(["_cause", "_direction"]):
        correct = [_to_bool(v) for v in g.get(CORRECT_24H, pd.Series(dtype=str)).tolist()]
        valid = [v for v in correct if v is not None]
        signed = []
        for v in g.get(SIGNED_RETURN_24H, pd.Series(dtype=float)).tolist():
            f = safe_float(v, None)
            if f is not None:
                signed.append(float(f))
        samples = len(valid)
        hit = _pct(sum(1 for v in valid if v), samples)
        avg = _mean(signed)
        if samples < min_samples:
            verdict = "LOW_SAMPLE_DO_NOT_RETUNE"
        elif hit >= 55 and avg > 0:
            verdict = "EVIDENCE_WEIGHT_CAN_BE_REVIEWED_UP"
        elif hit < 45 or avg < 0:
            verdict = "EVIDENCE_WEIGHT_REVIEW_DOWN_OR_CONDITIONAL"
        else:
            verdict = "MIXED_KEEP_NEUTRAL_WEIGHT"
        out.append({
            "root_cause_primary": cause,
            "root_cause_direction": direction,
            "samples_24h": samples,
            "hit_rate_24h": hit,
            "avg_signed_return_24h_pct": avg,
            "verdict": verdict,
        })
    return sorted(out, key=lambda x: (x["samples_24h"], x["avg_signed_return_24h_pct"]), reverse=True)


def run_evidence_graph(*, min_samples: int = 10, research_samples: int = 30, candidate_samples: int = 90) -> EvidenceGraphReport:
    rid = run_id("evidence_graph")
    warnings = [
        "Evidence Graph فقط رابطه‌های پژوهشی بین شواهد، روایت، علت و outcome را می‌سازد؛ سیگنال خرید/فروش نیست.",
        "تا وقتی sample کافی وجود نداشته باشد، هیچ وزن evidence نباید برای Paper/Live تغییر کند.",
    ]
    recommendations = [
        "چرخه Forward را منظم اجرا کن تا مسیرهای evidence به outcomeهای بیشتری وصل شوند.",
        "مسیرهایی که چند هفته متوالی hit-rate و signed-return مثبت دارند بعداً می‌توانند وارد Evidence Weight Review شوند.",
        "اگر یک منبع یا روایت در Forward چندبار fail شد، وزن آن باید فقط بعد از sample کافی بازبینی شود.",
    ]
    blockers: List[str] = []
    df = read_csv_df(EVALUATIONS_FILE)
    evaluation_rows = int(len(df)) if not df.empty else 0
    complete_rows = int((df.get("evaluation_status", pd.Series(dtype=str)).fillna("").astype(str).str.upper() == "COMPLETE").sum()) if not df.empty and "evaluation_status" in df.columns else evaluation_rows
    graph_df = _prepare_graph_rows(df)
    root_cause_rows = int(len(graph_df))
    nodes: List[EvidenceNode] = []
    edges: List[EvidenceEdge] = []
    paths: List[EvidencePath] = []
    if graph_df.empty:
        blockers.append("هیچ decision_evaluations row با root_cause قابل ساخت گراف پیدا نشد؛ root_cause_dashboard و decision_evaluator را اجرا کن.")
        status = "NO_EVIDENCE_GRAPH_ROWS"
        maturity = "NO_GRAPH_DATA"
        signals: List[Dict[str, Any]] = []
    else:
        nodes, edges, paths = _build_graph(graph_df, min_samples=min_samples, research_samples=research_samples)
        signals = _learning_signals(graph_df, min_samples=min_samples)
        if root_cause_rows * 3 < min_samples:
            status = "EVIDENCE_GRAPH_ACTIVE_LOW_SAMPLE"
            maturity = "LOW_SAMPLE_ACCUMULATING"
            blockers.append(f"Evidence graph evaluated cells کمتر از حداقل است: {root_cause_rows * 3}/{min_samples}")
        elif root_cause_rows * 3 < research_samples:
            status = "EVIDENCE_GRAPH_MIN_SAMPLE_READY"
            maturity = "MIN_SAMPLE_READY"
        elif root_cause_rows * 3 < candidate_samples:
            status = "EVIDENCE_GRAPH_RESEARCH_SAMPLE_READY"
            maturity = "RESEARCH_SAMPLE_READY"
        else:
            status = "EVIDENCE_GRAPH_CANDIDATE_SAMPLE_READY"
            maturity = "CANDIDATE_SAMPLE_READY"

    return EvidenceGraphReport(
        run_id=rid,
        generated_utc=utc_now_iso(),
        version=VERSION,
        status=status,
        evaluations_file=str(EVALUATIONS_FILE),
        evaluation_rows=evaluation_rows,
        complete_rows=complete_rows,
        graph_rows=root_cause_rows,
        root_cause_rows=root_cause_rows,
        nodes_total=len(nodes),
        edges_total=len(edges),
        paths_total=len(paths),
        min_samples=min_samples,
        research_samples=research_samples,
        candidate_samples=candidate_samples,
        graph_maturity=maturity,
        top_nodes=[asdict(n) for n in nodes[:20]],
        top_edges=[asdict(e) for e in edges[:30]],
        top_paths=[asdict(p) for p in paths[:20]],
        root_cause_learning_signals=signals[:20],
        blockers=blockers,
        warnings=warnings,
        recommendations=recommendations,
    )


def format_evidence_graph_console(report: EvidenceGraphReport, compact: bool = True) -> str:
    sep = "=" * 110
    lines = [sep, f"🕸️ Freakto Evidence Graph Engine {VERSION}", sep]
    lines.append(f"Status                 : {report.status}")
    lines.append(f"Run ID                 : {report.run_id}")
    lines.append(f"Evaluations File       : {report.evaluations_file}")
    lines.append(f"Rows / Complete        : {report.evaluation_rows} / {report.complete_rows}")
    lines.append(f"Graph Rows             : {report.graph_rows}")
    lines.append(f"Nodes / Edges / Paths  : {report.nodes_total} / {report.edges_total} / {report.paths_total}")
    lines.append(f"Graph Maturity         : {report.graph_maturity}")
    lines.append(f"Min/Research/Candidate : {report.min_samples} / {report.research_samples} / {report.candidate_samples} evaluated cells")
    if report.top_paths:
        lines.append("\nTop Evidence Paths:")
        for p in report.top_paths[:5 if compact else 12]:
            lines.append(
                f"- {p.get('source_node')} -> {p.get('root_cause_node')} -> {p.get('outcome_node')} | "
                f"n={p.get('samples')} hit24={p.get('hit_rate_24h')}% avg24={p.get('avg_signed_return_24h_pct')}% | {p.get('verdict')}"
            )
    if report.root_cause_learning_signals:
        lines.append("\nRoot Cause Learning Signals:")
        for s in report.root_cause_learning_signals[:5 if compact else 12]:
            lines.append(
                f"- {s.get('root_cause_primary')} | {s.get('root_cause_direction')} | "
                f"n24={s.get('samples_24h')} hit24={s.get('hit_rate_24h')}% avg24={s.get('avg_signed_return_24h_pct')}% | {s.get('verdict')}"
            )
    if not compact and report.top_edges:
        lines.append("\nTop Edges:")
        for e in report.top_edges[:20]:
            lines.append(
                f"- {e.get('source')} -> {e.get('target')} ({e.get('edge_type')}) | "
                f"n={e.get('samples')} hit24={e.get('hit_rate_24h')}% score={e.get('reliability_score')} | {e.get('verdict')}"
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


def _append_observation(report: EvidenceGraphReport) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    top_path = report.top_paths[0] if report.top_paths else {}
    top_signal = report.root_cause_learning_signals[0] if report.root_cause_learning_signals else {}
    row = {
        "run_id": report.run_id,
        "generated_utc": report.generated_utc,
        "version": report.version,
        "status": report.status,
        "graph_rows": report.graph_rows,
        "nodes_total": report.nodes_total,
        "edges_total": report.edges_total,
        "paths_total": report.paths_total,
        "graph_maturity": report.graph_maturity,
        "top_path": top_path.get("path_id", ""),
        "top_path_samples": top_path.get("samples", ""),
        "top_path_hit_rate_24h": top_path.get("hit_rate_24h", ""),
        "top_path_avg_signed_return_24h_pct": top_path.get("avg_signed_return_24h_pct", ""),
        "top_learning_root_cause": top_signal.get("root_cause_primary", ""),
        "top_learning_verdict": top_signal.get("verdict", ""),
    }
    exists = OBSERVATIONS_FILE.exists() and OBSERVATIONS_FILE.stat().st_size > 0
    with OBSERVATIONS_FILE.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    return OBSERVATIONS_FILE


def save_evidence_graph_report(report: EvidenceGraphReport):
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    SUITE_DIR.mkdir(parents=True, exist_ok=True)
    data = asdict(report)
    json_path = EVIDENCE_DIR / f"evidence_graph_{report.run_id}.json"
    md_path = EVIDENCE_DIR / f"evidence_graph_report_{report.run_id}.md"
    nodes_csv = EVIDENCE_DIR / f"evidence_graph_nodes_{report.run_id}.csv"
    edges_csv = EVIDENCE_DIR / f"evidence_graph_edges_{report.run_id}.csv"
    paths_csv = EVIDENCE_DIR / f"evidence_graph_paths_{report.run_id}.csv"
    write_json(json_path, data)
    write_text(md_path, format_evidence_graph_console(report, compact=False))
    save_dataframe_csv(nodes_csv, pd.DataFrame(report.top_nodes))
    save_dataframe_csv(edges_csv, pd.DataFrame(report.top_edges))
    save_dataframe_csv(paths_csv, pd.DataFrame(report.top_paths))
    obs = _append_observation(report)
    write_json(SUITE_DIR / f"evidence_graph_{report.run_id}.json", data)
    return json_path, md_path, nodes_csv, edges_csv, paths_csv, obs
