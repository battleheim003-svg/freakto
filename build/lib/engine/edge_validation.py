"""
engine.edge_validation

Freakto v4.7.1 Edge Validation Engine

This module validates whether logged decisions and paper trades show a measurable
edge. It does not trade, optimize weights, or claim future performance. It turns
raw logs into statistical diagnostics that are useful before any live test.
Metric names are explicit: decision win rate means Directional Win Rate,
while target-hit rates are shown separately.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

LOGS_DIR = Path("logs")
EDGE_DIR = LOGS_DIR / "edge_validation"
DECISION_EVALS_FILE = LOGS_DIR / "decision_evaluations.csv"
PAPER_EVALS_FILE = LOGS_DIR / "paper_trade_evaluations.csv"


@dataclass
class EdgeMetrics:
    source: str
    unit: str
    win_rate_label: str = "Directional Win Rate"
    sample_count: int = 0
    win_count: int = 0
    loss_count: int = 0
    flat_count: int = 0
    win_rate: float = 0.0
    avg_return: float = 0.0
    median_return: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    best_return: float = 0.0
    worst_return: float = 0.0
    expectancy: float = 0.0
    profit_factor: float = 0.0
    sharpe_like: float = 0.0
    sortino_like: float = 0.0
    max_drawdown: float = 0.0
    stop_hit_rate: float = 0.0
    target_1_hit_rate: float = 0.0
    target_2_hit_rate: float = 0.0
    target_3_hit_rate: float = 0.0
    avg_mfe_pct: float = 0.0
    avg_mae_pct: float = 0.0
    quality: str = "NO_DATA"
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass
class EdgeValidationResult:
    created_utc: str
    decision_edge: EdgeMetrics
    paper_edge: EdgeMetrics
    combined_quality: str
    overall_notes: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _bool_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series([False] * len(df), index=df.index)
    return df[column].astype(str).str.lower().isin(["true", "1", "yes", "y", "win"])


def _safe_mean(values: pd.Series) -> float:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    return round(float(clean.mean()), 4) if not clean.empty else 0.0


def _safe_median(values: pd.Series) -> float:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    return round(float(clean.median()), 4) if not clean.empty else 0.0


def _profit_factor(returns: pd.Series) -> float:
    returns = pd.to_numeric(returns, errors="coerce").dropna()
    if returns.empty:
        return 0.0
    gross_profit = float(returns[returns > 0].sum())
    gross_loss = abs(float(returns[returns < 0].sum()))
    if gross_profit <= 0 and gross_loss <= 0:
        return 0.0
    if gross_loss == 0:
        return round(gross_profit, 4) if gross_profit else 0.0
    return round(gross_profit / gross_loss, 4)


def _sharpe_like(returns: pd.Series) -> float:
    r = pd.to_numeric(returns, errors="coerce").dropna()
    if len(r) < 2:
        return 0.0
    std = float(r.std(ddof=1))
    if std == 0:
        return 0.0
    return round(float(r.mean()) / std * math.sqrt(len(r)), 4)


def _sortino_like(returns: pd.Series) -> float:
    r = pd.to_numeric(returns, errors="coerce").dropna()
    if len(r) < 2:
        return 0.0
    downside = r[r < 0]
    if len(downside) < 2:
        return 0.0
    std = float(downside.std(ddof=1))
    if std == 0:
        return 0.0
    return round(float(r.mean()) / std * math.sqrt(len(r)), 4)


def _max_drawdown(returns: pd.Series) -> float:
    r = pd.to_numeric(returns, errors="coerce").fillna(0.0)
    if r.empty:
        return 0.0
    equity = r.cumsum()
    peak = equity.cummax()
    drawdown = equity - peak
    return round(float(drawdown.min()), 4)


def _quality(sample_count: int, win_rate: float, expectancy: float, profit_factor: float, stop_hit_rate: float) -> str:
    if sample_count <= 0:
        return "NO_DATA"
    if sample_count < 30:
        if expectancy > 0 and win_rate >= 55:
            return "EARLY_POSITIVE_LOW_SAMPLE"
        return "LOW_SAMPLE"
    if sample_count < 100:
        if expectancy > 0 and win_rate >= 55 and profit_factor >= 1.1 and stop_hit_rate <= 35:
            return "VALIDATING_POSITIVE"
        if expectancy > 0:
            return "MIXED_VALIDATION"
        return "WEAK_VALIDATION"
    if expectancy > 0 and win_rate >= 55 and profit_factor >= 1.2 and stop_hit_rate <= 35:
        return "ROBUST_POSITIVE"
    if expectancy > 0:
        return "POSITIVE_BUT_NEEDS_FILTERING"
    return "NO_EDGE_CONFIRMED"


def _metrics_from_returns(
    *,
    source: str,
    unit: str,
    returns: pd.Series,
    stop_hits: Optional[pd.Series] = None,
    t1_hits: Optional[pd.Series] = None,
    t2_hits: Optional[pd.Series] = None,
    t3_hits: Optional[pd.Series] = None,
    mfe: Optional[pd.Series] = None,
    mae: Optional[pd.Series] = None,
    win_rate_label: str = "Directional Win Rate",
) -> EdgeMetrics:
    r = pd.to_numeric(returns, errors="coerce").dropna()
    sample_count = len(r)
    if sample_count == 0:
        return EdgeMetrics(source=source, unit=unit, win_rate_label=win_rate_label, warnings=["داده قابل محاسبه وجود ندارد."])

    wins = r[r > 0]
    losses = r[r < 0]
    flat = r[r == 0]
    win_rate = round(len(wins) / sample_count * 100, 2) if sample_count else 0.0
    avg_return = round(float(r.mean()), 4)
    pf = _profit_factor(r)

    if stop_hits is not None and len(stop_hits):
        stop_hit_rate = round(float(stop_hits.reindex(r.index, fill_value=False).mean() * 100), 2)
    else:
        stop_hit_rate = 0.0

    metrics = EdgeMetrics(
        source=source,
        unit=unit,
        win_rate_label=win_rate_label,
        sample_count=sample_count,
        win_count=len(wins),
        loss_count=len(losses),
        flat_count=len(flat),
        win_rate=win_rate,
        avg_return=avg_return,
        median_return=_safe_median(r),
        avg_win=round(float(wins.mean()), 4) if not wins.empty else 0.0,
        avg_loss=round(float(losses.mean()), 4) if not losses.empty else 0.0,
        best_return=round(float(r.max()), 4),
        worst_return=round(float(r.min()), 4),
        expectancy=avg_return,
        profit_factor=pf,
        sharpe_like=_sharpe_like(r),
        sortino_like=_sortino_like(r),
        max_drawdown=_max_drawdown(r),
        stop_hit_rate=stop_hit_rate,
        target_1_hit_rate=round(float(t1_hits.reindex(r.index, fill_value=False).mean() * 100), 2) if t1_hits is not None and len(t1_hits) else 0.0,
        target_2_hit_rate=round(float(t2_hits.reindex(r.index, fill_value=False).mean() * 100), 2) if t2_hits is not None and len(t2_hits) else 0.0,
        target_3_hit_rate=round(float(t3_hits.reindex(r.index, fill_value=False).mean() * 100), 2) if t3_hits is not None and len(t3_hits) else 0.0,
        avg_mfe_pct=_safe_mean(mfe.reindex(r.index)) if mfe is not None and len(mfe) else 0.0,
        avg_mae_pct=_safe_mean(mae.reindex(r.index)) if mae is not None and len(mae) else 0.0,
    )

    metrics.quality = _quality(sample_count, metrics.win_rate, metrics.expectancy, metrics.profit_factor, metrics.stop_hit_rate)

    if sample_count < 30:
        metrics.warnings.append("نمونه کمتر از 30 است؛ نتیجه فقط سیگنال اولیه است.")
    elif sample_count < 100:
        metrics.warnings.append("نمونه هنوز کمتر از 100 است؛ برای تصمیم عملی باید داده بیشتری جمع شود.")

    if metrics.profit_factor < 1.0 and sample_count >= 10:
        metrics.warnings.append("Profit Factor زیر 1 است؛ Edge قابل اتکا نیست.")
    if metrics.max_drawdown < -5 and unit == "pct":
        metrics.warnings.append("افت تجمعی قابل توجه دیده شده است؛ کنترل ریسک باید بررسی شود.")
    if metrics.expectancy > 0 and metrics.win_rate >= 55:
        metrics.notes.append(f"Expectancy و {metrics.win_rate_label} فعلاً مثبت هستند.")
    else:
        metrics.notes.append("Edge مثبت قطعی هنوز تأیید نشده است.")

    return metrics


def decision_edge_metrics() -> EdgeMetrics:
    df = _load_csv(DECISION_EVALS_FILE)
    if df.empty:
        return EdgeMetrics(source="decision_evaluations", unit="pct", warnings=["logs/decision_evaluations.csv پیدا نشد یا خالی است."])
    if "evaluation_status" in df.columns:
        df = df[df["evaluation_status"].astype(str) == "COMPLETE"].copy()
    if df.empty:
        return EdgeMetrics(source="decision_evaluations", unit="pct", warnings=["هیچ ارزیابی COMPLETE وجود ندارد."])

    returns = pd.to_numeric(df.get("return_after_24h_pct"), errors="coerce")
    if returns.dropna().empty:
        returns = pd.to_numeric(df.get("return_after_12h_pct"), errors="coerce")
    if returns.dropna().empty:
        returns = pd.to_numeric(df.get("return_after_4h_pct"), errors="coerce")

    return _metrics_from_returns(
        source="decision_evaluations",
        unit="pct",
        returns=returns,
        stop_hits=_bool_series(df, "stop_hit"),
        t1_hits=_bool_series(df, "target_1_hit"),
        t2_hits=_bool_series(df, "target_2_hit"),
        t3_hits=_bool_series(df, "target_3_hit"),
        mfe=pd.to_numeric(df.get("mfe_pct"), errors="coerce") if "mfe_pct" in df.columns else None,
        mae=pd.to_numeric(df.get("mae_pct"), errors="coerce") if "mae_pct" in df.columns else None,
        win_rate_label="Directional Win Rate",
    )


def paper_edge_metrics() -> EdgeMetrics:
    df = _load_csv(PAPER_EVALS_FILE)
    if df.empty:
        return EdgeMetrics(source="paper_trade_evaluations", unit="R", win_rate_label="Paper Trade Win Rate", warnings=["هنوز Paper Trade ارزیابی‌شده وجود ندارد."])
    if "status" in df.columns:
        df = df[df["status"].astype(str) == "CLOSED"].copy()
    if df.empty:
        return EdgeMetrics(source="paper_trade_evaluations", unit="R", win_rate_label="Paper Trade Win Rate", warnings=["Paper Trade بسته‌شده وجود ندارد."])

    if "r_multiple" in df.columns:
        returns = pd.to_numeric(df["r_multiple"], errors="coerce")
    elif "return_r" in df.columns:
        returns = pd.to_numeric(df["return_r"], errors="coerce")
    else:
        returns = pd.Series(dtype=float)

    stop_hits = df.get("result", pd.Series(dtype=str)).astype(str).str.upper().eq("LOSS") if "result" in df.columns else None

    return _metrics_from_returns(
        source="paper_trade_evaluations",
        unit="R",
        returns=returns,
        stop_hits=stop_hits,
        mfe=pd.to_numeric(df.get("mfe_pct"), errors="coerce") if "mfe_pct" in df.columns else None,
        mae=pd.to_numeric(df.get("mae_pct"), errors="coerce") if "mae_pct" in df.columns else None,
        win_rate_label="Paper Trade Win Rate",
    )


def run_edge_validation() -> EdgeValidationResult:
    decision = decision_edge_metrics()
    paper = paper_edge_metrics()
    blockers: List[str] = []
    notes: List[str] = []

    if decision.sample_count < 100:
        blockers.append(f"Decision COMPLETE کمتر از 100 است: {decision.sample_count}")
    if paper.sample_count < 30:
        blockers.append(f"Paper trades بسته‌شده کمتر از 30 است: {paper.sample_count}")

    if decision.expectancy > 0 and decision.win_rate >= 55:
        notes.append("Decision Directional Win Rate و Expectancy فعلاً مثبت‌اند، اما تا رسیدن به نمونه کافی فقط تحقیقاتی محسوب می‌شوند.")
    if paper.sample_count == 0:
        notes.append("Paper edge هنوز شروع نشده یا معامله بسته‌شده ندارد.")
    elif paper.expectancy > 0:
        notes.append("Paper edge فعلاً مثبت است؛ باید با نمونه بیشتر تأیید شود.")

    if not blockers and decision.quality in {"ROBUST_POSITIVE", "POSITIVE_BUT_NEEDS_FILTERING"} and paper.expectancy > 0:
        quality = "LIVE_VALIDATION_CANDIDATE"
    elif decision.expectancy > 0 or paper.expectancy > 0:
        quality = "EARLY_EDGE_OBSERVED"
    else:
        quality = "NO_VALIDATED_EDGE"

    return EdgeValidationResult(
        created_utc=datetime.now(timezone.utc).isoformat(),
        decision_edge=decision,
        paper_edge=paper,
        combined_quality=quality,
        overall_notes=notes,
        blockers=blockers,
    )


def save_edge_validation(result: EdgeValidationResult) -> tuple[Path, Path]:
    EDGE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = EDGE_DIR / f"edge_validation_{stamp}.json"
    report_path = EDGE_DIR / f"edge_validation_report_{stamp}.md"

    json_path.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(format_edge_validation_report(result), encoding="utf-8")
    return json_path, report_path


def _format_metric_block(lines: List[str], m: EdgeMetrics) -> None:
    lines.append("-" * 110)
    lines.append(f"Source       : {m.source}")
    lines.append(f"Quality      : {m.quality}")
    row_label = "Positive/Negative/Flat" if m.unit == "pct" else "Wins/Losses/Flat"
    lines.append(f"Samples      : {m.sample_count} | {row_label}: {m.win_count}/{m.loss_count}/{m.flat_count}")
    lines.append(f"{m.win_rate_label:<13}: {m.win_rate:.2f}%")
    lines.append(f"Expectancy   : {m.expectancy:.4f}{m.unit}")
    lines.append(f"ProfitFactor : {m.profit_factor:.4f}")
    lines.append(f"Sharpe-like  : {m.sharpe_like:.4f} | Sortino-like: {m.sortino_like:.4f}")
    lines.append(f"Max Drawdown : {m.max_drawdown:.4f}{m.unit}")
    lines.append(f"Best/Worst   : {m.best_return:.4f}{m.unit} / {m.worst_return:.4f}{m.unit}")
    lines.append(f"Avg Win/Loss : {m.avg_win:.4f}{m.unit} / {m.avg_loss:.4f}{m.unit}")
    lines.append(f"Stop Rate    : {m.stop_hit_rate:.2f}%")
    if m.unit == "pct":
        lines.append(f"Target Hit   : T1 {m.target_1_hit_rate:.2f}% | T2 {m.target_2_hit_rate:.2f}% | T3 {m.target_3_hit_rate:.2f}%")
        lines.append("Definition   : Directional Win = positive evaluated return; Target Hit = target_1_hit.")
        lines.append(f"MFE/MAE Avg  : {m.avg_mfe_pct:.4f}% / {m.avg_mae_pct:.4f}%")
    elif m.unit == "R":
        lines.append("Definition   : Paper Trade Win = closed paper trades with positive R multiple.")
    for note in m.notes[:3]:
        lines.append(f"Note         : {note}")
    for warning in m.warnings[:4]:
        lines.append(f"Warning      : {warning}")


def format_edge_validation_console(result: EdgeValidationResult) -> str:
    lines: List[str] = []
    lines.append("=" * 110)
    lines.append("📐 Freakto Edge Validation Engine v4.7.1")
    lines.append("=" * 110)
    lines.append(f"Created UTC      : {result.created_utc}")
    lines.append(f"Combined Quality : {result.combined_quality}")
    lines.append("")
    _format_metric_block(lines, result.decision_edge)
    _format_metric_block(lines, result.paper_edge)
    if result.overall_notes:
        lines.append("")
        lines.append("Overall Notes:")
        for note in result.overall_notes:
            lines.append(f"✓ {note}")
    if result.blockers:
        lines.append("")
        lines.append("Validation Blockers:")
        for blocker in result.blockers:
            lines.append(f"⛔ {blocker}")
    lines.append("=" * 110)
    return "\n".join(lines)


def format_edge_validation_report(result: EdgeValidationResult) -> str:
    lines = ["# Freakto Edge Validation Engine v4.7.1", "", f"Created UTC: {result.created_utc}", "", f"Combined Quality: **{result.combined_quality}**", ""]
    for m in [result.decision_edge, result.paper_edge]:
        lines.append(f"## {m.source}")
        lines.append(f"- Quality: {m.quality}")
        lines.append(f"- Samples: {m.sample_count}")
        lines.append(f"- {m.win_rate_label}: {m.win_rate:.2f}%")
        lines.append(f"- Expectancy: {m.expectancy:.4f}{m.unit}")
        lines.append(f"- Profit Factor: {m.profit_factor:.4f}")
        lines.append(f"- Sharpe-like: {m.sharpe_like:.4f}")
        lines.append(f"- Sortino-like: {m.sortino_like:.4f}")
        lines.append(f"- Max Drawdown: {m.max_drawdown:.4f}{m.unit}")
        lines.append(f"- Stop Hit Rate: {m.stop_hit_rate:.2f}%")
        if m.unit == "pct":
            lines.append(f"- Target 1 Hit Rate: {m.target_1_hit_rate:.2f}%")
            lines.append("- Definition: Directional Win Rate is based on positive evaluated return; Target 1 Hit Rate is based on `target_1_hit`.")
        elif m.unit == "R":
            lines.append("- Definition: Paper Trade Win Rate is based on closed paper trades with positive R multiple.")
        for note in m.notes:
            lines.append(f"- Note: {note}")
        for warning in m.warnings:
            lines.append(f"- Warning: {warning}")
        lines.append("")
    if result.blockers:
        lines.append("## Blockers")
        for blocker in result.blockers:
            lines.append(f"- {blocker}")
    if result.overall_notes:
        lines.append("## Notes")
        for note in result.overall_notes:
            lines.append(f"- {note}")
    return "\n".join(lines)
