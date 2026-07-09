"""
Freakto v6.3.0 - Research Robustness & Forward Regime Intelligence Suite

Implements the 11 requested improvement areas in research-only mode:
1) Gate robustness / multiple-testing guard / walk-forward / embargo proxy
2) Decision layer: meta-labeling, ensemble, explainability
3) Data enrichment readiness: on-chain, derivatives, microstructure, regime
4) Realistic simulation: fee/slippage and cross-exchange validation
5) Infrastructure/observability: SQLite, static dashboard, pipeline health
6) Stricter readiness: statistical significance, regime coverage, BTC beta
7) Paper/Micro-live preparation: position sizing lab + airdrop gate/shadow concept

No function here places live orders or creates paper trades.
"""
from __future__ import annotations

import json
import math
import os
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, roc_auc_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
except Exception:  # pragma: no cover
    LogisticRegression = None
    accuracy_score = None
    roc_auc_score = None
    StandardScaler = None
    Pipeline = None

from engine.research_utils import (
    AIRDROP_WATCHLIST,
    BACKTEST_EVALS,
    DECISIONS,
    FORWARD_EVALS,
    FORWARD_RUNS,
    LOG_DIR,
    RESEARCH_DIR,
    RETURN_COLUMNS,
    SHADOW_SIGNALS,
    add_cost_columns,
    apply_gate,
    compact_table,
    directional_complete,
    load_backtest_df,
    load_decisions_df,
    load_forward_eval_df,
    metric_summary,
    pct,
    read_csv_df,
    run_id,
    safe_float,
    safe_int,
    save_dataframe_csv,
    split_time_windows,
    standard_gate_specs,
    time_ordered,
    utc_now_iso,
    write_json,
    write_text,
)

VERSION = "v6.3.0"
SUITE_DIR = RESEARCH_DIR / "v6_suite"


def _verdict_for_metrics(m: Dict[str, Any], min_samples: int = 30, require_net: bool = True) -> str:
    avg = safe_float(m.get("avg_return_pct"), 0.0) or 0.0
    n = safe_int(m.get("samples"), 0)
    if n < min_samples:
        return "LOW_SAMPLE"
    if avg <= 0:
        return "NEGATIVE_OR_FLAT"
    if m.get("mfe_mae_ratio", 0) >= 1 and m.get("win_rate", 0) >= 50 and m.get("target_1_hit_rate", 0) >= m.get("stop_hit_rate", 0):
        return "RESEARCH_CANDIDATE"
    return "POSITIVE_BUT_FRAGILE"


# 1) Gate Robustness / Overfitting Guard

def run_gate_robustness(
    *,
    horizon: str = "24h",
    min_samples: int = 30,
    windows: int = 5,
    embargo_rows: int = 2,
    fee_bps: float = 10.0,
    slippage_bps: float = 5.0,
) -> Dict[str, Any]:
    df = directional_complete(load_backtest_df())
    rid = run_id("gate_robustness")
    if df.empty:
        return {
            "run_id": rid,
            "generated_utc": utc_now_iso(),
            "status": "NO_BACKTEST_DATA",
            "results": [],
            "blockers": ["هیچ دیتای backtest کامل برای robust validation وجود ندارد."],
            "warnings": [],
        }

    wdf = time_ordered(df)
    chunks = split_time_windows(wdf, n_windows=windows)
    gates = standard_gate_specs()
    baseline_gross = metric_summary(wdf, horizon=horizon, use_net=False)
    baseline_net = metric_summary(wdf, horizon=horizon, use_net=True, fee_bps=fee_bps, slippage_bps=slippage_bps)
    results: List[Dict[str, Any]] = []

    for gate in gates:
        full = apply_gate(wdf, gate["filters"])
        full_gross = metric_summary(full, horizon=horizon, use_net=False)
        full_net = metric_summary(full, horizon=horizon, use_net=True, fee_bps=fee_bps, slippage_bps=slippage_bps)
        window_rows = []
        positive_windows = 0
        valid_windows = 0
        min_net_avg = None
        for idx, chunk in enumerate(chunks, start=1):
            # Embargo proxy: remove boundary rows so overlapping outcomes do not leak across windows.
            c = chunk.copy()
            if len(c) > 2 * embargo_rows:
                c = c.iloc[embargo_rows: len(c) - embargo_rows].copy()
            sample = apply_gate(c, gate["filters"])
            met = metric_summary(sample, horizon=horizon, use_net=True, fee_bps=fee_bps, slippage_bps=slippage_bps)
            n = met["samples"]
            if n > 0:
                valid_windows += 1
                avg = met["avg_return_pct"]
                min_net_avg = avg if min_net_avg is None else min(min_net_avg, avg)
                if avg > 0:
                    positive_windows += 1
            window_rows.append({"window": idx, "samples": n, "net_avg": met["avg_return_pct"], "win": met["win_rate"]})
        stability = round(positive_windows / valid_windows * 100, 2) if valid_windows else 0.0
        # Lightweight multiple testing penalty proxy. It is deliberately conservative.
        n = max(full_net["samples"], 1)
        trials = max(len(gates), 1)
        multiple_testing_penalty = round(0.10 * math.sqrt(math.log(trials + 1) / math.sqrt(n)), 4)
        stability_penalty = round(max(0.0, 50.0 - stability) / 100.0, 4)
        robust_score = round(full_net["avg_return_pct"] + full_net["mfe_mae_ratio"] * 0.05 + (stability / 100.0) * 0.20 - multiple_testing_penalty - stability_penalty, 4)
        if full_net["samples"] < min_samples:
            verdict = "LOW_SAMPLE"
        elif full_net["avg_return_pct"] <= 0:
            verdict = "NET_NEGATIVE_AFTER_COST"
        elif stability >= 60 and robust_score > 0 and full_net["confidence_95_low_pct"] > -0.75:
            verdict = "ROBUST_RESEARCH_CANDIDATE"
        elif stability >= 40:
            verdict = "FRAGILE_POSITIVE"
        else:
            verdict = "OVERFIT_RISK"
        results.append({
            "gate": gate["name"],
            "family": gate["family"],
            "filters": gate["filters"],
            "samples": full_net["samples"],
            "gross_avg_pct": full_gross["avg_return_pct"],
            "net_avg_pct": full_net["avg_return_pct"],
            "net_win_rate": full_net["win_rate"],
            "net_t_stat": full_net["t_stat"],
            "net_ci_low": full_net["confidence_95_low_pct"],
            "net_ci_high": full_net["confidence_95_high_pct"],
            "target_1_hit_rate": full_net["target_1_hit_rate"],
            "stop_hit_rate": full_net["stop_hit_rate"],
            "mfe_mae_ratio": full_net["mfe_mae_ratio"],
            "valid_windows": valid_windows,
            "positive_windows": positive_windows,
            "stability_pct": stability,
            "min_window_net_avg_pct": round(min_net_avg or 0.0, 4),
            "multiple_testing_penalty": multiple_testing_penalty,
            "stability_penalty": stability_penalty,
            "robust_score": robust_score,
            "verdict": verdict,
            "window_results": window_rows,
        })

    results = sorted(results, key=lambda r: (r["verdict"] == "ROBUST_RESEARCH_CANDIDATE", r["robust_score"], r["net_avg_pct"], r["samples"]), reverse=True)
    robust_count = sum(1 for r in results if r["verdict"] == "ROBUST_RESEARCH_CANDIDATE")
    fragile_count = sum(1 for r in results if r["verdict"] == "FRAGILE_POSITIVE")
    warnings = [
        "Multiple-testing penalty اینجا یک تخمین محافظه‌کارانه است؛ جایگزین قطعی PBO آکادمیک نیست.",
        "Embargo به‌صورت row-based اعمال شده تا با ساختار فعلی CSV سازگار بماند.",
    ]
    blockers = []
    if robust_count == 0:
        blockers.append("هیچ Gate بعد از cost و stability به ROBUST_RESEARCH_CANDIDATE نرسید.")
    return {
        "run_id": rid,
        "generated_utc": utc_now_iso(),
        "status": "ROBUST_GATES_FOUND" if robust_count else "ROBUSTNESS_BUILDING",
        "horizon": horizon,
        "min_samples": min_samples,
        "windows": windows,
        "embargo_rows": embargo_rows,
        "fee_bps": fee_bps,
        "slippage_bps": slippage_bps,
        "baseline_gross": baseline_gross,
        "baseline_net": baseline_net,
        "gates_tested": len(gates),
        "robust_candidates": robust_count,
        "fragile_positive": fragile_count,
        "results": results,
        "top_results": results[:12],
        "blockers": blockers,
        "warnings": warnings,
        "recommendations": _recommend_gate_robustness(results),
    }


def _recommend_gate_robustness(results: List[Dict[str, Any]]) -> List[str]:
    recs = []
    robust = [r for r in results if r["verdict"] == "ROBUST_RESEARCH_CANDIDATE"]
    fragile = [r for r in results if r["verdict"] == "FRAGILE_POSITIVE"]
    if robust:
        best = robust[0]
        recs.append(f"بهترین Gate robust فعلی: {best['gate']} با net_avg={best['net_avg_pct']}% و stability={best['stability_pct']}%.")
        recs.append("این Gate فقط باید در Shadow/Forward ادامه پیدا کند؛ هنوز Paper/Live مجاز نیست.")
    elif fragile:
        best = fragile[0]
        recs.append(f"بهترین Gate مثبت ولی fragile: {best['gate']}؛ قبل از هر استفاده باید sample و window stability بیشتر شود.")
    else:
        recs.append("Gateهای فعلی بعد از جریمه هزینه و stability کافی نیستند؛ باید feature/gate جدید یا regime split بررسی شود.")
    return recs


# 2) Decision layer: meta-labeling, ensemble, explainability

def run_meta_labeling(*, horizon: str = "24h", min_samples: int = 120) -> Dict[str, Any]:
    df = directional_complete(load_backtest_df())
    rid = run_id("meta_label")
    if df.empty or len(df) < min_samples:
        return {
            "run_id": rid, "generated_utc": utc_now_iso(), "status": "LOW_SAMPLE_META_LABELING",
            "samples": len(df), "blockers": [f"برای meta-labeling حداقل {min_samples} نمونه لازم است."], "warnings": [], "top_features": []
        }
    col = RETURN_COLUMNS.get(horizon, "return_after_24h_pct")
    if col not in df.columns:
        return {"run_id": rid, "generated_utc": utc_now_iso(), "status": "MISSING_RETURN_COLUMN", "blockers": [f"ستون {col} پیدا نشد."], "warnings": [], "top_features": []}
    features = ["score", "trend_score", "momentum_score", "volume_score", "structure_score", "historical_edge_score", "long_score", "short_score"]
    Xdf = df[features].apply(pd.to_numeric, errors="coerce").fillna(0)
    y = (pd.to_numeric(df[col], errors="coerce").fillna(0) > 0).astype(int)
    # Time split to preserve chronology.
    ordered = time_ordered(df).reset_index(drop=True)
    Xdf = ordered[features].apply(pd.to_numeric, errors="coerce").fillna(0)
    y = (pd.to_numeric(ordered[col], errors="coerce").fillna(0) > 0).astype(int)
    split = int(len(ordered) * 0.70)
    X_train, X_test = Xdf.iloc[:split], Xdf.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    if len(set(y_train.tolist())) < 2 or len(set(y_test.tolist())) < 2 or LogisticRegression is None:
        # Fallback correlation ranking.
        corrs = []
        for f in features:
            try:
                corr = float(np.corrcoef(Xdf[f], y)[0, 1])
                if math.isnan(corr):
                    corr = 0.0
            except Exception:
                corr = 0.0
            corrs.append({"feature": f, "weight": round(corr, 4), "abs_weight": round(abs(corr), 4)})
        corrs = sorted(corrs, key=lambda x: x["abs_weight"], reverse=True)
        return {
            "run_id": rid, "generated_utc": utc_now_iso(), "status": "META_LABEL_CORRELATION_FALLBACK",
            "samples": len(df), "train_samples": len(X_train), "test_samples": len(X_test), "accuracy": 0.0, "auc": 0.0,
            "top_features": corrs[:8], "blockers": [], "warnings": ["sklearn یا کلاس‌بندی دوطرفه کافی نبود؛ fallback correlation استفاده شد."],
            "recommendations": ["Meta-labeling هنوز فقط research است و نباید actionability را تغییر دهد."],
        }
    model = Pipeline([("scale", StandardScaler()), ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))])
    model.fit(X_train, y_train)
    prob = model.predict_proba(X_test)[:, 1]
    pred = (prob >= 0.5).astype(int)
    acc = float(accuracy_score(y_test, pred)) if accuracy_score else 0.0
    try:
        auc = float(roc_auc_score(y_test, prob)) if roc_auc_score else 0.0
    except Exception:
        auc = 0.0
    coefs = model.named_steps["clf"].coef_[0]
    feat_rows = sorted([
        {"feature": f, "weight": round(float(w), 4), "abs_weight": round(abs(float(w)), 4)} for f, w in zip(features, coefs)
    ], key=lambda r: r["abs_weight"], reverse=True)
    # Research-only threshold study.
    threshold_rows = []
    test_returns = pd.to_numeric(ordered.iloc[split:][col], errors="coerce").fillna(0).reset_index(drop=True)
    for th in [0.50, 0.55, 0.60, 0.65, 0.70]:
        chosen = test_returns[pd.Series(prob) >= th]
        threshold_rows.append({
            "threshold": th,
            "samples": int(len(chosen)),
            "avg_return_pct": round(float(chosen.mean()), 4) if len(chosen) else 0.0,
            "win_rate": round(float((chosen > 0).mean() * 100), 2) if len(chosen) else 0.0,
        })
    verdict = "META_LABEL_RESEARCH_READY" if len(X_test) >= 50 and auc >= 0.55 else "META_LABEL_BUILDING"
    return {
        "run_id": rid, "generated_utc": utc_now_iso(), "status": verdict,
        "samples": len(df), "train_samples": len(X_train), "test_samples": len(X_test),
        "accuracy": round(acc * 100, 2), "auc": round(auc, 4), "top_features": feat_rows[:8],
        "threshold_study": threshold_rows,
        "blockers": [] if verdict == "META_LABEL_RESEARCH_READY" else ["AUC یا sample هنوز برای استفاده عملی کافی نیست."],
        "warnings": ["Meta-labeling فعلاً فقط Shadow/Research است و actionability را تغییر نمی‌دهد."],
        "recommendations": ["اگر AUC در Forward هم بالای 0.55 بماند، مرحله بعدی meta-label shadow gate است."],
    }


def run_ensemble_explainability(limit_recent: int = 25) -> Dict[str, Any]:
    df = load_decisions_df()
    if df.empty:
        df = directional_complete(load_backtest_df())
    rid = run_id("ensemble_explain")
    if df.empty:
        return {"run_id": rid, "generated_utc": utc_now_iso(), "status": "NO_DECISION_DATA", "rows": 0, "recent_explanations": [], "blockers": ["هیچ decision/backtest data برای explainability وجود ندارد."]}
    w = time_ordered(df).tail(limit_recent).copy()
    components = ["trend_score", "momentum_score", "volume_score", "structure_score", "historical_edge_score"]
    for c in components + ["long_score", "short_score", "score"]:
        if c in w.columns:
            w[c] = pd.to_numeric(w[c], errors="coerce").fillna(0)
        else:
            w[c] = 0
    explanations = []
    for _, row in w.iterrows():
        comp_vals = {c: float(row.get(c, 0) or 0) for c in components}
        total_abs = sum(abs(v) for v in comp_vals.values()) or 1.0
        shares = sorted([{"feature": k, "value": round(v, 2), "share_pct": round(abs(v) / total_abs * 100, 1)} for k, v in comp_vals.items()], key=lambda x: x["share_pct"], reverse=True)
        long_score = safe_float(row.get("long_score"), 0.0) or 0.0
        short_score = safe_float(row.get("short_score"), 0.0) or 0.0
        side = str(row.get("side", "NEUTRAL")).upper()
        side_margin = abs(long_score - short_score)
        component_support = sum(1 for v in comp_vals.values() if v > 0)
        agreement_score = round((component_support / len(components)) * 60 + min(side_margin, 40), 2)
        explanations.append({
            "decision_id": str(row.get("decision_id", "")),
            "candle_timestamp": str(row.get("candle_timestamp", "")),
            "symbol": str(row.get("symbol", "")),
            "side": side,
            "score": safe_float(row.get("score"), 0.0) or 0.0,
            "actionability": str(row.get("actionability", "")),
            "ensemble_agreement_score": agreement_score,
            "top_contributors": shares[:3],
            "note": "high_agreement" if agreement_score >= 70 else "mixed_or_building",
        })
    avg_agreement = round(float(np.mean([e["ensemble_agreement_score"] for e in explanations])), 2) if explanations else 0.0
    return {
        "run_id": rid,
        "generated_utc": utc_now_iso(),
        "status": "EXPLAINABILITY_READY",
        "rows": len(df),
        "recent_count": len(explanations),
        "avg_ensemble_agreement": avg_agreement,
        "recent_explanations": explanations,
        "warnings": ["Explainability سهم featureها را برای دیباگ نشان می‌دهد؛ به تنهایی سیگنال معاملاتی نیست."],
        "blockers": [],
    }


# 3) Data enrichment + regime

def run_data_enrichment_readiness() -> Dict[str, Any]:
    df = load_backtest_df()
    fwd = load_forward_eval_df()
    combined = pd.concat([df, fwd], ignore_index=True, sort=False) if not df.empty or not fwd.empty else pd.DataFrame()
    desired = {
        "funding_rate": ["funding_rate", "fundingRate", "funding"],
        "open_interest": ["open_interest", "openInterest", "oi"],
        "long_short_ratio": ["long_short_ratio", "longShortRatio", "ls_ratio"],
        "liquidations": ["liquidations", "long_liquidations", "short_liquidations"],
        "order_book_imbalance": ["order_book_imbalance", "bid_ask_imbalance", "book_imbalance"],
        "exchange_inflow_outflow": ["exchange_inflow", "exchange_outflow", "netflow"],
    }
    rows = []
    cols = set(combined.columns) if not combined.empty else set()
    for feature, aliases in desired.items():
        found = [a for a in aliases if a in cols]
        coverage = 0.0
        if found and not combined.empty:
            coverage = round(float(combined[found[0]].notna().mean() * 100), 2)
        rows.append({"feature": feature, "present": bool(found), "column": found[0] if found else "", "coverage_pct": coverage})
    connectors = {
        "coinalyze_fetcher.py": Path("coinalyze_fetcher.py").exists(),
        "futures_data_fetcher.py": Path("futures_data_fetcher.py").exists(),
        "news_sentiment.py": Path("news_sentiment.py").exists(),
        "airdrop_radar.py": Path("airdrop_radar.py").exists(),
    }
    missing = [r["feature"] for r in rows if not r["present"]]
    status = "ENRICHMENT_READY" if not missing else "ENRICHMENT_CONNECTORS_PRESENT" if any(connectors.values()) else "ENRICHMENT_MISSING"
    return {
        "run_id": run_id("data_enrichment"),
        "generated_utc": utc_now_iso(),
        "status": status,
        "features": rows,
        "connectors": connectors,
        "recommendations": [
            "Funding/Open Interest/Long-Short را اول به Shadow features اضافه کن، نه به decision live.",
            "Order book برای تایم‌فریم 4h اولویت پایین‌تر از derivatives aggregate دارد.",
        ],
        "warnings": ["عدم وجود ستون یعنی feature هنوز در لاگ تصمیم‌ها persist نشده است، نه اینکه collector حتماً وجود ندارد."],
    }


def run_regime_research(*, horizon: str = "24h") -> Dict[str, Any]:
    df = directional_complete(load_backtest_df())
    rid = run_id("regime_research")
    if df.empty:
        return {"run_id": rid, "generated_utc": utc_now_iso(), "status": "NO_BACKTEST_DATA", "regimes": [], "blockers": ["Backtest data موجود نیست."]}
    w = df.copy()
    if "regime_label" not in w.columns or w["regime_label"].astype(str).str.strip().eq("").all():
        w["regime_label"] = np.where(pd.to_numeric(w.get("trend_score", 0), errors="coerce").fillna(0) >= 20, "TRENDING", "RANGING")
    regime_rows = []
    for regime, group in w.groupby(w["regime_label"].fillna("UNKNOWN").astype(str)):
        met = metric_summary(group, horizon=horizon)
        regime_rows.append({"regime": regime, **met})
    regime_rows = sorted(regime_rows, key=lambda x: (x["avg_return_pct"], x["samples"]), reverse=True)
    coverage = len(regime_rows)
    return {
        "run_id": rid,
        "generated_utc": utc_now_iso(),
        "status": "REGIME_RESEARCH_READY" if coverage >= 2 else "REGIME_COVERAGE_LOW",
        "regime_count": coverage,
        "regimes": regime_rows,
        "coverage_requirement": "حداقل TRENDING/RANGING/HIGH_VOL یا معادل آن قبل از Paper جدی لازم است.",
        "warnings": ["Regime باید در Forward هم پر شود؛ Backtest regime به تنهایی کافی نیست."],
    }


# 4) Realistic simulation + cross-exchange

def run_cost_adjusted_backtest(*, horizon: str = "24h", fee_bps: float = 10.0, slippage_bps: float = 5.0) -> Dict[str, Any]:
    df = directional_complete(load_backtest_df())
    rid = run_id("cost_backtest")
    if df.empty:
        return {"run_id": rid, "generated_utc": utc_now_iso(), "status": "NO_BACKTEST_DATA", "groups": [], "blockers": ["Backtest data موجود نیست."]}
    groups = []
    group_defs = [("ALL", df)]
    for name, group in df.groupby("actionability"):
        group_defs.append((f"ACTIONABILITY_{name}", group))
    for spec in standard_gate_specs()[:17]:
        group_defs.append((f"GATE_{spec['name']}", apply_gate(df, spec["filters"])))
    for name, group in group_defs:
        gross = metric_summary(group, horizon=horizon, use_net=False)
        net = metric_summary(group, horizon=horizon, use_net=True, fee_bps=fee_bps, slippage_bps=slippage_bps)
        groups.append({"name": name, "samples": net["samples"], "gross_avg_pct": gross["avg_return_pct"], "net_avg_pct": net["avg_return_pct"], "net_win_rate": net["win_rate"], "net_t_stat": net["t_stat"], "verdict": _verdict_for_metrics(net)})
    groups = sorted(groups, key=lambda r: (r["net_avg_pct"], r["samples"]), reverse=True)
    return {
        "run_id": rid,
        "generated_utc": utc_now_iso(),
        "status": "COST_ADJUSTED_READY",
        "horizon": horizon,
        "fee_bps": fee_bps,
        "slippage_bps": slippage_bps,
        "groups": groups,
        "top_groups": groups[:12],
        "warnings": ["هزینه‌ها تخمینی هستند؛ برای هر صرافی باید fee/slippage جدا تنظیم شود."],
    }


def run_cross_exchange_validation(*, horizon: str = "24h") -> Dict[str, Any]:
    df = directional_complete(load_backtest_df())
    rid = run_id("cross_exchange")
    if df.empty:
        return {"run_id": rid, "generated_utc": utc_now_iso(), "status": "NO_BACKTEST_DATA", "providers": [], "blockers": ["Backtest data موجود نیست."]}
    if "provider" not in df.columns:
        return {"run_id": rid, "generated_utc": utc_now_iso(), "status": "PROVIDER_COLUMN_MISSING", "providers": [], "blockers": ["ستون provider وجود ندارد."]}
    providers = []
    for p, group in df.groupby(df["provider"].fillna("UNKNOWN").astype(str)):
        providers.append({"provider": p, **metric_summary(group, horizon=horizon)})
    providers = sorted(providers, key=lambda r: (r["avg_return_pct"], r["samples"]), reverse=True)
    verdict = "SINGLE_PROVIDER_ONLY" if len(providers) < 2 else "CROSS_EXCHANGE_READY"
    return {
        "run_id": rid,
        "generated_utc": utc_now_iso(),
        "status": verdict,
        "providers": providers,
        "recommendations": ["اگر فقط یک provider وجود دارد، همان Gate را روی Binance/Bybit/OKX جدا backfill کن."],
    }


# 5) Infra and observability

def run_research_db_export() -> Dict[str, Any]:
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    db_path = RESEARCH_DIR / "freakto_research.db"
    tables = {
        "historical_backtest_evaluations": BACKTEST_EVALS,
        "decision_evaluations": FORWARD_EVALS,
        "decisions": DECISIONS,
        "forward_test_runs": FORWARD_RUNS,
        "shadow_gate_signals": SHADOW_SIGNALS,
    }
    exported = []
    with sqlite3.connect(db_path) as con:
        for table, path in tables.items():
            df = read_csv_df(path)
            if not df.empty:
                df.to_sql(table, con, if_exists="replace", index=False)
                exported.append({"table": table, "rows": len(df), "source": str(path)})
        meta = pd.DataFrame([{"generated_utc": utc_now_iso(), "version": VERSION}])
        meta.to_sql("metadata", con, if_exists="replace", index=False)
    return {"run_id": run_id("research_db"), "generated_utc": utc_now_iso(), "status": "RESEARCH_DB_READY", "db_path": str(db_path), "tables": exported}


def run_pipeline_health(max_hours_without_run: float = 8.0) -> Dict[str, Any]:
    runs = read_csv_df(FORWARD_RUNS)
    alerts = []
    latest = {}
    if runs.empty:
        alerts.append("هیچ forward_test_runs.csv پیدا نشد.")
    else:
        latest_row = runs.tail(1).iloc[0].to_dict()
        latest = {k: str(v) for k, v in latest_row.items()}
        ok_text = str(latest_row.get("ok", "")).lower()
        if ok_text not in {"true", "1", "yes"}:
            alerts.append("آخرین Forward Run موفق نبوده است.")
        try:
            started = pd.to_datetime(latest_row.get("started_utc"), utc=True)
            hours = (pd.Timestamp.now(tz="UTC") - started).total_seconds() / 3600
            latest["hours_since_last_run"] = round(hours, 2)
            if hours > max_hours_without_run:
                alerts.append(f"بیش از {max_hours_without_run} ساعت از آخرین Forward Run گذشته است.")
        except Exception:
            alerts.append("زمان آخرین Forward Run قابل parse نیست.")
    evals = read_csv_df(FORWARD_EVALS)
    regime_known = 0
    regime_unknown = 0
    if evals.empty:
        alerts.append("decision_evaluations.csv خالی یا موجود نیست.")
    elif "regime_label" in evals.columns:
        labels = evals["regime_label"].fillna("UNKNOWN").astype(str).str.strip().str.upper().replace({"": "UNKNOWN", "NAN": "UNKNOWN", "NONE": "UNKNOWN"})
        regime_known = int((labels != "UNKNOWN").sum())
        regime_unknown = int((labels == "UNKNOWN").sum())
        if regime_known == 0:
            alerts.append("decision_evaluations.csv هنوز هیچ regime_label شناخته‌شده ندارد؛ v6.2.1 injection/evaluator را بررسی کن.")
    else:
        alerts.append("decision_evaluations.csv ستون regime_label ندارد؛ v6.2.1 injection لازم است.")
    shadow = read_csv_df(SHADOW_SIGNALS)
    if shadow.empty:
        alerts.append("shadow_gate_signals.csv هنوز ساخته نشده یا خالی است.")
    status = "PIPELINE_HEALTHY" if not alerts else "PIPELINE_ATTENTION_REQUIRED"
    return {"run_id": run_id("pipeline_health"), "generated_utc": utc_now_iso(), "status": status, "alerts": alerts, "latest_forward_run": latest, "forward_eval_rows": len(evals), "forward_regime_known_rows": regime_known, "forward_regime_unknown_rows": regime_unknown, "shadow_signal_rows": len(shadow)}


def run_static_dashboard(summary: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    summary = summary or run_full_research_suite(save=False)
    out_dir = LOG_DIR / "research_dashboard"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "index.html"
    sections = []
    for key, val in summary.get("sections", {}).items():
        status = val.get("status", "") if isinstance(val, dict) else ""
        sections.append(f"<tr><td>{key}</td><td>{status}</td><td><pre>{json.dumps(val, ensure_ascii=False, indent=2)[:2500]}</pre></td></tr>")
    html = f"""<!doctype html><html lang='fa'><head><meta charset='utf-8'><title>Freakto Research Dashboard</title>
<style>body{{font-family:Arial,sans-serif;direction:rtl;background:#111;color:#eee;padding:24px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #555;padding:8px;vertical-align:top}}pre{{white-space:pre-wrap;direction:ltr;text-align:left}}</style></head>
<body><h1>Freakto Research Dashboard v6</h1><p>Generated UTC: {utc_now_iso()}</p><table><tr><th>Section</th><th>Status</th><th>Details</th></tr>{''.join(sections)}</table></body></html>"""
    write_text(path, html)
    return {"run_id": run_id("static_dashboard"), "generated_utc": utc_now_iso(), "status": "STATIC_DASHBOARD_READY", "html_path": str(path)}


# 6) Strict readiness

def run_statistical_readiness(*, horizon: str = "24h") -> Dict[str, Any]:
    backtest = directional_complete(load_backtest_df())
    forward = directional_complete(load_forward_eval_df())
    bt = metric_summary(backtest, horizon=horizon, use_net=True)
    fw = metric_summary(forward, horizon=horizon, use_net=True)
    blockers = []
    if bt["samples"] < 100:
        blockers.append("Backtest sample کمتر از 100 است.")
    if bt["confidence_95_low_pct"] <= 0:
        blockers.append("Backtest net expectancy از نظر CI95 بالای صفر نیست.")
    if fw["samples"] < 30:
        blockers.append("Forward complete samples کمتر از 30 است.")
    if fw["avg_return_pct"] <= 0:
        blockers.append("Forward net expectancy مثبت نیست.")
    regimes = []
    if not backtest.empty and "regime_label" in backtest.columns:
        regimes = sorted([str(x) for x in backtest["regime_label"].dropna().astype(str).unique() if str(x).strip()])
    if len(regimes) < 2:
        blockers.append("پوشش regime کافی نیست؛ حداقل دو رژیم معتبر لازم است.")
    btc_corr = _estimate_btc_beta_correlation(backtest, horizon=horizon)
    if abs(btc_corr.get("correlation_to_btc", 0.0)) > 0.80 and btc_corr.get("samples", 0) >= 20:
        blockers.append("Edge ممکن است بیشتر beta/exposure به BTC باشد تا edge مستقل.")
    status = "STRICT_READINESS_RESEARCH_ONLY" if blockers else "STRICT_READINESS_PAPER_REVIEW_CANDIDATE"
    return {"run_id": run_id("strict_readiness"), "generated_utc": utc_now_iso(), "status": status, "backtest_net": bt, "forward_net": fw, "regime_labels": regimes, "btc_beta_check": btc_corr, "blockers": blockers, "warnings": ["این readiness سخت‌گیرانه‌تر از نسخه‌های قبلی است و به تنهایی مجوز Live نیست."]}


def _estimate_btc_beta_correlation(df: pd.DataFrame, horizon: str = "24h") -> Dict[str, Any]:
    col = RETURN_COLUMNS.get(horizon, "return_after_24h_pct")
    if df.empty or col not in df.columns or "symbol" not in df.columns or "candle_timestamp" not in df.columns:
        return {"samples": 0, "correlation_to_btc": 0.0, "note": "insufficient_data"}
    w = df[["candle_timestamp", "symbol", col]].copy()
    w[col] = pd.to_numeric(w[col], errors="coerce")
    pivot = w.pivot_table(index="candle_timestamp", columns="symbol", values=col, aggfunc="mean")
    if "BTC/USDT" not in pivot.columns or len(pivot) < 5:
        return {"samples": 0, "correlation_to_btc": 0.0, "note": "btc_column_missing"}
    others = pivot.drop(columns=["BTC/USDT"]).mean(axis=1)
    joined = pd.concat([pivot["BTC/USDT"], others], axis=1).dropna()
    joined.columns = ["btc", "others"]
    if len(joined) < 5:
        return {"samples": int(len(joined)), "correlation_to_btc": 0.0, "note": "low_overlap"}
    return {"samples": int(len(joined)), "correlation_to_btc": round(float(joined["btc"].corr(joined["others"])), 4), "note": "avg_other_symbols_vs_btc"}


# 7) Paper/Micro-live preparation + airdrop gate/shadow

def run_position_sizing_lab(*, horizon: str = "24h", max_risk_pct: float = 0.50) -> Dict[str, Any]:
    df = directional_complete(load_backtest_df())
    if df.empty:
        return {"run_id": run_id("position_sizing"), "generated_utc": utc_now_iso(), "status": "NO_BACKTEST_DATA", "rows": []}
    rows = []
    for spec in standard_gate_specs():
        sample = apply_gate(df, spec["filters"])
        met = metric_summary(sample, horizon=horizon, use_net=True)
        n = met["samples"]
        mean = met["avg_return_pct"] / 100.0
        std = met["std_return_pct"] / 100.0
        # Conservative fractional Kelly proxy: mean / variance, clipped and scaled down to 10% Kelly.
        raw_kelly = mean / (std ** 2) if std > 0 and mean > 0 else 0.0
        conservative_kelly_pct = max(0.0, min(max_risk_pct, raw_kelly * 0.10 * 100))
        if n < 30 or met["avg_return_pct"] <= 0:
            conservative_kelly_pct = 0.0
        volatility_risk_pct = max(0.0, min(max_risk_pct, 0.25 / max(met["std_return_pct"], 0.01))) if n >= 30 else 0.0
        suggested = min(conservative_kelly_pct, volatility_risk_pct, max_risk_pct)
        rows.append({"gate": spec["name"], "samples": n, "net_avg_pct": met["avg_return_pct"], "std_pct": met["std_return_pct"], "kelly_proxy_risk_pct": round(conservative_kelly_pct, 4), "volatility_risk_pct": round(volatility_risk_pct, 4), "suggested_shadow_risk_pct": round(suggested, 4), "verdict": "SIZE_RESEARCH_ONLY" if suggested > 0 else "NO_SIZE"})
    rows = sorted(rows, key=lambda r: (r["suggested_shadow_risk_pct"], r["net_avg_pct"], r["samples"]), reverse=True)
    return {"run_id": run_id("position_sizing"), "generated_utc": utc_now_iso(), "status": "POSITION_SIZING_RESEARCH_READY", "max_risk_pct": max_risk_pct, "rows": rows[:20], "warnings": ["Position sizing فقط آزمایشگاهی است؛ تا readiness کافی نباشد نباید live شود."]}


def run_airdrop_shadow_research() -> Dict[str, Any]:
    rid = run_id("airdrop_shadow")
    if not AIRDROP_WATCHLIST.exists():
        return {"run_id": rid, "generated_utc": utc_now_iso(), "status": "NO_AIRDROP_WATCHLIST", "items": [], "blockers": ["data/airdrop_watchlist.json وجود ندارد."]}
    try:
        data = json.loads(AIRDROP_WATCHLIST.read_text(encoding="utf-8"))
        items = data.get("items", data if isinstance(data, list) else [])
    except Exception as exc:
        return {"run_id": rid, "generated_utc": utc_now_iso(), "status": "INVALID_AIRDROP_WATCHLIST", "items": [], "blockers": [str(exc)]}
    rows = []
    for item in items:
        cost = safe_float(item.get("estimated_cost_usd"), None)
        minutes = safe_float(item.get("estimated_minutes"), None)
        priority = safe_int(item.get("priority_hint"), 0)
        token_status = str(item.get("token_status", "")).lower()
        tags = [str(t).lower() for t in item.get("tags", [])]
        score = 0
        if item.get("official_url"):
            score += 15
        if item.get("docs_url"):
            score += 10
        if token_status in {"tokenless-likely", "no-token-confirmed"}:
            score += 15
        if cost is not None and cost <= 10:
            score += 15
        elif cost is not None and cost > 25:
            score -= 10
        if minutes is not None and minutes <= 45:
            score += 10
        elif minutes is not None and minutes > 90:
            score -= 8
        if any(t in tags for t in ["points", "testnet", "tokenless", "incentive"]):
            score += 15
        score += priority
        score = max(0, min(100, score))
        gates = []
        if score >= 65:
            gates.append("AIRDROP_SCORE_GE_65")
        if cost is not None and cost <= 10:
            gates.append("LOW_COST")
        if token_status in {"tokenless-likely", "no-token-confirmed"}:
            gates.append("TOKENLESS_CANDIDATE")
        rows.append({"name": item.get("name", "UNKNOWN"), "score": score, "shadow_gates": ",".join(gates), "cost_usd": cost, "minutes": minutes, "token_status": token_status, "verdict": "AIRDROP_RESEARCH_CANDIDATE" if score >= 65 else "WATCH_OR_IGNORE"})
    rows = sorted(rows, key=lambda r: r["score"], reverse=True)
    return {"run_id": rid, "generated_utc": utc_now_iso(), "status": "AIRDROP_SHADOW_READY", "items": rows, "warnings": ["Airdrop shadow فقط امتیازدهی تحقیقاتی است؛ نباید wallet connect یا signature خودکار انجام شود."]}


# Save / format / orchestrate

def save_section(name: str, data: Dict[str, Any]) -> Tuple[Path, Path]:
    SUITE_DIR.mkdir(parents=True, exist_ok=True)
    rid = data.get("run_id", run_id(name))
    json_path = SUITE_DIR / f"{name}_{rid}.json"
    md_path = SUITE_DIR / f"{name}_report_{rid}.md"
    write_json(json_path, data)
    write_text(md_path, format_section_console(name, data, compact=False))
    return json_path, md_path


def format_section_console(name: str, data: Dict[str, Any], compact: bool = True) -> str:
    sep = "=" * 110
    title = name.replace("_", " ").title()
    lines = [sep, f"🧠 Freakto {title} {VERSION}", sep]
    lines.append(f"Status: {data.get('status', 'UNKNOWN')}")
    if data.get("run_id"):
        lines.append(f"Run ID: {data.get('run_id')}")
    # common summaries
    if "baseline_net" in data:
        bn = data["baseline_net"]
        lines.append(f"Baseline Net: samples={bn.get('samples')} | avg={bn.get('avg_return_pct')}% | win={bn.get('win_rate')}%")
    if "top_results" in data:
        lines.append("\nTop Robustness Results:")
        for r in data["top_results"][:8 if compact else 20]:
            lines.append(f"- {r.get('gate')}: {r.get('verdict')} | n={r.get('samples')} | net={r.get('net_avg_pct')}% | stability={r.get('stability_pct')}% | robust={r.get('robust_score')}")
    if "top_features" in data:
        lines.append("\nTop Features:")
        for r in data["top_features"][:8]:
            lines.append(f"- {r.get('feature')}: weight={r.get('weight')}")
    if "features" in data:
        lines.append("\nData Features:")
        for r in data["features"]:
            lines.append(f"- {r.get('feature')}: present={r.get('present')} | coverage={r.get('coverage_pct')}%")
    if "regimes" in data:
        lines.append("\nRegimes:")
        for r in data["regimes"][:10]:
            lines.append(f"- {r.get('regime')}: n={r.get('samples')} | avg={r.get('avg_return_pct')}% | win={r.get('win_rate')}%")
    if "top_groups" in data:
        lines.append("\nTop Cost-Adjusted Groups:")
        for r in data["top_groups"][:10]:
            lines.append(f"- {r.get('name')}: {r.get('verdict')} | n={r.get('samples')} | gross={r.get('gross_avg_pct')}% | net={r.get('net_avg_pct')}%")
    if "providers" in data:
        lines.append("\nProviders:")
        for r in data["providers"]:
            lines.append(f"- {r.get('provider')}: n={r.get('samples')} | avg={r.get('avg_return_pct')}% | win={r.get('win_rate')}%")
    if "tables" in data:
        lines.append("\nSQLite Tables:")
        for r in data["tables"]:
            lines.append(f"- {r.get('table')}: rows={r.get('rows')}")
    if "alerts" in data:
        lines.append("\nPipeline Alerts:")
        lines.extend([f"⚠️ {a}" for a in data.get("alerts", [])] or ["✅ بدون هشدار جدی"])
    if "backtest_net" in data:
        lines.append(f"\nBacktest Net: n={data['backtest_net'].get('samples')} avg={data['backtest_net'].get('avg_return_pct')}% ci95=[{data['backtest_net'].get('confidence_95_low_pct')},{data['backtest_net'].get('confidence_95_high_pct')}]")
        lines.append(f"Forward Net: n={data['forward_net'].get('samples')} avg={data['forward_net'].get('avg_return_pct')}%")
    if "rows" in data and isinstance(data["rows"], list):
        lines.append("\nRows:")
        for r in data["rows"][:10]:
            if "gate" in r:
                lines.append(f"- {r.get('gate')}: suggested={r.get('suggested_shadow_risk_pct')}% | n={r.get('samples')} | avg={r.get('net_avg_pct')}% | verdict={r.get('verdict')}")
    if "items" in data:
        lines.append("\nAirdrop Items:")
        for r in data["items"][:10]:
            lines.append(f"- {r.get('name')}: score={r.get('score')} | gates={r.get('shadow_gates')} | verdict={r.get('verdict')}")
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



def _shadow_report_to_dict(report: Any) -> Dict[str, Any]:
    """Convert ShadowGateReport dataclass to a compact dict for the v6.2 suite."""
    try:
        data = asdict(report)
    except Exception:
        data = dict(report) if isinstance(report, dict) else {}
    regime_metrics = [m for m in data.get("gate_metrics", []) if m.get("family") == "regime_gate_matrix_candidate"]
    data["regime_gate_metrics"] = regime_metrics[:12]
    data["regime_gate_count"] = len(regime_metrics)
    data["regime_gate_signals"] = sum(int(m.get("total_signals", 0) or 0) for m in regime_metrics)
    data["status"] = "REGIME_SHADOW_GATES_ACTIVE" if regime_metrics else data.get("status", "UNKNOWN")
    return data

def run_full_research_suite(*, save: bool = True) -> Dict[str, Any]:
    from engine.regime_gate_matrix import run_regime_gate_matrix
    from engine.shadow_gates import run_shadow_gate_validation
    from engine.forward_regime_labeling import run_forward_regime_labeling
    from engine.forward_shadow_coverage import run_forward_shadow_coverage

    sections = {
        "gate_robustness": run_gate_robustness(),
        "cost_adjusted_backtest": run_cost_adjusted_backtest(),
        "meta_labeling": run_meta_labeling(),
        "ensemble_explainability": run_ensemble_explainability(),
        "data_enrichment": run_data_enrichment_readiness(),
        "regime_research": run_regime_research(),
        "forward_regime_labeling": asdict(run_forward_regime_labeling(apply_changes=False)),
        "regime_gate_matrix": run_regime_gate_matrix(),
        "regime_shadow_gates": _shadow_report_to_dict(run_shadow_gate_validation()),
        "forward_shadow_coverage": run_forward_shadow_coverage(),
        "cross_exchange_validation": run_cross_exchange_validation(),
        "research_db": run_research_db_export(),
        "pipeline_health": run_pipeline_health(),
        "strict_readiness": run_statistical_readiness(),
        "position_sizing_lab": run_position_sizing_lab(),
        "airdrop_shadow_research": run_airdrop_shadow_research(),
    }
    # Build static dashboard after sections exist.
    static = run_static_dashboard({"sections": sections})
    sections["static_dashboard"] = static
    status = "RESEARCH_SUITE_READY"
    blockers = []
    for key, sec in sections.items():
        blockers.extend([f"{key}: {b}" for b in sec.get("blockers", [])]) if isinstance(sec, dict) else None
    if blockers:
        status = "RESEARCH_SUITE_WITH_BLOCKERS"
    report = {"run_id": run_id("research_suite"), "generated_utc": utc_now_iso(), "version": VERSION, "status": status, "sections": sections, "blockers": blockers[:25]}
    if save:
        SUITE_DIR.mkdir(parents=True, exist_ok=True)
        write_json(SUITE_DIR / f"research_suite_{report['run_id']}.json", report)
        write_text(SUITE_DIR / f"research_suite_report_{report['run_id']}.md", format_full_suite_console(report))
    return report


def format_full_suite_console(report: Dict[str, Any], compact: bool = True) -> str:
    sep = "=" * 110
    lines = [sep, f"🧠 Freakto Research Robustness & Intelligence Suite {VERSION}", sep]
    lines.append(f"Status: {report.get('status')}")
    lines.append(f"Run ID: {report.get('run_id')}")
    lines.append("\nSections:")
    for key, sec in report.get("sections", {}).items():
        status = sec.get("status", "UNKNOWN") if isinstance(sec, dict) else "UNKNOWN"
        lines.append(f"- {key}: {status}")
    # Important highlights.
    gr = report.get("sections", {}).get("gate_robustness", {})
    if gr:
        lines.append("\nGate Robustness Highlights:")
        for r in gr.get("top_results", [])[:5]:
            lines.append(f"- {r.get('gate')}: {r.get('verdict')} | n={r.get('samples')} | net={r.get('net_avg_pct')}% | stability={r.get('stability_pct')}%")
    rgm = report.get("sections", {}).get("regime_gate_matrix", {})
    if rgm:
        lines.append("\nRegime-Gate Matrix Highlights:")
        lines.append(f"- {rgm.get('status')} | candidates={rgm.get('candidate_count', 0)} | horizon={rgm.get('horizon')}")
        for r in (rgm.get("regime_candidates", []) + rgm.get("regime_gate_side_candidates", []))[:5]:
            label = f"{r.get('regime')} × {r.get('gate')}" + (f" × {r.get('side')}" if r.get('side') else "")
            lines.append(f"- {label}: n={r.get('samples')} | net={r.get('net_avg_pct')}% | verdict={r.get('verdict')}")
    frl = report.get("sections", {}).get("forward_regime_labeling", {})
    if frl:
        lines.append("\nForward Regime Labeling:")
        lines.append(f"- {frl.get('status')} | known={frl.get('known_after')} | unknown={frl.get('unknown_after')} | injected={frl.get('injected_decision_rows')}")
    rsg = report.get("sections", {}).get("regime_shadow_gates", {})
    if rsg:
        lines.append("\nRegime Shadow Gate Highlights:")
        lines.append(f"- {rsg.get('status')} | regime_gates={rsg.get('regime_gate_count', 0)} | signals={rsg.get('regime_gate_signals', 0)} | eval={rsg.get('evaluated_shadow_samples', 0)}")
        for r in rsg.get("regime_gate_metrics", [])[:4]:
            lines.append(f"- {r.get('gate')}: {r.get('verdict')} | signals={r.get('total_signals')} | eval={r.get('evaluated_samples')} | avg={r.get('avg_return_pct')}%")
    fsc = report.get("sections", {}).get("forward_shadow_coverage", {})
    if fsc:
        lines.append("\nForward Shadow Coverage / Bull Probe:")
        lines.append(f"- {fsc.get('status')} | decisions={fsc.get('decision_rows')} | shadow_signals={fsc.get('shadow_signal_rows')} | eval_shadow={fsc.get('evaluated_shadow_rows')}")
        for r in fsc.get("bull_forward_probes", [])[:4]:
            lines.append(f"- {r.get('probe')}: {r.get('verdict')} | fwd_n={r.get('forward_samples')} | fwd_avg={r.get('forward_avg_pct')}% | bt_net={r.get('backtest_net_avg_pct')}%")
    sr = report.get("sections", {}).get("strict_readiness", {})
    if sr:
        lines.append("\nStrict Readiness:")
        lines.append(f"- {sr.get('status')} | blockers={len(sr.get('blockers', []))}")
        for b in sr.get("blockers", [])[:8]:
            lines.append(f"  ⛔ {b}")
    ph = report.get("sections", {}).get("pipeline_health", {})
    if ph:
        lines.append("\nPipeline Health:")
        lines.append(f"- {ph.get('status')} | alerts={len(ph.get('alerts', []))}")
    if report.get("blockers"):
        lines.append("\nSuite Blockers:")
        for b in report.get("blockers", [])[:12]:
            lines.append(f"⛔ {b}")
    lines.append("\nSafety: هیچ بخش v6/v6.1/v6.2/v6.2.1/v6.3 سفارش واقعی ارسال نمی‌کند و Paper Trade جدید ایجاد نمی‌کند.")
    lines.append(sep)
    return "\n".join(lines)


def save_full_suite(report: Dict[str, Any]) -> Tuple[Path, Path]:
    SUITE_DIR.mkdir(parents=True, exist_ok=True)
    json_path = SUITE_DIR / f"research_suite_{report['run_id']}.json"
    md_path = SUITE_DIR / f"research_suite_report_{report['run_id']}.md"
    write_json(json_path, report)
    write_text(md_path, format_full_suite_console(report, compact=False))
    return json_path, md_path
