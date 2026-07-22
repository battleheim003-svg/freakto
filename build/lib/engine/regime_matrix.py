"""
engine.regime_matrix

Freakto v4.7.1 Regime Performance Matrix

Builds a performance matrix by market regime, side, and actionability. It uses
logged decision evaluations and joins decisions.csv when available. New decisions
logged after v4.7 include regime fields; old rows without regime data are grouped
under UNKNOWN.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import pandas as pd

LOGS_DIR = Path("logs")
REGIME_DIR = LOGS_DIR / "regime_matrix"
DECISIONS_FILE = LOGS_DIR / "decisions.csv"
EVALS_FILE = LOGS_DIR / "decision_evaluations.csv"


@dataclass
class RegimeMatrixRow:
    regime: str
    side: str
    actionability: str
    samples: int
    # Legacy win_rate equals Target 1 Hit Rate.
    win_rate: float
    directional_win_rate: float
    avg_24h_return_pct: float
    profit_factor: float
    stop_hit_rate: float
    avg_score: float
    avg_mfe_pct: float
    avg_mae_pct: float
    verdict: str
    notes: List[str] = field(default_factory=list)


@dataclass
class RegimeMatrixResult:
    created_utc: str
    rows: List[RegimeMatrixRow]
    known_regime_samples: int
    unknown_regime_samples: int
    best_regime: str = "UNKNOWN"
    worst_regime: str = "UNKNOWN"
    overall_verdict: str = "NO_DATA"
    warnings: List[str] = field(default_factory=list)


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
    return df[column].astype(str).str.lower().isin(["true", "1", "yes", "y"])


def _profit_factor(returns: pd.Series) -> float:
    r = pd.to_numeric(returns, errors="coerce").dropna()
    if r.empty:
        return 0.0
    gp = float(r[r > 0].sum())
    gl = abs(float(r[r < 0].sum()))
    if gp <= 0 and gl <= 0:
        return 0.0
    if gl == 0:
        return round(gp, 4) if gp else 0.0
    return round(gp / gl, 4)


def _avg(series: pd.Series) -> float:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    return round(float(clean.mean()), 4) if not clean.empty else 0.0


def _load_joined_complete() -> pd.DataFrame:
    evals = _load_csv(EVALS_FILE)
    if evals.empty:
        return pd.DataFrame()
    if "evaluation_status" in evals.columns:
        evals = evals[evals["evaluation_status"].astype(str) == "COMPLETE"].copy()
    if evals.empty:
        return evals

    decisions = _load_csv(DECISIONS_FILE)
    if not decisions.empty and "decision_id" in evals.columns and "decision_id" in decisions.columns:
        keep = [
            c for c in [
                "decision_id",
                "regime_label",
                "regime_confidence",
                "score",
                "side",
                "actionability",
                "trend_score",
                "momentum_score",
                "volume_score",
                "structure_score",
                "provider",
            ]
            if c in decisions.columns
        ]
        decisions = decisions[keep].drop_duplicates(subset=["decision_id"], keep="last")
        evals = evals.merge(decisions, on="decision_id", how="left", suffixes=("", "_decision"))

    if "regime_label" not in evals.columns:
        evals["regime_label"] = "UNKNOWN"
    evals["regime_label"] = evals["regime_label"].fillna("UNKNOWN").astype(str).replace({"": "UNKNOWN", "nan": "UNKNOWN", "None": "UNKNOWN"})

    if "side" not in evals.columns and "side_decision" in evals.columns:
        evals["side"] = evals["side_decision"]
    elif "side_decision" in evals.columns:
        evals["side"] = evals["side"].fillna(evals["side_decision"])

    if "actionability" not in evals.columns and "actionability_decision" in evals.columns:
        evals["actionability"] = evals["actionability_decision"]
    elif "actionability_decision" in evals.columns:
        evals["actionability"] = evals["actionability"].fillna(evals["actionability_decision"])

    return evals


def _row_verdict(samples: int, avg24: float, target_hit_rate: float, pf: float, stop: float, regime: str) -> tuple[str, List[str]]:
    notes: List[str] = []
    if samples < 5:
        return "LOW_SAMPLE", ["نمونه کمتر از 5 است؛ فقط برای رصد." ]
    if regime == "UNKNOWN":
        notes.append("Regime در لاگ‌های قدیمی ثبت نشده؛ برای تصمیم‌گیری نیاز به داده v4.7 به بعد است.")
    if avg24 > 0 and target_hit_rate >= 55 and pf >= 1.1 and stop <= 35:
        verdict = "REGIME_POSITIVE"
        notes.append("در این رژیم نشانه اولیه Edge مثبت دیده می‌شود.")
    elif avg24 > 0:
        verdict = "MIXED_POSITIVE"
        notes.append("بازده مثبت است اما کیفیت آماری کامل نیست.")
    elif avg24 <= 0 and samples >= 10:
        verdict = "REGIME_WEAK"
        notes.append("در این رژیم فعلاً مزیت واضح دیده نمی‌شود.")
    else:
        verdict = "OBSERVE"
        notes.append("نیاز به داده بیشتر دارد.")
    return verdict, notes


def _build_row(group: pd.DataFrame, regime: str, side: str, actionability: str) -> RegimeMatrixRow:
    returns = pd.to_numeric(group.get("return_after_24h_pct"), errors="coerce")
    if returns.dropna().empty:
        returns = pd.to_numeric(group.get("return_after_12h_pct"), errors="coerce")
    if returns.dropna().empty:
        returns = pd.to_numeric(group.get("return_after_4h_pct"), errors="coerce")

    wins = _bool_series(group, "target_1_hit")
    stop = _bool_series(group, "stop_hit")
    win_rate = round(float(wins.mean() * 100), 2) if len(wins) else 0.0
    directional_win_rate = round(float((returns.dropna() > 0).mean() * 100), 2) if not returns.dropna().empty else 0.0
    stop_rate = round(float(stop.mean() * 100), 2) if len(stop) else 0.0
    avg24 = _avg(returns)
    pf = _profit_factor(returns)
    verdict, notes = _row_verdict(len(group), avg24, win_rate, pf, stop_rate, regime)

    return RegimeMatrixRow(
        regime=regime,
        side=side,
        actionability=actionability,
        samples=len(group),
        win_rate=win_rate,
        directional_win_rate=directional_win_rate,
        avg_24h_return_pct=avg24,
        profit_factor=pf,
        stop_hit_rate=stop_rate,
        avg_score=_avg(group.get("score", pd.Series(dtype=float))),
        avg_mfe_pct=_avg(group.get("mfe_pct", pd.Series(dtype=float))),
        avg_mae_pct=_avg(group.get("mae_pct", pd.Series(dtype=float))),
        verdict=verdict,
        notes=notes,
    )


def run_regime_matrix() -> RegimeMatrixResult:
    df = _load_joined_complete()
    warnings: List[str] = []
    if df.empty:
        return RegimeMatrixResult(
            created_utc=datetime.now(timezone.utc).isoformat(),
            rows=[],
            known_regime_samples=0,
            unknown_regime_samples=0,
            warnings=["هیچ decision evaluation کامل برای ساخت Regime Matrix وجود ندارد."],
        )

    for col, default in [("side", "UNKNOWN"), ("actionability", "UNKNOWN")]:
        if col not in df.columns:
            df[col] = default
        df[col] = df[col].fillna(default).astype(str).replace({"": default, "nan": default, "None": default})

    rows: List[RegimeMatrixRow] = []
    group_cols = ["regime_label", "side", "actionability"]
    for keys, group in df.groupby(group_cols, dropna=False):
        regime, side, actionability = [str(k) for k in keys]
        rows.append(_build_row(group, regime, side, actionability))

    rows.sort(key=lambda r: (r.verdict == "REGIME_POSITIVE", r.samples, r.avg_24h_return_pct), reverse=True)

    known = int((df["regime_label"].astype(str) != "UNKNOWN").sum())
    unknown = int((df["regime_label"].astype(str) == "UNKNOWN").sum())
    if unknown > known:
        warnings.append("بیشتر نمونه‌ها regime_label ندارند؛ چند اجرای جدید monitor.py بعد از v4.7 لازم است.")

    regime_summary = []
    for regime, group in df.groupby("regime_label"):
        returns = pd.to_numeric(group.get("return_after_24h_pct"), errors="coerce")
        regime_summary.append((str(regime), len(group), _avg(returns)))
    valid = [r for r in regime_summary if r[1] >= 5]
    if valid:
        best = max(valid, key=lambda x: x[2])[0]
        worst = min(valid, key=lambda x: x[2])[0]
    else:
        best = "UNKNOWN"
        worst = "UNKNOWN"

    if known >= 30 and any(r.verdict == "REGIME_POSITIVE" for r in rows):
        overall = "REGIME_EDGE_EMERGING"
    elif known > 0:
        overall = "REGIME_DATA_COLLECTING"
    else:
        overall = "REGIME_DATA_MISSING"

    return RegimeMatrixResult(
        created_utc=datetime.now(timezone.utc).isoformat(),
        rows=rows,
        known_regime_samples=known,
        unknown_regime_samples=unknown,
        best_regime=best,
        worst_regime=worst,
        overall_verdict=overall,
        warnings=warnings,
    )


def save_regime_matrix(result: RegimeMatrixResult) -> tuple[Path, Path]:
    REGIME_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    csv_path = REGIME_DIR / f"regime_matrix_{stamp}.csv"
    report_path = REGIME_DIR / f"regime_matrix_report_{stamp}.md"

    fields = [
        "regime", "side", "actionability", "samples", "target_1_hit_rate", "directional_win_rate", "avg_24h_return_pct",
        "profit_factor", "stop_hit_rate", "avg_score", "avg_mfe_pct", "avg_mae_pct", "verdict", "notes",
    ]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in result.rows:
            writer.writerow({
                "regime": row.regime,
                "side": row.side,
                "actionability": row.actionability,
                "samples": row.samples,
                "target_1_hit_rate": row.win_rate,
                "directional_win_rate": row.directional_win_rate,
                "avg_24h_return_pct": row.avg_24h_return_pct,
                "profit_factor": row.profit_factor,
                "stop_hit_rate": row.stop_hit_rate,
                "avg_score": row.avg_score,
                "avg_mfe_pct": row.avg_mfe_pct,
                "avg_mae_pct": row.avg_mae_pct,
                "verdict": row.verdict,
                "notes": " | ".join(row.notes),
            })

    report_path.write_text(format_regime_matrix_report(result), encoding="utf-8")
    return csv_path, report_path


def format_regime_matrix_console(result: RegimeMatrixResult) -> str:
    lines: List[str] = []
    lines.append("=" * 110)
    lines.append("🧬 Freakto Regime Performance Matrix v4.7.1")
    lines.append("=" * 110)
    lines.append(f"Created UTC          : {result.created_utc}")
    lines.append(f"Overall Verdict      : {result.overall_verdict}")
    lines.append(f"Known/Unknown Regime : {result.known_regime_samples} / {result.unknown_regime_samples}")
    lines.append(f"Best/Worst Regime    : {result.best_regime} / {result.worst_regime}")
    if result.warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in result.warnings:
            lines.append(f"⚠️ {warning}")
    if not result.rows:
        lines.append("No regime matrix rows. Run: python decision_evaluator.py")
        lines.append("=" * 110)
        return "\n".join(lines)
    for row in result.rows[:12]:
        lines.append("-" * 110)
        lines.append(f"Regime/Side/Action : {row.regime} / {row.side} / {row.actionability}")
        lines.append(f"Samples            : {row.samples}")
        lines.append(f"Target 1 Hit       : {row.win_rate:.2f}%")
        lines.append(f"Directional Win    : {row.directional_win_rate:.2f}%")
        lines.append(f"Avg 24h            : {row.avg_24h_return_pct:.4f}%")
        lines.append(f"Profit Factor      : {row.profit_factor:.4f}")
        lines.append(f"Stop Rate          : {row.stop_hit_rate:.2f}%")
        lines.append(f"Avg Score          : {row.avg_score:.2f}")
        lines.append(f"Verdict            : {row.verdict}")
        for note in row.notes[:2]:
            lines.append(f"Note               : {note}")
    lines.append("=" * 110)
    return "\n".join(lines)


def format_regime_matrix_report(result: RegimeMatrixResult) -> str:
    lines = ["# Freakto Regime Performance Matrix v4.7.1", "", f"Created UTC: {result.created_utc}", "", f"Overall Verdict: **{result.overall_verdict}**", ""]
    lines.append(f"Known/Unknown Regime Samples: {result.known_regime_samples}/{result.unknown_regime_samples}")
    lines.append(f"Best/Worst Regime: {result.best_regime}/{result.worst_regime}")
    lines.append("")
    if result.warnings:
        lines.append("## Warnings")
        for warning in result.warnings:
            lines.append(f"- {warning}")
        lines.append("")
    lines.append("## Matrix")
    for row in result.rows:
        lines.append(f"### {row.regime} / {row.side} / {row.actionability}")
        lines.append(f"- Samples: {row.samples}")
        lines.append(f"- Target 1 Hit Rate: {row.win_rate:.2f}%")
        lines.append(f"- Directional Win Rate: {row.directional_win_rate:.2f}%")
        lines.append(f"- Avg 24h Return: {row.avg_24h_return_pct:.4f}%")
        lines.append(f"- Profit Factor: {row.profit_factor:.4f}")
        lines.append(f"- Stop Hit Rate: {row.stop_hit_rate:.2f}%")
        lines.append(f"- Verdict: {row.verdict}")
        for note in row.notes:
            lines.append(f"- {note}")
        lines.append("")
    return "\n".join(lines)
