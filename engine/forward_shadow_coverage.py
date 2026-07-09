"""
Freakto v6.3.0 - Forward Shadow Coverage & Bull Regime Probe

Purpose:
- Explain why v6.2 Regime Shadow gates may have zero signals.
- Measure which regimes are actually receiving Forward decisions/signals.
- Probe TRENDING_BULL + structure/volume/risk combinations without promoting them
  to actionable candidates.
- Compare Forward low-sample observations with Backtest net results so the project
  does not over-trust a small Forward streak.

Safety:
This module never sends orders and never creates paper trades. It only reads logs
and writes research reports under logs/research/v6_suite/.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from engine.research_utils import (
    RESEARCH_DIR,
    SHADOW_SIGNALS,
    RETURN_COLUMNS,
    DIRECTIONAL_SIDES,
    load_decisions_df,
    load_forward_eval_df,
    load_backtest_df,
    directional_complete,
    metric_summary,
    read_csv_df,
    write_json,
    write_text,
    save_dataframe_csv,
    safe_float,
    pct,
    utc_now_iso,
    run_id,
)

VERSION = "v6.3.0"
SUITE_DIR = RESEARCH_DIR / "v6_suite"

REGIME_BEAR_GATES = [
    "REGIME_TRENDING_BEAR__RISK_MEDIUM",
    "REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT",
    "REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10",
    "REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT",
]


@dataclass
class CoverageReport:
    run_id: str
    generated_utc: str
    status: str
    version: str
    horizon: str
    min_samples: int
    decision_rows: int
    directional_decisions: int
    evaluation_rows: int
    complete_evaluations: int
    shadow_signal_rows: int
    evaluated_shadow_rows: int
    forward_regime_counts: List[Dict[str, Any]] = field(default_factory=list)
    shadow_gate_coverage: List[Dict[str, Any]] = field(default_factory=list)
    shadow_regime_coverage: List[Dict[str, Any]] = field(default_factory=list)
    bull_forward_probes: List[Dict[str, Any]] = field(default_factory=list)
    bear_zero_signal_diagnostics: List[Dict[str, Any]] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _norm(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return default
    return text


def _upper_series(df: pd.DataFrame, col: str, default: str = "") -> pd.Series:
    if col not in df.columns:
        return pd.Series([default] * len(df), index=df.index)
    return df[col].fillna(default).astype(str).str.strip().str.upper()


def _safe_numeric(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series([0.0] * len(df), index=df.index)
    return pd.to_numeric(df[col], errors="coerce").fillna(0.0)


def _prepare_decisions_for_probe(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    w = df.copy()
    defaults = {
        "decision_id": "",
        "symbol": "",
        "side": "NEUTRAL",
        "score": 0,
        "risk_label": "",
        "regime_label": "UNKNOWN",
        "regime_source": "",
        "regime_label_quality": "",
        "trend_score": 0,
        "momentum_score": 0,
        "volume_score": 0,
        "structure_score": 0,
        "historical_edge_score": 0,
        "long_score": 0,
        "short_score": 0,
        "candle_timestamp": "",
        "logged_at_utc": "",
    }
    for col, default in defaults.items():
        if col not in w.columns:
            w[col] = default
    for col in ["score", "trend_score", "momentum_score", "volume_score", "structure_score", "historical_edge_score", "long_score", "short_score"]:
        w[col] = pd.to_numeric(w[col], errors="coerce").fillna(0.0)
    for col in ["decision_id", "symbol", "side", "risk_label", "regime_label", "regime_source", "regime_label_quality"]:
        w[col] = w[col].fillna("").astype(str).str.strip()
    w["side"] = w["side"].str.upper()
    w["regime_label"] = w["regime_label"].replace("", "UNKNOWN").str.upper()
    w["risk_label_upper"] = w["risk_label"].astype(str).str.upper()
    return w


def _join_forward_decisions_and_evals(horizon: str) -> pd.DataFrame:
    decisions = _prepare_decisions_for_probe(load_decisions_df())
    evals = load_forward_eval_df()
    if decisions.empty:
        return pd.DataFrame()
    if evals is None or evals.empty or "decision_id" not in evals.columns:
        for col in ["evaluation_status", *RETURN_COLUMNS.values(), "target_1_hit", "stop_hit", "mfe_pct", "mae_pct"]:
            decisions[col] = ""
        return decisions
    keep_cols = ["decision_id", "evaluation_status", *RETURN_COLUMNS.values(), "target_1_hit", "stop_hit", "mfe_pct", "mae_pct"]
    for col in keep_cols:
        if col not in evals.columns:
            evals[col] = ""
    eval_work = evals[keep_cols].drop_duplicates(subset=["decision_id"], keep="last")
    joined = decisions.merge(eval_work, on="decision_id", how="left", suffixes=("", "_eval"))
    return joined


def _complete_directional(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    w = df.copy()
    if "evaluation_status" in w.columns:
        w = w[_upper_series(w, "evaluation_status") == "COMPLETE"].copy()
    return w[_upper_series(w, "side").isin(DIRECTIONAL_SIDES)].copy()


def _filter(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    mask = pd.Series([True] * len(df), index=df.index)
    if "regime_label" in filters:
        mask &= _upper_series(df, "regime_label") == str(filters["regime_label"]).upper()
    if "side" in filters:
        mask &= _upper_series(df, "side") == str(filters["side"]).upper()
    if "symbol" in filters:
        mask &= _upper_series(df, "symbol") == str(filters["symbol"]).upper()
    if "risk_medium" in filters and filters["risk_medium"]:
        risk = _upper_series(df, "risk_label")
        mask &= risk.str.contains("MEDIUM") | risk.str.contains("متوسط") | risk.str.contains("مدیوم")
    for col in ["score", "structure_score", "volume_score", "historical_edge_score"]:
        key = f"{col}_min"
        if key in filters:
            mask &= _safe_numeric(df, col) >= float(filters[key])
    return df[mask].copy()


def _metric(df: pd.DataFrame, horizon: str, use_net: bool = False) -> Dict[str, Any]:
    if df is None or df.empty:
        return metric_summary(pd.DataFrame(), horizon=horizon, use_net=use_net)
    return metric_summary(df, horizon=horizon, use_net=use_net)


def _regime_counts(decisions: pd.DataFrame) -> List[Dict[str, Any]]:
    if decisions.empty:
        return []
    total = len(decisions)
    side_mask = _upper_series(decisions, "side").isin(DIRECTIONAL_SIDES)
    counts = []
    regimes = _upper_series(decisions, "regime_label", "UNKNOWN").replace("", "UNKNOWN")
    for regime, group in decisions.groupby(regimes):
        directional = int(side_mask.loc[group.index].sum())
        direct = int((_upper_series(group, "regime_source") == "DIRECT_ENGINE").sum()) if "regime_source" in group.columns else 0
        proxy = int((_upper_series(group, "regime_label_quality").str.contains("PROXY")).sum()) if "regime_label_quality" in group.columns else 0
        counts.append({
            "regime": regime or "UNKNOWN",
            "rows": int(len(group)),
            "share_pct": pct(int(len(group)), total),
            "directional_rows": directional,
            "direct_engine_rows": direct,
            "proxy_or_text_rows": proxy,
        })
    return sorted(counts, key=lambda r: (r["rows"], r["directional_rows"]), reverse=True)


def _shadow_metrics(shadow: pd.DataFrame, horizon: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if shadow is None or shadow.empty:
        return [], []
    w = shadow.copy()
    for col in ["selected_return_pct", "mfe_pct", "mae_pct"]:
        if col in w.columns:
            w[col] = pd.to_numeric(w[col], errors="coerce")
    if "gate_name" not in w.columns:
        return [], []
    gate_rows = []
    for gate, group in w.groupby(w["gate_name"].fillna("").astype(str)):
        if not gate:
            continue
        if "shadow_status" in group.columns:
            evaluated = group[group["shadow_status"].astype(str).str.upper() == "EVALUATED"]
        else:
            evaluated = group.dropna(subset=["selected_return_pct"]) if "selected_return_pct" in group.columns else pd.DataFrame()
        ret = pd.to_numeric(evaluated.get("selected_return_pct", pd.Series(dtype=float)), errors="coerce").dropna()
        regimes = group.get("regime_label", pd.Series(["UNKNOWN"] * len(group), index=group.index)).fillna("UNKNOWN").astype(str).str.upper()
        top_regime = "UNKNOWN"
        if len(regimes):
            top_regime = regimes.value_counts().index[0]
        gate_rows.append({
            "gate": gate,
            "family": _norm(group.get("gate_family", pd.Series([""])).iloc[0]) if "gate_family" in group.columns else "",
            "signals": int(len(group)),
            "evaluated": int(len(ret)),
            "avg_return_pct": round(float(ret.mean()), 4) if len(ret) else 0.0,
            "win_rate": pct(int((ret > 0).sum()), int(len(ret))) if len(ret) else 0.0,
            "dominant_regime": top_regime,
            "regime_count": int((regimes == top_regime).sum()) if top_regime else 0,
        })
    reg_rows = []
    if "regime_label" in w.columns:
        for regime, group in w.groupby(w["regime_label"].fillna("UNKNOWN").astype(str).str.upper()):
            if "shadow_status" in group.columns:
                evaluated = group[group["shadow_status"].astype(str).str.upper() == "EVALUATED"]
            else:
                evaluated = group.dropna(subset=["selected_return_pct"]) if "selected_return_pct" in group.columns else pd.DataFrame()
            ret = pd.to_numeric(evaluated.get("selected_return_pct", pd.Series(dtype=float)), errors="coerce").dropna()
            reg_rows.append({
                "regime": regime or "UNKNOWN",
                "shadow_signals": int(len(group)),
                "evaluated": int(len(ret)),
                "avg_return_pct": round(float(ret.mean()), 4) if len(ret) else 0.0,
                "win_rate": pct(int((ret > 0).sum()), int(len(ret))) if len(ret) else 0.0,
                "distinct_gates": int(group.get("gate_name", pd.Series(dtype=str)).astype(str).nunique()) if "gate_name" in group.columns else 0,
            })
    return sorted(gate_rows, key=lambda r: (r["signals"], r["evaluated"], r["avg_return_pct"]), reverse=True), sorted(reg_rows, key=lambda r: r["shadow_signals"], reverse=True)


def _historical_metric_for(filters: Dict[str, Any], horizon: str) -> Dict[str, Any]:
    hist = directional_complete(load_backtest_df())
    if hist.empty:
        return _metric(pd.DataFrame(), horizon, use_net=True)
    # normalize expected columns
    if "risk_label" in hist.columns:
        hist["risk_label"] = hist["risk_label"].fillna("").astype(str)
    if "regime_label" in hist.columns:
        hist["regime_label"] = hist["regime_label"].fillna("UNKNOWN").astype(str).str.upper()
    selected = _filter(hist, filters)
    return _metric(selected, horizon, use_net=True)


def _forward_bull_probes(joined: pd.DataFrame, horizon: str, min_samples: int) -> List[Dict[str, Any]]:
    complete = _complete_directional(joined)
    probe_specs = [
        ("BULL_STRUCTURE_SCORE_GE_10", {"regime_label": "TRENDING_BULL", "structure_score_min": 10}),
        ("BULL_STRUCTURE_SCORE_GE_10_LONG", {"regime_label": "TRENDING_BULL", "structure_score_min": 10, "side": "LONG"}),
        ("BULL_VOLUME_SCORE_GE_10", {"regime_label": "TRENDING_BULL", "volume_score_min": 10}),
        ("BULL_RISK_MEDIUM", {"regime_label": "TRENDING_BULL", "risk_medium": True}),
        ("BULL_SCORE_GE_80", {"regime_label": "TRENDING_BULL", "score_min": 80}),
        ("BULL_BNB_LONG_SCORE_GE_60", {"regime_label": "TRENDING_BULL", "symbol": "BNB/USDT", "side": "LONG", "score_min": 60}),
    ]
    rows: List[Dict[str, Any]] = []
    for name, filters in probe_specs:
        fwd = _filter(complete, filters)
        fwd_m = _metric(fwd, horizon, use_net=False)
        hist_m = _historical_metric_for(filters, horizon)
        verdict = "NO_FORWARD_SAMPLE"
        fwd_n = int(fwd_m.get("samples", 0) or 0)
        fwd_avg = float(fwd_m.get("avg_return_pct", 0.0) or 0.0)
        hist_n = int(hist_m.get("samples", 0) or 0)
        hist_avg = float(hist_m.get("avg_return_pct", 0.0) or 0.0)
        if fwd_n == 0:
            verdict = "NO_FORWARD_SAMPLE"
        elif fwd_n < min_samples and fwd_avg > 0 and hist_avg <= 0:
            verdict = "FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT"
        elif fwd_n < min_samples and fwd_avg > 0:
            verdict = "FORWARD_PROMISING_LOW_SAMPLE"
        elif fwd_avg > 0 and hist_avg > 0:
            verdict = "FORWARD_AND_BACKTEST_POSITIVE_RESEARCH_ONLY"
        elif fwd_avg > 0:
            verdict = "FORWARD_POSITIVE_BACKTEST_UNCONFIRMED"
        elif fwd_n < min_samples:
            verdict = "LOW_SAMPLE_NO_EDGE"
        else:
            verdict = "FORWARD_NO_EDGE"
        rows.append({
            "probe": name,
            "filters": filters,
            "verdict": verdict,
            "forward_samples": fwd_n,
            "forward_avg_pct": fwd_m.get("avg_return_pct", 0.0),
            "forward_win_rate": fwd_m.get("win_rate", 0.0),
            "forward_t1_rate": fwd_m.get("target_1_hit_rate", 0.0),
            "forward_stop_rate": fwd_m.get("stop_hit_rate", 0.0),
            "forward_mfe_mae": fwd_m.get("mfe_mae_ratio", 0.0),
            "backtest_samples": hist_n,
            "backtest_net_avg_pct": hist_m.get("avg_return_pct", 0.0),
            "backtest_win_rate": hist_m.get("win_rate", 0.0),
            "backtest_t1_rate": hist_m.get("target_1_hit_rate", 0.0),
            "backtest_stop_rate": hist_m.get("stop_hit_rate", 0.0),
            "backtest_mfe_mae": hist_m.get("mfe_mae_ratio", 0.0),
        })
    return sorted(rows, key=lambda r: (r["forward_samples"], r["forward_avg_pct"]), reverse=True)


def _bear_zero_diagnostics(joined: pd.DataFrame, shadow_gate_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if joined is None or joined.empty:
        return [{"gate": g, "cause": "NO_FORWARD_DECISIONS", "matching_decisions": 0} for g in REGIME_BEAR_GATES]
    directional = joined[_upper_series(joined, "side").isin(DIRECTIONAL_SIDES)].copy()
    bear = _filter(directional, {"regime_label": "TRENDING_BEAR"})
    results = []
    existing = {row.get("gate"): row for row in shadow_gate_rows}
    for gate in REGIME_BEAR_GATES:
        filters: Dict[str, Any] = {"regime_label": "TRENDING_BEAR"}
        if "RISK_MEDIUM" in gate:
            filters["risk_medium"] = True
        if "STRUCTURE_SCORE_GE_10" in gate:
            filters["structure_score_min"] = 10
        if gate.endswith("__SHORT"):
            filters["side"] = "SHORT"
        match = _filter(directional, filters)
        if len(match) > 0:
            cause = "MATCHING_DECISIONS_EXIST_BUT_NOT_IN_SHADOW_LEDGER"
        elif len(bear) == 0:
            cause = "NO_TRENDING_BEAR_FORWARD_DECISIONS"
        elif gate.endswith("__SHORT") and int((_upper_series(bear, "side") == "SHORT").sum()) == 0:
            cause = "TRENDING_BEAR_EXISTS_BUT_NO_SHORT_DECISIONS"
        elif "STRUCTURE_SCORE_GE_10" in gate and int((_safe_numeric(bear, "structure_score") >= 10).sum()) == 0:
            cause = "TRENDING_BEAR_EXISTS_BUT_STRUCTURE_LT_10"
        elif "RISK_MEDIUM" in gate:
            risk = _upper_series(bear, "risk_label")
            if int((risk.str.contains("MEDIUM") | risk.str.contains("متوسط") | risk.str.contains("مدیوم")).sum()) == 0:
                cause = "TRENDING_BEAR_EXISTS_BUT_NO_RISK_MEDIUM"
            else:
                cause = "TRENDING_BEAR_EXISTS_BUT_OTHER_FILTER_BLOCKED"
        else:
            cause = "OTHER_FILTER_BLOCKED"
        results.append({
            "gate": gate,
            "cause": cause,
            "matching_decisions": int(len(match)),
            "trend_bear_decisions": int(len(bear)),
            "existing_shadow_signals": int(existing.get(gate, {}).get("signals", 0) or 0),
        })
    return results


def run_forward_shadow_coverage(*, horizon: str = "24h", min_samples: int = 30) -> Dict[str, Any]:
    horizon = str(horizon).lower().replace(" ", "")
    if horizon not in RETURN_COLUMNS:
        horizon = "24h"
    rid = run_id("forward_shadow_coverage")
    joined = _join_forward_decisions_and_evals(horizon)
    decisions = _prepare_decisions_for_probe(load_decisions_df())
    evals = load_forward_eval_df()
    shadow = read_csv_df(SHADOW_SIGNALS)
    complete = _complete_directional(joined)

    regime_counts = _regime_counts(decisions)
    shadow_gate_coverage, shadow_regime_coverage = _shadow_metrics(shadow, horizon)
    bull_probes = _forward_bull_probes(joined, horizon, min_samples)
    zero_diag = _bear_zero_diagnostics(joined, shadow_gate_coverage)

    evaluated_shadow_rows = 0
    if shadow is not None and not shadow.empty and "shadow_status" in shadow.columns:
        evaluated_shadow_rows = int((shadow["shadow_status"].astype(str).str.upper() == "EVALUATED").sum())

    contradictions = []
    for probe in bull_probes:
        if probe["verdict"] in {"FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT", "FORWARD_POSITIVE_BACKTEST_UNCONFIRMED"}:
            contradictions.append(
                f"{probe['probe']}: Forward avg={probe['forward_avg_pct']}% با n={probe['forward_samples']} اما Backtest net={probe['backtest_net_avg_pct']}% است."
            )

    blockers = []
    recommendations = []
    known_bear_count = next((r["rows"] for r in regime_counts if r["regime"] == "TRENDING_BEAR"), 0)
    if known_bear_count == 0:
        blockers.append("هیچ تصمیم Forward در TRENDING_BEAR وجود ندارد؛ Regime Bear shadow gates طبیعی است که signal نگیرند.")
        recommendations.append("Regime Bear gates را فعال نگه دار، اما قضاوت را تا رخ دادن TRENDING_BEAR در Forward به تعویق بینداز.")
    if evaluated_shadow_rows < min_samples:
        blockers.append(f"Shadow evaluated samples کمتر از {min_samples} است: {evaluated_shadow_rows}")
    top_bull = bull_probes[0] if bull_probes else None
    if top_bull and top_bull.get("forward_samples", 0) > 0:
        recommendations.append(
            f"فعال‌ترین Bull probe فعلی: {top_bull['probe']} | forward n={top_bull['forward_samples']} | avg={top_bull['forward_avg_pct']}% | verdict={top_bull['verdict']}."
        )
        if str(top_bull.get("verdict", "")).startswith("FORWARD_PROMISING"):
            recommendations.append("Bull probe فقط مشاهده‌ای است؛ تا وقتی Backtest/Forward هر دو robust نشوند، به Shadow Candidate ارتقا نده.")
    recommendations.append("برای تصمیم‌گیری بعدی، STRUCTURE_SCORE_GE_10 را جداگانه به تفکیک regime در Forward دنبال کن.")

    status = "FORWARD_SHADOW_COVERAGE_READY"
    if contradictions:
        status = "FORWARD_PROMISING_BACKTEST_CONFLICTS_FOUND"
    if known_bear_count == 0:
        status = "NO_BEAR_FORWARD_COVERAGE_YET"
    if decisions.empty:
        status = "NO_FORWARD_DECISIONS"

    warnings = [
        "این ماژول فقط coverage و probe تحقیقاتی می‌سازد؛ هیچ Paper/Live فعال نمی‌کند.",
        "Bull probeها کاندید قطعی نیستند؛ تضاد Forward کم‌نمونه با Backtest باید جدی گرفته شود.",
        "برچسب‌های legacy/proxy regime برای تحقیق‌اند؛ Forward جدید DIRECT_ENGINE ارزش بیشتری دارد.",
    ]

    report = CoverageReport(
        run_id=rid,
        generated_utc=utc_now_iso(),
        status=status,
        version=VERSION,
        horizon=horizon,
        min_samples=min_samples,
        decision_rows=int(len(decisions)),
        directional_decisions=int((_upper_series(decisions, "side").isin(DIRECTIONAL_SIDES)).sum()) if not decisions.empty else 0,
        evaluation_rows=int(len(evals)) if evals is not None and not evals.empty else 0,
        complete_evaluations=int(len(complete)),
        shadow_signal_rows=int(len(shadow)) if shadow is not None and not shadow.empty else 0,
        evaluated_shadow_rows=evaluated_shadow_rows,
        forward_regime_counts=regime_counts,
        shadow_gate_coverage=shadow_gate_coverage,
        shadow_regime_coverage=shadow_regime_coverage,
        bull_forward_probes=bull_probes,
        bear_zero_signal_diagnostics=zero_diag,
        contradictions=contradictions,
        blockers=blockers,
        recommendations=recommendations,
        warnings=warnings,
    )
    return asdict(report)


def format_forward_shadow_coverage_console(report: Dict[str, Any], *, compact: bool = False) -> str:
    sep = "=" * 110
    lines = [sep, f"🔎 Freakto Forward Shadow Coverage & Bull Regime Probe {VERSION}", sep]
    lines.append(f"Status                 : {report.get('status')}")
    lines.append(f"Run ID                 : {report.get('run_id')}")
    lines.append(f"Horizon                : {report.get('horizon')}")
    lines.append(f"Decision Rows          : {report.get('decision_rows')}")
    lines.append(f"Directional Decisions  : {report.get('directional_decisions')}")
    lines.append(f"Evaluation Rows        : {report.get('evaluation_rows')}")
    lines.append(f"Complete Evaluations   : {report.get('complete_evaluations')}")
    lines.append(f"Shadow Signals         : {report.get('shadow_signal_rows')}")
    lines.append(f"Evaluated Shadow       : {report.get('evaluated_shadow_rows')}")

    lines.append("\nForward Regime Coverage:")
    rows = report.get("forward_regime_counts", [])
    if rows:
        for row in rows[:8]:
            lines.append(f"- {row.get('regime')}: rows={row.get('rows')} | directional={row.get('directional_rows')} | share={row.get('share_pct')}% | direct={row.get('direct_engine_rows')} | proxy/text={row.get('proxy_or_text_rows')}")
    else:
        lines.append("- No regime data yet.")

    lines.append("\nShadow Gate Coverage:")
    if report.get("shadow_gate_coverage"):
        for row in report.get("shadow_gate_coverage", [])[:10]:
            lines.append(f"- {row.get('gate')}: signals={row.get('signals')} | eval={row.get('evaluated')} | avg={row.get('avg_return_pct')}% | win={row.get('win_rate')}% | dominant_regime={row.get('dominant_regime')}")
    else:
        lines.append("- No shadow signals yet.")

    lines.append("\nBull Regime Probes:")
    if report.get("bull_forward_probes"):
        for row in report.get("bull_forward_probes", [])[:8]:
            lines.append(
                f"- {row.get('probe')}: {row.get('verdict')} | fwd_n={row.get('forward_samples')} | fwd_avg={row.get('forward_avg_pct')}% | fwd_win={row.get('forward_win_rate')}% | bt_n={row.get('backtest_samples')} | bt_net={row.get('backtest_net_avg_pct')}%"
            )
    else:
        lines.append("- No Bull probes available.")

    if not compact:
        lines.append("\nBear Regime Zero-Signal Diagnostics:")
        for row in report.get("bear_zero_signal_diagnostics", [])[:8]:
            lines.append(f"- {row.get('gate')}: cause={row.get('cause')} | matches={row.get('matching_decisions')} | bear_decisions={row.get('trend_bear_decisions')}")

    if report.get("contradictions"):
        lines.append("\nBacktest/Forward Contradictions:")
        for item in report.get("contradictions", [])[:8]:
            lines.append(f"⚠️ {item}")
    if report.get("blockers"):
        lines.append("\nBlockers:")
        for item in report.get("blockers", [])[:8]:
            lines.append(f"⛔ {item}")
    if report.get("recommendations"):
        lines.append("\nRecommendations:")
        for item in report.get("recommendations", [])[:8]:
            lines.append(f"→ {item}")
    if report.get("warnings"):
        lines.append("\nWarnings:")
        for item in report.get("warnings", [])[:8]:
            lines.append(f"⚠️ {item}")
    lines.append(sep)
    return "\n".join(lines)


def save_forward_shadow_coverage(report: Dict[str, Any]) -> Tuple[Path, Path, Path, Path]:
    SUITE_DIR.mkdir(parents=True, exist_ok=True)
    rid = report.get("run_id") or run_id("forward_shadow_coverage")
    json_path = SUITE_DIR / f"forward_shadow_coverage_{rid}.json"
    md_path = SUITE_DIR / f"forward_shadow_coverage_report_{rid}.md"
    bull_csv = SUITE_DIR / f"forward_bull_probes_{rid}.csv"
    gate_csv = SUITE_DIR / f"forward_shadow_gate_coverage_{rid}.csv"
    write_json(json_path, report)
    write_text(md_path, format_forward_shadow_coverage_console(report, compact=False))
    save_dataframe_csv(bull_csv, pd.DataFrame(report.get("bull_forward_probes", [])))
    save_dataframe_csv(gate_csv, pd.DataFrame(report.get("shadow_gate_coverage", [])))
    return json_path, md_path, bull_csv, gate_csv
