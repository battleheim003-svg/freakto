"""
Freakto v6.1.0 - Regime-Split Gate Matrix

Research-only matrix layer that combines live-known regime labels with
candidate gates, side, symbol and cost-adjusted outcomes.

Safety:
- Does not place orders.
- Does not create paper trades.
- Does not use future outcome columns to build filters; returns/target/stop/MFE/MAE are used only for evaluation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from engine.research_utils import (
    RESEARCH_DIR,
    RETURN_COLUMNS,
    add_cost_columns,
    apply_gate,
    directional_complete,
    load_backtest_df,
    metric_summary,
    run_id,
    safe_float,
    save_dataframe_csv,
    standard_gate_specs,
    utc_now_iso,
    write_json,
    write_text,
)

VERSION = "v6.1.0"
SUITE_DIR = RESEARCH_DIR / "v6_suite"

PRIMARY_GATES = {
    "VOLUME_SCORE_GE_10",
    "QUALITY_STRUCTURE_RISK_MEDIUM",
    "RISK_MEDIUM",
    "HISTORICAL_EDGE_SCORE_GE_1",
    "STRUCTURE_SCORE_GE_10",
    "SCORE_GE_80",
    "DOGE_SHORT_WATCH",
    "BNB_LONG_SCORE_GE_60",
}

AVOID_REGIME_NAMES = {"UNKNOWN", "SIDEWAYS"}


def _norm(value: Any, default: str = "UNKNOWN") -> str:
    txt = str(value or "").strip().upper()
    return txt if txt else default


def _gate_specs(include_all: bool = True) -> List[Dict[str, Any]]:
    specs = standard_gate_specs()
    if include_all:
        return specs
    return [s for s in specs if s.get("name") in PRIMARY_GATES]


def _quality_verdict(metrics: Dict[str, Any], *, min_samples: int, candidate_min_samples: int) -> str:
    n = int(metrics.get("samples", 0) or 0)
    avg = safe_float(metrics.get("avg_return_pct"), 0.0) or 0.0
    win = safe_float(metrics.get("win_rate"), 0.0) or 0.0
    t1 = safe_float(metrics.get("target_1_hit_rate"), 0.0) or 0.0
    stop = safe_float(metrics.get("stop_hit_rate"), 0.0) or 0.0
    ratio = safe_float(metrics.get("mfe_mae_ratio"), 0.0) or 0.0

    if n < min_samples:
        return "LOW_SAMPLE"
    if avg <= 0:
        if n >= candidate_min_samples and (avg <= -0.25 or win < 42 or stop > t1 + 12):
            return "AVOID_CANDIDATE"
        return "NET_NEGATIVE_AFTER_COST"
    if n < candidate_min_samples:
        return "POSITIVE_LOW_SAMPLE"
    if win >= 50 and ratio >= 1 and t1 >= stop:
        return "REGIME_RESEARCH_CANDIDATE"
    return "POSITIVE_BUT_FRAGILE"


def _avoid_verdict(metrics: Dict[str, Any], *, min_samples: int) -> str:
    n = int(metrics.get("samples", 0) or 0)
    avg = safe_float(metrics.get("avg_return_pct"), 0.0) or 0.0
    win = safe_float(metrics.get("win_rate"), 0.0) or 0.0
    t1 = safe_float(metrics.get("target_1_hit_rate"), 0.0) or 0.0
    stop = safe_float(metrics.get("stop_hit_rate"), 0.0) or 0.0
    if n < min_samples:
        return "LOW_SAMPLE"
    if avg <= -0.50 or stop > t1 + 15:
        return "AVOID"
    if avg < 0 or win < 40:
        return "WEAK_NEGATIVE"
    return "NOT_AVOID"


def _score_row(metrics: Dict[str, Any]) -> float:
    avg = safe_float(metrics.get("avg_return_pct"), 0.0) or 0.0
    ratio = safe_float(metrics.get("mfe_mae_ratio"), 0.0) or 0.0
    win = safe_float(metrics.get("win_rate"), 0.0) or 0.0
    t1 = safe_float(metrics.get("target_1_hit_rate"), 0.0) or 0.0
    stop = safe_float(metrics.get("stop_hit_rate"), 0.0) or 0.0
    ci_low = safe_float(metrics.get("confidence_95_low_pct"), 0.0) or 0.0
    # Conservative score: reward net edge and quality, penalize stop excess and weak CI.
    return round(avg + ratio * 0.10 + (win - 50.0) * 0.01 + (t1 - stop) * 0.005 + min(ci_low, 0.0) * 0.15, 4)


def _filters_to_label(filters: Dict[str, Any]) -> str:
    parts = []
    for k, v in filters.items():
        parts.append(f"{k}={v}")
    return ", ".join(parts)


def _build_matrix_rows(
    df: pd.DataFrame,
    *,
    horizon: str,
    fee_bps: float,
    slippage_bps: float,
    min_samples: int,
    candidate_min_samples: int,
    include_all_gates: bool,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    regimes = sorted({_norm(x) for x in df.get("regime_label", pd.Series(dtype=str)).dropna().tolist()}) or ["UNKNOWN"]
    gates = _gate_specs(include_all=include_all_gates)
    sides = sorted({_norm(x) for x in df.get("side", pd.Series(dtype=str)).dropna().tolist() if _norm(x) in {"LONG", "SHORT"}})
    symbols = sorted({str(x).strip().upper() for x in df.get("symbol", pd.Series(dtype=str)).dropna().tolist() if str(x).strip()})

    regime_gate_rows: List[Dict[str, Any]] = []
    regime_gate_side_rows: List[Dict[str, Any]] = []
    regime_side_rows: List[Dict[str, Any]] = []
    regime_symbol_rows: List[Dict[str, Any]] = []
    regime_symbol_side_rows: List[Dict[str, Any]] = []

    for regime in regimes:
        rdf = df[df["regime_label"].astype(str).str.upper().fillna("UNKNOWN") == regime].copy()
        for gate in gates:
            gdf = apply_gate(rdf, gate["filters"])
            met = metric_summary(gdf, horizon=horizon, use_net=True, fee_bps=fee_bps, slippage_bps=slippage_bps)
            row = {
                "regime": regime,
                "gate": gate["name"],
                "gate_family": gate.get("family", ""),
                "filters": json.dumps(gate.get("filters", {}), ensure_ascii=False),
                "samples": met["samples"],
                "net_avg_pct": met["avg_return_pct"],
                "win_rate": met["win_rate"],
                "target_1_hit_rate": met["target_1_hit_rate"],
                "stop_hit_rate": met["stop_hit_rate"],
                "mfe_mae_ratio": met["mfe_mae_ratio"],
                "ci95_low_pct": met["confidence_95_low_pct"],
                "ci95_high_pct": met["confidence_95_high_pct"],
                "score": _score_row(met),
                "verdict": _quality_verdict(met, min_samples=min_samples, candidate_min_samples=candidate_min_samples),
            }
            regime_gate_rows.append(row)
            for side in sides:
                sgdf = gdf[gdf["side"].astype(str).str.upper() == side].copy()
                smet = metric_summary(sgdf, horizon=horizon, use_net=True, fee_bps=fee_bps, slippage_bps=slippage_bps)
                if smet["samples"] == 0:
                    continue
                regime_gate_side_rows.append({
                    "regime": regime,
                    "gate": gate["name"],
                    "side": side,
                    "gate_family": gate.get("family", ""),
                    "filters": json.dumps({**gate.get("filters", {}), "side": side}, ensure_ascii=False),
                    "samples": smet["samples"],
                    "net_avg_pct": smet["avg_return_pct"],
                    "win_rate": smet["win_rate"],
                    "target_1_hit_rate": smet["target_1_hit_rate"],
                    "stop_hit_rate": smet["stop_hit_rate"],
                    "mfe_mae_ratio": smet["mfe_mae_ratio"],
                    "ci95_low_pct": smet["confidence_95_low_pct"],
                    "ci95_high_pct": smet["confidence_95_high_pct"],
                    "score": _score_row(smet),
                    "verdict": _quality_verdict(smet, min_samples=min_samples, candidate_min_samples=candidate_min_samples),
                })

        for side in sides:
            sdf = rdf[rdf["side"].astype(str).str.upper() == side].copy()
            met = metric_summary(sdf, horizon=horizon, use_net=True, fee_bps=fee_bps, slippage_bps=slippage_bps)
            if met["samples"] == 0:
                continue
            regime_side_rows.append({
                "regime": regime,
                "side": side,
                "samples": met["samples"],
                "net_avg_pct": met["avg_return_pct"],
                "win_rate": met["win_rate"],
                "target_1_hit_rate": met["target_1_hit_rate"],
                "stop_hit_rate": met["stop_hit_rate"],
                "mfe_mae_ratio": met["mfe_mae_ratio"],
                "score": _score_row(met),
                "verdict": _quality_verdict(met, min_samples=min_samples, candidate_min_samples=candidate_min_samples),
            })

        for symbol in symbols:
            symdf = rdf[rdf["symbol"].astype(str).str.upper() == symbol].copy()
            met = metric_summary(symdf, horizon=horizon, use_net=True, fee_bps=fee_bps, slippage_bps=slippage_bps)
            if met["samples"] == 0:
                continue
            regime_symbol_rows.append({
                "regime": regime,
                "symbol": symbol,
                "samples": met["samples"],
                "net_avg_pct": met["avg_return_pct"],
                "win_rate": met["win_rate"],
                "target_1_hit_rate": met["target_1_hit_rate"],
                "stop_hit_rate": met["stop_hit_rate"],
                "mfe_mae_ratio": met["mfe_mae_ratio"],
                "score": _score_row(met),
                "verdict": _quality_verdict(met, min_samples=min_samples, candidate_min_samples=candidate_min_samples),
            })
            for side in sides:
                ssdf = symdf[symdf["side"].astype(str).str.upper() == side].copy()
                smet = metric_summary(ssdf, horizon=horizon, use_net=True, fee_bps=fee_bps, slippage_bps=slippage_bps)
                if smet["samples"] == 0:
                    continue
                regime_symbol_side_rows.append({
                    "regime": regime,
                    "symbol": symbol,
                    "side": side,
                    "samples": smet["samples"],
                    "net_avg_pct": smet["avg_return_pct"],
                    "win_rate": smet["win_rate"],
                    "target_1_hit_rate": smet["target_1_hit_rate"],
                    "stop_hit_rate": smet["stop_hit_rate"],
                    "mfe_mae_ratio": smet["mfe_mae_ratio"],
                    "score": _score_row(smet),
                    "verdict": _quality_verdict(smet, min_samples=min_samples, candidate_min_samples=candidate_min_samples),
                })

    return regime_gate_rows, regime_gate_side_rows, regime_side_rows, regime_symbol_rows, regime_symbol_side_rows


def _sort_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    preferred = {
        "REGIME_RESEARCH_CANDIDATE": 5,
        "POSITIVE_BUT_FRAGILE": 4,
        "POSITIVE_LOW_SAMPLE": 3,
        "NET_NEGATIVE_AFTER_COST": 2,
        "AVOID_CANDIDATE": 1,
        "LOW_SAMPLE": 0,
    }
    return sorted(rows, key=lambda r: (preferred.get(r.get("verdict"), 0), r.get("score", 0), r.get("net_avg_pct", 0), r.get("samples", 0)), reverse=True)


def _avoid_regimes(df: pd.DataFrame, *, horizon: str, fee_bps: float, slippage_bps: float, min_samples: int) -> List[Dict[str, Any]]:
    rows = []
    for regime, g in df.groupby(df["regime_label"].astype(str).str.upper().fillna("UNKNOWN")):
        met = metric_summary(g, horizon=horizon, use_net=True, fee_bps=fee_bps, slippage_bps=slippage_bps)
        verdict = _avoid_verdict(met, min_samples=min_samples)
        if regime in AVOID_REGIME_NAMES and met["avg_return_pct"] < 0:
            verdict = "AVOID" if met["samples"] >= min_samples else "AVOID_WATCH_LOW_SAMPLE"
        rows.append({
            "regime": regime,
            "samples": met["samples"],
            "net_avg_pct": met["avg_return_pct"],
            "win_rate": met["win_rate"],
            "target_1_hit_rate": met["target_1_hit_rate"],
            "stop_hit_rate": met["stop_hit_rate"],
            "mfe_mae_ratio": met["mfe_mae_ratio"],
            "verdict": verdict,
        })
    severity = {"AVOID": 3, "AVOID_WATCH_LOW_SAMPLE": 2, "WEAK_NEGATIVE": 1, "LOW_SAMPLE": 0, "NOT_AVOID": 0}
    return sorted(rows, key=lambda r: (severity.get(r.get("verdict"), 0), -r.get("net_avg_pct", 0), r.get("samples", 0)), reverse=True)


def _shadow_proposals(regime_gate: List[Dict[str, Any]], regime_gate_side: List[Dict[str, Any]], *, candidate_min_samples: int) -> List[Dict[str, Any]]:
    proposals: List[Dict[str, Any]] = []
    by_name = {s["name"]: s for s in standard_gate_specs()}
    source_rows = [r for r in regime_gate if r.get("verdict") == "REGIME_RESEARCH_CANDIDATE"]
    source_rows += [r for r in regime_gate_side if r.get("verdict") == "REGIME_RESEARCH_CANDIDATE"]
    # If no full candidate exists, add positive fragile rows as watch-only proposals.
    if not source_rows:
        source_rows = [r for r in regime_gate if r.get("verdict") in {"POSITIVE_BUT_FRAGILE", "POSITIVE_LOW_SAMPLE"} and r.get("samples", 0) >= max(10, candidate_min_samples // 2)]
    seen = set()
    for row in _sort_rows(source_rows)[:8]:
        spec = by_name.get(row.get("gate"), {"filters": {}})
        filters = dict(spec.get("filters", {}))
        filters["regime_label"] = row.get("regime")
        if row.get("side"):
            filters["side"] = row.get("side")
        key = json.dumps(filters, sort_keys=True, ensure_ascii=False)
        if key in seen:
            continue
        seen.add(key)
        proposals.append({
            "proposal_name": "REGIME_" + str(row.get("regime", "UNKNOWN")) + "__" + str(row.get("gate", "GATE")) + ("__" + str(row.get("side")) if row.get("side") else ""),
            "mode": "SHADOW_ONLY",
            "filters": filters,
            "filters_label": _filters_to_label(filters),
            "samples": row.get("samples"),
            "net_avg_pct": row.get("net_avg_pct"),
            "win_rate": row.get("win_rate"),
            "target_1_hit_rate": row.get("target_1_hit_rate"),
            "stop_hit_rate": row.get("stop_hit_rate"),
            "mfe_mae_ratio": row.get("mfe_mae_ratio"),
            "source_verdict": row.get("verdict"),
            "note": "این پیشنهاد فقط برای Shadow/Forward است و نباید Paper/Live را فعال کند.",
        })
    return proposals


def _recommendations(report: Dict[str, Any]) -> List[str]:
    recs = []
    cands = report.get("regime_candidates", [])
    avoid = [r for r in report.get("avoid_regimes", []) if str(r.get("verdict", "")).startswith("AVOID")]
    if cands:
        best = cands[0]
        recs.append(f"بهترین ترکیب Regime/Gate فعلی: {best.get('regime')} × {best.get('gate')} با net={best.get('net_avg_pct')}% و n={best.get('samples')}.")
        recs.append("این ترکیب فقط باید در Shadow Forward رصد شود؛ هنوز Paper/Live مجاز نیست.")
    else:
        recs.append("هیچ ترکیب Regime/Gate با sample و کیفیت کافی پیدا نشد؛ روی feature/gate جدید یا بهبود Regime Engine تمرکز کن.")
    if avoid:
        names = ", ".join([str(r.get("regime")) for r in avoid[:4]])
        recs.append(f"Regimeهای خام مشکوک برای Avoid/Watch بدون Gate: {names}.")
    recs.append("horizon اصلی فعلاً 24h بماند؛ 4h و 12h قبلاً بعد از cost/stability candidate ندادند.")
    return recs


def run_regime_gate_matrix(
    *,
    horizon: str = "24h",
    min_samples: int = 10,
    candidate_min_samples: int = 30,
    fee_bps: float = 10.0,
    slippage_bps: float = 5.0,
    include_all_gates: bool = True,
) -> Dict[str, Any]:
    rid = run_id("regime_gate_matrix")
    df = directional_complete(load_backtest_df())
    if df.empty:
        return {
            "run_id": rid,
            "generated_utc": utc_now_iso(),
            "version": VERSION,
            "status": "NO_BACKTEST_DATA",
            "horizon": horizon,
            "min_samples": min_samples,
            "candidate_min_samples": candidate_min_samples,
            "fee_bps": fee_bps,
            "slippage_bps": slippage_bps,
            "baseline_net": {"samples": 0, "avg_return_pct": 0.0, "win_rate": 0.0, "target_1_hit_rate": 0.0, "stop_hit_rate": 0.0},
            "regimes_seen": [],
            "gates_tested": 0,
            "candidate_count": 0,
            "regime_candidates": [],
            "regime_gate_side_candidates": [],
            "top_regime_gate": [],
            "top_regime_gate_side": [],
            "top_regime_side": [],
            "top_regime_symbol": [],
            "avoid_regimes": [],
            "shadow_proposals": [],
            "blockers": ["هیچ historical_backtest_evaluations کامل برای ساخت Regime-Gate Matrix پیدا نشد."],
            "warnings": [],
            "recommendations": [],
        }
    if "regime_label" not in df.columns:
        df["regime_label"] = "UNKNOWN"
    df["regime_label"] = df["regime_label"].apply(_norm)
    baseline = metric_summary(df, horizon=horizon, use_net=True, fee_bps=fee_bps, slippage_bps=slippage_bps)
    regime_gate, regime_gate_side, regime_side, regime_symbol, regime_symbol_side = _build_matrix_rows(
        df,
        horizon=horizon,
        fee_bps=fee_bps,
        slippage_bps=slippage_bps,
        min_samples=min_samples,
        candidate_min_samples=candidate_min_samples,
        include_all_gates=include_all_gates,
    )
    regime_gate = _sort_rows(regime_gate)
    regime_gate_side = _sort_rows(regime_gate_side)
    regime_side = _sort_rows(regime_side)
    regime_symbol = _sort_rows(regime_symbol)
    regime_symbol_side = _sort_rows(regime_symbol_side)
    avoid = _avoid_regimes(df, horizon=horizon, fee_bps=fee_bps, slippage_bps=slippage_bps, min_samples=min_samples)
    candidates = [r for r in regime_gate if r.get("verdict") == "REGIME_RESEARCH_CANDIDATE"]
    side_candidates = [r for r in regime_gate_side if r.get("verdict") == "REGIME_RESEARCH_CANDIDATE"]
    positive_watch = [r for r in regime_gate if r.get("verdict") in {"POSITIVE_BUT_FRAGILE", "POSITIVE_LOW_SAMPLE"}]
    proposals = _shadow_proposals(regime_gate, regime_gate_side, candidate_min_samples=candidate_min_samples)

    blockers = []
    if not candidates and not side_candidates:
        blockers.append("هیچ ترکیب Regime/Gate با sample کافی و معیارهای کیفیت کامل پیدا نشد.")
    if baseline.get("avg_return_pct", 0) <= 0:
        blockers.append("Baseline net return کلی هنوز مثبت نیست.")
    status = "REGIME_GATE_CANDIDATES_FOUND" if candidates or side_candidates else "REGIME_GATE_RESEARCH_BUILDING"
    report = {
        "run_id": rid,
        "generated_utc": utc_now_iso(),
        "version": VERSION,
        "status": status,
        "horizon": horizon,
        "min_samples": min_samples,
        "candidate_min_samples": candidate_min_samples,
        "fee_bps": fee_bps,
        "slippage_bps": slippage_bps,
        "baseline_net": baseline,
        "regimes_seen": sorted(df["regime_label"].astype(str).str.upper().unique().tolist()),
        "gates_tested": len(_gate_specs(include_all=include_all_gates)),
        "regime_gate_rows": len(regime_gate),
        "regime_gate_side_rows": len(regime_gate_side),
        "candidate_count": len(candidates) + len(side_candidates),
        "regime_candidates": candidates[:20],
        "regime_gate_side_candidates": side_candidates[:20],
        "positive_watchlist": positive_watch[:20],
        "top_regime_gate": regime_gate[:20],
        "top_regime_gate_side": regime_gate_side[:20],
        "top_regime_side": regime_side[:20],
        "top_regime_symbol": regime_symbol[:20],
        "top_regime_symbol_side": regime_symbol_side[:20],
        "avoid_regimes": avoid,
        "shadow_proposals": proposals,
        "blockers": blockers,
        "recommendations": [],
        "warnings": [
            "Regime label باید در Forward هم ثبت و validate شود؛ Backtest به تنهایی کافی نیست.",
            "گروه‌های کم‌نمونه می‌توانند overfit باشند؛ sample و window stability باید رشد کند.",
            "این ماژول فقط از داده‌های live-known برای فیلتر استفاده می‌کند؛ outcomeها فقط برای ارزیابی‌اند.",
        ],
    }
    report["recommendations"] = _recommendations(report)
    return report


def format_regime_gate_matrix_console(report: Dict[str, Any], *, compact: bool = True) -> str:
    sep = "=" * 110
    lines = [sep, f"🧬 Freakto Regime-Split Gate Matrix {VERSION}", sep]
    lines.append(f"Status: {report.get('status', 'UNKNOWN')}")
    lines.append(f"Run ID: {report.get('run_id', '')}")
    lines.append(f"Horizon: {report.get('horizon', '24h')}")
    lines.append(f"Min Samples: {report.get('min_samples')} | Candidate Min Samples: {report.get('candidate_min_samples')}")
    base = report.get("baseline_net", {})
    if base:
        lines.append(f"Baseline Net: samples={base.get('samples')} | avg={base.get('avg_return_pct')}% | win={base.get('win_rate')}% | T1={base.get('target_1_hit_rate')}% | Stop={base.get('stop_hit_rate')}%")
    lines.append(f"Regimes Seen: {', '.join(report.get('regimes_seen', []))}")
    lines.append(f"Gates Tested: {report.get('gates_tested')} | Candidates: {report.get('candidate_count')}")

    def add_rows(title: str, rows: List[Dict[str, Any]], keys: List[str], limit: int) -> None:
        lines.append(f"\n{title}:")
        if not rows:
            lines.append("- هیچ داده‌ای موجود نیست.")
            return
        for r in rows[:limit]:
            head = []
            if r.get("regime"):
                head.append(str(r.get("regime")))
            if r.get("gate"):
                head.append(str(r.get("gate")))
            if r.get("side"):
                head.append(str(r.get("side")))
            if r.get("symbol"):
                head.append(str(r.get("symbol")))
            label = " × ".join(head) if head else str(r.get("name", "row"))
            bits = [f"{k}={r.get(k)}" for k in keys]
            lines.append(f"- {label}: " + " | ".join(bits))

    add_rows("Regime Candidates", report.get("regime_candidates", []) + report.get("regime_gate_side_candidates", []), ["verdict", "samples", "net_avg_pct", "win_rate", "target_1_hit_rate", "stop_hit_rate", "mfe_mae_ratio", "score"], 8 if compact else 25)
    add_rows("Top Regime × Gate", report.get("top_regime_gate", []), ["verdict", "samples", "net_avg_pct", "win_rate", "target_1_hit_rate", "stop_hit_rate", "mfe_mae_ratio", "score"], 10 if compact else 30)
    add_rows("Top Regime × Gate × Side", report.get("top_regime_gate_side", []), ["verdict", "samples", "net_avg_pct", "win_rate", "target_1_hit_rate", "stop_hit_rate", "mfe_mae_ratio", "score"], 10 if compact else 30)
    add_rows("Top Regime × Side", report.get("top_regime_side", []), ["verdict", "samples", "net_avg_pct", "win_rate", "target_1_hit_rate", "stop_hit_rate", "mfe_mae_ratio", "score"], 8 if compact else 20)
    add_rows("Top Regime × Symbol", report.get("top_regime_symbol", []), ["verdict", "samples", "net_avg_pct", "win_rate", "target_1_hit_rate", "stop_hit_rate", "mfe_mae_ratio", "score"], 8 if compact else 20)

    lines.append("\nAvoid Regimes:")
    avoid = report.get("avoid_regimes", [])
    for r in avoid[:8 if compact else 20]:
        lines.append(f"- {r.get('regime')}: {r.get('verdict')} | n={r.get('samples')} | net={r.get('net_avg_pct')}% | win={r.get('win_rate')}% | T1={r.get('target_1_hit_rate')}% | Stop={r.get('stop_hit_rate')}%")

    lines.append("\nShadow Proposals:")
    proposals = report.get("shadow_proposals", [])
    if not proposals:
        lines.append("- فعلاً proposal قابل اتکا برای Shadow اضافه نشد.")
    for p in proposals[:8 if compact else 20]:
        lines.append(f"- {p.get('proposal_name')}: mode={p.get('mode')} | n={p.get('samples')} | net={p.get('net_avg_pct')}% | filters={p.get('filters_label')}")

    if report.get("blockers"):
        lines.append("\nBlockers:")
        lines.extend([f"⛔ {b}" for b in report.get("blockers", [])])
    if report.get("recommendations"):
        lines.append("\nRecommendations:")
        lines.extend([f"→ {r}" for r in report.get("recommendations", [])])
    if report.get("warnings"):
        lines.append("\nWarnings:")
        lines.extend([f"⚠️ {w}" for w in report.get("warnings", [])])
    lines.append(sep)
    return "\n".join(lines)


def save_regime_gate_matrix(report: Dict[str, Any]) -> Tuple[Path, Path, Path, Path, Path, Path]:
    SUITE_DIR.mkdir(parents=True, exist_ok=True)
    rid = report.get("run_id", run_id("regime_gate_matrix"))
    json_path = SUITE_DIR / f"regime_gate_matrix_{rid}.json"
    md_path = SUITE_DIR / f"regime_gate_matrix_report_{rid}.md"
    rg_csv = SUITE_DIR / f"regime_gate_matrix_results_{rid}.csv"
    rgs_csv = SUITE_DIR / f"regime_gate_side_matrix_results_{rid}.csv"
    avoid_csv = SUITE_DIR / f"regime_avoid_candidates_{rid}.csv"
    proposal_path = SUITE_DIR / f"regime_shadow_proposals_{rid}.json"
    write_json(json_path, report)
    write_text(md_path, format_regime_gate_matrix_console(report, compact=False))
    save_dataframe_csv(rg_csv, pd.DataFrame(report.get("top_regime_gate", []) + report.get("positive_watchlist", [])))
    save_dataframe_csv(rgs_csv, pd.DataFrame(report.get("top_regime_gate_side", [])))
    save_dataframe_csv(avoid_csv, pd.DataFrame(report.get("avoid_regimes", [])))
    write_json(proposal_path, {"run_id": rid, "generated_utc": utc_now_iso(), "mode": "SHADOW_ONLY", "proposals": report.get("shadow_proposals", [])})
    return json_path, md_path, rg_csv, rgs_csv, avoid_csv, proposal_path
