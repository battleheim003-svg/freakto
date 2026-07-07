"""
engine/backtest_diagnostics.py

Freakto v5.3.1 - Backtest Diagnostics & Edge Breakdown

Purpose:
- Diagnose WHY historical backtest edge is weak/negative.
- Break down performance by side, symbol, actionability, score bucket,
  confidence/risk labels, component buckets, target/stop behavior, MFE/MAE,
  and holding periods.
- Keep BACKTEST research separate from FORWARD_TEST and Paper/Live decisions.

Safety:
This module never sends orders and never creates paper trades. It only reads
logs/historical_backtest_evaluations.csv and writes diagnostic reports.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from engine.csv_utils import read_csv_dicts_lenient
from engine.historical_backtest import BACKTEST_EVALUATIONS_FILE


LOG_DIR = Path("logs")
DIAG_DIR = LOG_DIR / "backtests" / "diagnostics"

RETURN_COLUMNS = [
    "return_after_4h_pct",
    "return_after_12h_pct",
    "return_after_24h_pct",
]
COMPONENT_COLUMNS = [
    "trend_score",
    "momentum_score",
    "volume_score",
    "structure_score",
    "risk_penalty",
    "historical_edge_score",
    "long_score",
    "short_score",
]


@dataclass
class DiagnosticTable:
    name: str
    rows: List[Dict] = field(default_factory=list)


@dataclass
class BacktestDiagnostics:
    run_id: str
    generated_utc: str
    status: str
    total_rows: int
    complete_rows: int
    directional_samples: int
    avg_24h_return_pct: float
    directional_win_rate: float
    target_1_hit_rate: float
    stop_hit_rate: float
    mfe_mean_pct: float
    mae_mean_pct: float
    best_holding_period: str
    best_holding_avg_return_pct: float
    tables: Dict[str, List[Dict]]
    blockers: List[str]
    warnings: List[str]
    recommendations: List[str]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_run_id() -> str:
    return "backtest_diag_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _safe_float(value, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        text = str(value).replace(",", "").strip()
        if not text or text.lower() in {"nan", "none", "null"}:
            return default
        return float(text)
    except Exception:
        return default


def _safe_bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin({"true", "1", "yes", "y"})


def _rate(num: int, den: int) -> float:
    return round(num / den * 100, 2) if den else 0.0


def _read_backtest_rows(path: Path = BACKTEST_EVALUATIONS_FILE) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        _, rows = read_csv_dicts_lenient(path)
        return pd.DataFrame(rows)


def _prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    work = df.copy()
    for col in RETURN_COLUMNS + COMPONENT_COLUMNS + ["score", "mfe_pct", "mae_pct"]:
        if col in work.columns:
            work[col] = pd.to_numeric(work[col], errors="coerce")
    if "evaluation_status" not in work.columns:
        work["evaluation_status"] = ""
    if "side" not in work.columns:
        work["side"] = ""
    if "actionability" not in work.columns:
        work["actionability"] = ""
    if "symbol" not in work.columns:
        work["symbol"] = "UNKNOWN"
    return work


def _complete_directional(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    complete = df[df["evaluation_status"].astype(str).str.upper() == "COMPLETE"].copy()
    return complete[complete["side"].astype(str).isin(["LONG", "SHORT"])].copy()


def _metrics_for_group(group: pd.DataFrame, return_col: str = "return_after_24h_pct") -> Dict:
    if group is None or group.empty:
        return {
            "rows": 0,
            "samples": 0,
            "win_rate": 0.0,
            "avg_return_pct": 0.0,
            "median_return_pct": 0.0,
            "best_return_pct": 0.0,
            "worst_return_pct": 0.0,
            "target_1_hit_rate": 0.0,
            "stop_hit_rate": 0.0,
            "mfe_mean_pct": 0.0,
            "mae_mean_pct": 0.0,
            "mfe_mae_ratio": 0.0,
        }
    ret = pd.to_numeric(group.get(return_col, pd.Series(dtype=float)), errors="coerce").dropna()
    t1 = _safe_bool_series(group.get("target_1_hit", pd.Series(dtype=str))).sum() if "target_1_hit" in group else 0
    st = _safe_bool_series(group.get("stop_hit", pd.Series(dtype=str))).sum() if "stop_hit" in group else 0
    mfe = pd.to_numeric(group.get("mfe_pct", pd.Series(dtype=float)), errors="coerce").dropna()
    mae = pd.to_numeric(group.get("mae_pct", pd.Series(dtype=float)), errors="coerce").dropna()
    mae_abs = abs(float(mae.mean())) if len(mae) else 0.0
    mfe_mean = float(mfe.mean()) if len(mfe) else 0.0
    return {
        "rows": int(len(group)),
        "samples": int(len(ret)),
        "win_rate": _rate(int((ret > 0).sum()), int(len(ret))),
        "avg_return_pct": round(float(ret.mean()), 4) if len(ret) else 0.0,
        "median_return_pct": round(float(ret.median()), 4) if len(ret) else 0.0,
        "best_return_pct": round(float(ret.max()), 4) if len(ret) else 0.0,
        "worst_return_pct": round(float(ret.min()), 4) if len(ret) else 0.0,
        "target_1_hit_rate": _rate(int(t1), int(len(group))),
        "stop_hit_rate": _rate(int(st), int(len(group))),
        "mfe_mean_pct": round(mfe_mean, 4),
        "mae_mean_pct": round(float(mae.mean()), 4) if len(mae) else 0.0,
        "mfe_mae_ratio": round(mfe_mean / mae_abs, 3) if mae_abs else 0.0,
    }


def _group_table(df: pd.DataFrame, group_col: str, *, min_samples: int = 1, return_col: str = "return_after_24h_pct") -> List[Dict]:
    if df.empty or group_col not in df.columns:
        return []
    rows = []
    for key, group in df.groupby(group_col, dropna=False):
        metrics = _metrics_for_group(group, return_col=return_col)
        if metrics["samples"] < min_samples:
            continue
        rows.append({group_col: str(key), **metrics})
    return sorted(rows, key=lambda item: (item.get("avg_return_pct", 0.0), item.get("samples", 0)), reverse=True)


def _bucketize_numeric(df: pd.DataFrame, col: str, bins: Sequence[float], labels: Sequence[str]) -> pd.Series:
    if df.empty or col not in df.columns:
        return pd.Series(dtype=str)
    values = pd.to_numeric(df[col], errors="coerce")
    return pd.cut(values, bins=bins, labels=labels, include_lowest=True).astype(str)


def _score_bucket_table(df: pd.DataFrame) -> List[Dict]:
    if df.empty or "score" not in df.columns:
        return []
    work = df.copy()
    work["score_bucket"] = _bucketize_numeric(
        work,
        "score",
        bins=[-999, 29, 39, 49, 59, 69, 79, 89, 999],
        labels=["<30", "30-39", "40-49", "50-59", "60-69", "70-79", "80-89", "90+"],
    )
    return _group_table(work, "score_bucket", min_samples=1)


def _component_bucket_table(df: pd.DataFrame, col: str) -> List[Dict]:
    if df.empty or col not in df.columns:
        return []
    work = df.copy()
    work[f"{col}_bucket"] = _bucketize_numeric(
        work,
        col,
        bins=[-999, -1, 0, 4, 9, 14, 19, 999],
        labels=["negative", "0", "1-4", "5-9", "10-14", "15-19", "20+"],
    )
    return _group_table(work, f"{col}_bucket", min_samples=1)


def _holding_period_table(df: pd.DataFrame) -> List[Dict]:
    rows = []
    for col in RETURN_COLUMNS:
        if col not in df.columns:
            continue
        label = col.replace("return_after_", "").replace("_pct", "")
        metrics = _metrics_for_group(df, return_col=col)
        rows.append({"holding_period": label, **metrics})
    return sorted(rows, key=lambda item: item.get("avg_return_pct", 0.0), reverse=True)


def _target_stop_table(df: pd.DataFrame) -> List[Dict]:
    if df.empty:
        return []
    work = df.copy()
    t1 = _safe_bool_series(work.get("target_1_hit", pd.Series(dtype=str))) if "target_1_hit" in work else pd.Series([False] * len(work))
    stop = _safe_bool_series(work.get("stop_hit", pd.Series(dtype=str))) if "stop_hit" in work else pd.Series([False] * len(work))
    conditions = []
    for a, b in zip(t1.tolist(), stop.tolist()):
        if a and b:
            conditions.append("TARGET_AND_STOP")
        elif a:
            conditions.append("TARGET_ONLY")
        elif b:
            conditions.append("STOP_ONLY")
        else:
            conditions.append("NO_TARGET_NO_STOP")
    work["path_outcome"] = conditions
    return _group_table(work, "path_outcome", min_samples=1)


def _compound_group_table(df: pd.DataFrame, cols: Sequence[str], name: str) -> List[Dict]:
    if df.empty or any(col not in df.columns for col in cols):
        return []
    work = df.copy()
    work[name] = work[list(cols)].astype(str).agg(" | ".join, axis=1)
    return _group_table(work, name, min_samples=3)


def _find_best(rows: List[Dict], min_samples: int = 10) -> Optional[Dict]:
    candidates = [row for row in rows if int(row.get("samples", 0)) >= min_samples]
    if not candidates:
        candidates = [row for row in rows if int(row.get("samples", 0)) > 0]
    if not candidates:
        return None
    return sorted(candidates, key=lambda row: (float(row.get("avg_return_pct", 0.0)), int(row.get("samples", 0))), reverse=True)[0]


def _recommendations(tables: Dict[str, List[Dict]], overall_avg: float, directional_samples: int) -> Tuple[List[str], List[str]]:
    blockers = []
    recs = []
    if directional_samples < 100:
        blockers.append(f"نمونه‌های جهت‌دار Backtest کمتر از 100 است: {directional_samples}")
    if overall_avg <= 0:
        blockers.append("میانگین بازده 24h در کل Backtest مثبت نیست.")
        recs.append("قبل از Paper/Live، گیت‌های ورود باید سخت‌تر یا تفکیک‌شده‌تر شوند؛ ACTIONABLE فعلی هنوز Edge مثبت تاریخی نداده است.")

    best_side = _find_best(tables.get("by_side", []), min_samples=20)
    if best_side:
        recs.append(
            f"بهترین سمت تاریخی فعلی: {best_side.get('side')} با avg24h={best_side.get('avg_return_pct')}% و samples={best_side.get('samples')}. Long/Short را جداگانه gate کن."
        )

    best_symbol = _find_best(tables.get("by_symbol", []), min_samples=20)
    if best_symbol:
        recs.append(
            f"بهترین نماد تاریخی فعلی: {best_symbol.get('symbol')} با avg24h={best_symbol.get('avg_return_pct')}% و win={best_symbol.get('win_rate')}%. نمادهای ضعیف را برای Paper محدود کن."
        )

    best_hold = _find_best(tables.get("by_holding_period", []), min_samples=20)
    if best_hold:
        recs.append(
            f"بهترین holding period فعلی: {best_hold.get('holding_period')} با avg={best_hold.get('avg_return_pct')}%. خروج 24h را قطعی فرض نکن."
        )

    best_score = _find_best(tables.get("by_score_bucket", []), min_samples=20)
    if best_score:
        recs.append(
            f"بهترین score bucket فعلی: {best_score.get('score_bucket')} با avg={best_score.get('avg_return_pct')}%. threshold باید بر اساس bucket واقعی تنظیم شود، نه حس عددی score."
        )

    path_rows = tables.get("by_target_stop_path", [])
    stop_only = next((row for row in path_rows if row.get("path_outcome") == "STOP_ONLY"), None)
    target_only = next((row for row in path_rows if row.get("path_outcome") == "TARGET_ONLY"), None)
    if stop_only and target_only and stop_only.get("samples", 0) >= target_only.get("samples", 0):
        recs.append("STOP_ONLY حداقل به اندازه TARGET_ONLY رخ داده؛ stop/target یا entry timing باید بازبینی شود.")

    if not recs:
        recs.append("داده کافی برای پیشنهاد قطعی نیست؛ Backtest و Forward Test را ادامه بده.")
    return blockers, recs


def run_backtest_diagnostics(path: Path = BACKTEST_EVALUATIONS_FILE) -> BacktestDiagnostics:
    run_id = make_run_id()
    raw = _read_backtest_rows(path)
    df = _prepare_df(raw)
    if df.empty:
        return BacktestDiagnostics(
            run_id=run_id,
            generated_utc=utc_now_iso(),
            status="NO_BACKTEST_DATA",
            total_rows=0,
            complete_rows=0,
            directional_samples=0,
            avg_24h_return_pct=0.0,
            directional_win_rate=0.0,
            target_1_hit_rate=0.0,
            stop_hit_rate=0.0,
            mfe_mean_pct=0.0,
            mae_mean_pct=0.0,
            best_holding_period="",
            best_holding_avg_return_pct=0.0,
            tables={},
            blockers=["هیچ داده historical_backtest_evaluations.csv وجود ندارد."],
            warnings=["ابتدا historical_backtest_dashboard.py را اجرا کن."],
            recommendations=["یک Backtest سبک اجرا کن و دوباره diagnostics بگیر."],
        )

    complete = df[df["evaluation_status"].astype(str).str.upper() == "COMPLETE"].copy()
    directional = _complete_directional(df)
    overall = _metrics_for_group(directional)

    tables: Dict[str, List[Dict]] = {
        "by_side": _group_table(directional, "side"),
        "by_symbol": _group_table(directional, "symbol"),
        "by_actionability": _group_table(directional, "actionability"),
        "by_score_bucket": _score_bucket_table(directional),
        "by_confidence": _group_table(directional, "confidence_label"),
        "by_risk_label": _group_table(directional, "risk_label"),
        "by_regime": _group_table(directional, "regime_label"),
        "by_holding_period": _holding_period_table(directional),
        "by_target_stop_path": _target_stop_table(directional),
        "by_symbol_side": _compound_group_table(directional, ["symbol", "side"], "symbol_side"),
        "by_actionability_side": _compound_group_table(directional, ["actionability", "side"], "actionability_side"),
    }
    for col in ["trend_score", "momentum_score", "volume_score", "structure_score", "risk_penalty", "historical_edge_score"]:
        tables[f"by_{col}_bucket"] = _component_bucket_table(directional, col)

    best_hold = _find_best(tables.get("by_holding_period", []), min_samples=10) or {}
    blockers, recs = _recommendations(tables, overall.get("avg_return_pct", 0.0), int(len(directional)))
    warnings = [
        "این گزارش فقط Backtest تاریخی است و جای Forward/Paper واقعی را نمی‌گیرد.",
        "گروه‌هایی با sample کم ممکن است تصادفی یا overfit باشند؛ برای تصمیم از sample کافی استفاده کن.",
    ]
    status = "DIAGNOSTICS_READY" if len(directional) >= 30 else "DIAGNOSTICS_BUILDING"
    return BacktestDiagnostics(
        run_id=run_id,
        generated_utc=utc_now_iso(),
        status=status,
        total_rows=int(len(df)),
        complete_rows=int(len(complete)),
        directional_samples=int(len(directional)),
        avg_24h_return_pct=float(overall.get("avg_return_pct", 0.0)),
        directional_win_rate=float(overall.get("win_rate", 0.0)),
        target_1_hit_rate=float(overall.get("target_1_hit_rate", 0.0)),
        stop_hit_rate=float(overall.get("stop_hit_rate", 0.0)),
        mfe_mean_pct=float(overall.get("mfe_mean_pct", 0.0)),
        mae_mean_pct=float(overall.get("mae_mean_pct", 0.0)),
        best_holding_period=str(best_hold.get("holding_period", "")),
        best_holding_avg_return_pct=float(best_hold.get("avg_return_pct", 0.0) or 0.0),
        tables=tables,
        blockers=blockers,
        warnings=warnings,
        recommendations=recs,
    )


def _format_rows(rows: List[Dict], label_key: str, limit: int = 10) -> List[str]:
    lines = []
    for row in rows[:limit]:
        label = row.get(label_key, "")
        lines.append(
            f"- {label}: samples={row.get('samples')} | win={row.get('win_rate')}% | "
            f"avg24h={row.get('avg_return_pct')}% | T1={row.get('target_1_hit_rate')}% | "
            f"Stop={row.get('stop_hit_rate')}% | MFE/MAE={row.get('mfe_mae_ratio')}"
        )
    return lines


def format_diagnostics_console(diag: BacktestDiagnostics, *, detail: bool = True) -> str:
    lines = []
    lines.append("=" * 110)
    lines.append("🧪 Freakto Backtest Diagnostics & Edge Breakdown v5.3.1")
    lines.append("=" * 110)
    lines.append(f"Status                 : {diag.status}")
    lines.append(f"Run ID                 : {diag.run_id}")
    lines.append(f"Rows / Complete        : {diag.total_rows} / {diag.complete_rows}")
    lines.append(f"Directional Samples    : {diag.directional_samples}")
    lines.append(f"Directional Win Rate   : {diag.directional_win_rate:.2f}%")
    lines.append(f"Target 1 Hit Rate      : {diag.target_1_hit_rate:.2f}%")
    lines.append(f"Stop Hit Rate          : {diag.stop_hit_rate:.2f}%")
    lines.append(f"Avg 24h Return         : {diag.avg_24h_return_pct:.4f}%")
    lines.append(f"MFE / MAE Mean         : {diag.mfe_mean_pct:.4f}% / {diag.mae_mean_pct:.4f}%")
    if diag.best_holding_period:
        lines.append(f"Best Holding Period    : {diag.best_holding_period} ({diag.best_holding_avg_return_pct:.4f}%)")

    sections = [
        ("By Holding Period", "by_holding_period", "holding_period"),
        ("By Side", "by_side", "side"),
        ("By Symbol", "by_symbol", "symbol"),
        ("By Symbol + Side", "by_symbol_side", "symbol_side"),
        ("By Actionability", "by_actionability", "actionability"),
        ("By Score Bucket", "by_score_bucket", "score_bucket"),
        ("By Target/Stop Path", "by_target_stop_path", "path_outcome"),
    ]
    if detail:
        sections += [
            ("By Confidence", "by_confidence", "confidence_label"),
            ("By Risk Label", "by_risk_label", "risk_label"),
            ("By Trend Bucket", "by_trend_score_bucket", "trend_score_bucket"),
            ("By Momentum Bucket", "by_momentum_score_bucket", "momentum_score_bucket"),
            ("By Volume Bucket", "by_volume_score_bucket", "volume_score_bucket"),
            ("By Structure Bucket", "by_structure_score_bucket", "structure_score_bucket"),
            ("By Historical Edge Bucket", "by_historical_edge_score_bucket", "historical_edge_score_bucket"),
        ]

    for title, key, label_key in sections:
        rows = diag.tables.get(key, [])
        if not rows:
            continue
        lines.append("")
        lines.append(f"{title}:")
        lines.extend(_format_rows(rows, label_key, limit=10))

    if diag.blockers:
        lines.append("")
        lines.append("Research Blockers:")
        for blocker in diag.blockers:
            lines.append(f"⛔ {blocker}")

    if diag.recommendations:
        lines.append("")
        lines.append("Diagnostic Recommendations:")
        for rec in diag.recommendations:
            lines.append(f"→ {rec}")

    if diag.warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in diag.warnings:
            lines.append(f"⚠️ {warning}")
    lines.append("=" * 110)
    return "\n".join(lines)


def format_diagnostics_report(diag: BacktestDiagnostics) -> str:
    lines = []
    lines.append("# Freakto Backtest Diagnostics & Edge Breakdown v5.3.1")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Status: `{diag.status}`")
    lines.append(f"- Generated UTC: `{diag.generated_utc}`")
    lines.append(f"- Rows / Complete: `{diag.total_rows}/{diag.complete_rows}`")
    lines.append(f"- Directional Samples: `{diag.directional_samples}`")
    lines.append(f"- Directional Win Rate: `{diag.directional_win_rate:.2f}%`")
    lines.append(f"- Target 1 Hit Rate: `{diag.target_1_hit_rate:.2f}%`")
    lines.append(f"- Stop Hit Rate: `{diag.stop_hit_rate:.2f}%`")
    lines.append(f"- Avg 24h Return: `{diag.avg_24h_return_pct:.4f}%`")
    lines.append(f"- MFE / MAE Mean: `{diag.mfe_mean_pct:.4f}% / {diag.mae_mean_pct:.4f}%`")
    lines.append(f"- Best Holding Period: `{diag.best_holding_period}` `{diag.best_holding_avg_return_pct:.4f}%`")
    lines.append("")

    table_specs = [
        ("By Holding Period", "by_holding_period", "holding_period"),
        ("By Side", "by_side", "side"),
        ("By Symbol", "by_symbol", "symbol"),
        ("By Symbol + Side", "by_symbol_side", "symbol_side"),
        ("By Actionability", "by_actionability", "actionability"),
        ("By Score Bucket", "by_score_bucket", "score_bucket"),
        ("By Target/Stop Path", "by_target_stop_path", "path_outcome"),
        ("By Confidence", "by_confidence", "confidence_label"),
        ("By Risk Label", "by_risk_label", "risk_label"),
        ("By Trend Bucket", "by_trend_score_bucket", "trend_score_bucket"),
        ("By Momentum Bucket", "by_momentum_score_bucket", "momentum_score_bucket"),
        ("By Volume Bucket", "by_volume_score_bucket", "volume_score_bucket"),
        ("By Structure Bucket", "by_structure_score_bucket", "structure_score_bucket"),
        ("By Historical Edge Bucket", "by_historical_edge_score_bucket", "historical_edge_score_bucket"),
    ]
    for title, key, label_key in table_specs:
        rows = diag.tables.get(key, [])
        if not rows:
            continue
        lines.append(f"## {title}")
        lines.append("| Group | Samples | Win | Avg 24h | Median | T1 Hit | Stop | MFE | MAE | MFE/MAE |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for row in rows[:30]:
            lines.append(
                f"| {row.get(label_key)} | {row.get('samples')} | {row.get('win_rate')}% | "
                f"{row.get('avg_return_pct')}% | {row.get('median_return_pct')}% | "
                f"{row.get('target_1_hit_rate')}% | {row.get('stop_hit_rate')}% | "
                f"{row.get('mfe_mean_pct')}% | {row.get('mae_mean_pct')}% | {row.get('mfe_mae_ratio')} |"
            )
        lines.append("")

    lines.append("## Research Blockers")
    if diag.blockers:
        for item in diag.blockers:
            lines.append(f"- {item}")
    else:
        lines.append("- No major diagnostic blockers.")
    lines.append("")
    lines.append("## Recommendations")
    for item in diag.recommendations:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Safety Notes")
    for item in diag.warnings:
        lines.append(f"- {item}")
    return "\n".join(lines)


def save_backtest_diagnostics(diag: BacktestDiagnostics) -> Tuple[Path, Path]:
    DIAG_DIR.mkdir(parents=True, exist_ok=True)
    json_path = DIAG_DIR / f"backtest_diagnostics_{diag.run_id}.json"
    report_path = DIAG_DIR / f"backtest_diagnostics_report_{diag.run_id}.md"
    json_path.write_text(json.dumps(asdict(diag), ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(format_diagnostics_report(diag), encoding="utf-8")
    return json_path, report_path
