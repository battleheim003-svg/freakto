"""
engine.monte_carlo

Freakto v5.0 Monte Carlo Risk Lab

Bootstraps past evaluated returns or paper-trade R multiples to estimate possible
future paths. This is a risk/research tool, not a forecast and not a trading
permission system.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd

LOGS_DIR = Path("logs")
MC_DIR = LOGS_DIR / "monte_carlo"
DECISION_EVALS_FILE = LOGS_DIR / "decision_evaluations.csv"
PAPER_EVALS_FILE = LOGS_DIR / "paper_trade_evaluations.csv"


@dataclass
class MonteCarloResult:
    created_utc: str
    source: str
    unit: str
    sample_count: int
    iterations: int
    trades_per_run: int
    initial_equity: float
    median_final: float
    mean_final: float
    p05_final: float
    p95_final: float
    median_max_drawdown: float
    p95_max_drawdown: float
    probability_of_loss_pct: float
    probability_of_ruin_pct: float
    risk_of_ruin_threshold: float
    expected_per_trade: float
    best_sample: float
    worst_sample: float
    risk_quality: str
    notes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _return_column(frame: pd.DataFrame) -> Optional[str]:
    for column in ["return_after_24h_pct", "return_after_12h_pct", "return_after_4h_pct"]:
        if column in frame.columns and pd.to_numeric(frame[column], errors="coerce").notna().any():
            return column
    return None


def _load_sample_returns(prefer_paper: bool = True) -> tuple[str, str, pd.Series]:
    paper = _load_csv(PAPER_EVALS_FILE)
    if prefer_paper and not paper.empty:
        for col in ["r_multiple", "r", "result_r", "return_r"]:
            if col in paper.columns:
                r = pd.to_numeric(paper[col], errors="coerce").dropna()
                if not r.empty:
                    return "paper_trade_evaluations", "R", r
    decisions = _load_csv(DECISION_EVALS_FILE)
    if not decisions.empty:
        if "evaluation_status" in decisions.columns:
            decisions = decisions[decisions["evaluation_status"].astype(str).str.upper() == "COMPLETE"].copy()
        col = _return_column(decisions)
        if col:
            r = pd.to_numeric(decisions[col], errors="coerce").dropna()
            if not r.empty:
                return "decision_evaluations_fallback", "pct", r
    return "NO_DATA", "unit", pd.Series(dtype="float64")


def _max_drawdown(path: np.ndarray) -> float:
    peak = np.maximum.accumulate(path)
    dd = path - peak
    return float(dd.min()) if len(dd) else 0.0


def run_monte_carlo(iterations: int = 2000, trades_per_run: int = 100, seed: int = 42, prefer_paper: bool = True, ruin_threshold: float = -10.0) -> MonteCarloResult:
    source, unit, returns = _load_sample_returns(prefer_paper=prefer_paper)
    returns = pd.to_numeric(returns, errors="coerce").dropna()
    if returns.empty:
        return MonteCarloResult(
            created_utc=datetime.now(timezone.utc).isoformat(),
            source=source,
            unit=unit,
            sample_count=0,
            iterations=iterations,
            trades_per_run=trades_per_run,
            initial_equity=0.0,
            median_final=0.0,
            mean_final=0.0,
            p05_final=0.0,
            p95_final=0.0,
            median_max_drawdown=0.0,
            p95_max_drawdown=0.0,
            probability_of_loss_pct=0.0,
            probability_of_ruin_pct=0.0,
            risk_of_ruin_threshold=ruin_threshold,
            expected_per_trade=0.0,
            best_sample=0.0,
            worst_sample=0.0,
            risk_quality="NO_DATA",
            warnings=["برای Monte Carlo داده‌ای وجود ندارد."],
            blockers=["paper_trade_evaluations یا decision_evaluations معتبر پیدا نشد."],
        )

    sample = returns.to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    terminal = np.zeros(iterations)
    max_dd = np.zeros(iterations)
    for i in range(iterations):
        draws = rng.choice(sample, size=trades_per_run, replace=True)
        equity = np.cumsum(draws)
        terminal[i] = equity[-1]
        max_dd[i] = _max_drawdown(equity)

    probability_loss = float((terminal < 0).mean() * 100.0)
    probability_ruin = float((max_dd <= ruin_threshold).mean() * 100.0)

    notes: List[str] = []
    warnings: List[str] = []
    blockers: List[str] = []
    n = len(sample)
    if n < 30:
        warnings.append(f"نمونه Monte Carlo کمتر از 30 است: {n}")
    if source == "decision_evaluations_fallback":
        warnings.append("Paper Trade کافی نبود؛ شبیه‌سازی با decision returns درصدی انجام شد، نه R واقعی.")
    if probability_ruin >= 20:
        quality = "HIGH_RISK"
        blockers.append(f"Probability of ruin بالاست: {probability_ruin:.2f}%")
    elif probability_loss >= 35:
        quality = "MIXED_RISK"
        warnings.append(f"Probability of loss قابل توجه است: {probability_loss:.2f}%")
    elif n < 30:
        quality = "LOW_SAMPLE_RISK_MODEL"
    elif float(np.median(terminal)) > 0 and probability_ruin < 10:
        quality = "RISK_PROFILE_ACCEPTABLE"
        notes.append("Median path مثبت و Probability of ruin پایین است.")
    else:
        quality = "RISK_PROFILE_UNCONFIRMED"

    return MonteCarloResult(
        created_utc=datetime.now(timezone.utc).isoformat(),
        source=source,
        unit=unit,
        sample_count=int(n),
        iterations=int(iterations),
        trades_per_run=int(trades_per_run),
        initial_equity=0.0,
        median_final=round(float(np.median(terminal)), 4),
        mean_final=round(float(np.mean(terminal)), 4),
        p05_final=round(float(np.percentile(terminal, 5)), 4),
        p95_final=round(float(np.percentile(terminal, 95)), 4),
        median_max_drawdown=round(float(np.median(max_dd)), 4),
        p95_max_drawdown=round(float(np.percentile(max_dd, 5)), 4),
        probability_of_loss_pct=round(probability_loss, 2),
        probability_of_ruin_pct=round(probability_ruin, 2),
        risk_of_ruin_threshold=round(float(ruin_threshold), 4),
        expected_per_trade=round(float(np.mean(sample)), 4),
        best_sample=round(float(np.max(sample)), 4),
        worst_sample=round(float(np.min(sample)), 4),
        risk_quality=quality,
        notes=notes,
        warnings=warnings,
        blockers=blockers,
    )


def format_monte_carlo_console(result: MonteCarloResult) -> str:
    lines: List[str] = []
    lines.append("=" * 110)
    lines.append("🎲 Freakto Monte Carlo Risk Lab v5.0")
    lines.append("=" * 110)
    lines.append(f"Created UTC      : {result.created_utc}")
    lines.append(f"Risk Quality     : {result.risk_quality}")
    lines.append(f"Source           : {result.source} ({result.unit})")
    lines.append(f"Samples          : {result.sample_count}")
    lines.append(f"Iterations       : {result.iterations}")
    lines.append(f"Trades / Run     : {result.trades_per_run}")
    lines.append(f"Expected / Trade : {result.expected_per_trade:.4f}{result.unit}")
    lines.append(f"Best / Worst Samp: {result.best_sample:.4f}{result.unit} / {result.worst_sample:.4f}{result.unit}")
    lines.append("-" * 110)
    lines.append(f"Median Final     : {result.median_final:.4f}{result.unit}")
    lines.append(f"Mean Final       : {result.mean_final:.4f}{result.unit}")
    lines.append(f"P05 / P95 Final  : {result.p05_final:.4f}{result.unit} / {result.p95_final:.4f}{result.unit}")
    lines.append(f"Median Max DD    : {result.median_max_drawdown:.4f}{result.unit}")
    lines.append(f"P95 Max DD       : {result.p95_max_drawdown:.4f}{result.unit}")
    lines.append(f"Prob Loss        : {result.probability_of_loss_pct:.2f}%")
    lines.append(f"Prob Ruin        : {result.probability_of_ruin_pct:.2f}% | Threshold {result.risk_of_ruin_threshold:.2f}{result.unit}")
    if result.notes:
        lines.append("")
        lines.append("Notes:")
        for note in result.notes:
            lines.append(f"✓ {note}")
    if result.warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in result.warnings:
            lines.append(f"⚠️ {warning}")
    if result.blockers:
        lines.append("")
        lines.append("Blockers:")
        for blocker in result.blockers:
            lines.append(f"⛔ {blocker}")
    lines.append("=" * 110)
    return "\n".join(lines)


def format_monte_carlo_report(result: MonteCarloResult) -> str:
    lines = ["# Freakto Monte Carlo Risk Lab v5.0", "", f"Created UTC: {result.created_utc}", ""]
    lines.append(f"- Risk Quality: **{result.risk_quality}**")
    lines.append(f"- Source: {result.source} ({result.unit})")
    lines.append(f"- Samples: {result.sample_count}")
    lines.append(f"- Iterations: {result.iterations}")
    lines.append(f"- Trades per Run: {result.trades_per_run}")
    lines.append(f"- Expected per Trade: {result.expected_per_trade:.4f}{result.unit}")
    lines.append(f"- Median Final: {result.median_final:.4f}{result.unit}")
    lines.append(f"- P05/P95 Final: {result.p05_final:.4f}{result.unit} / {result.p95_final:.4f}{result.unit}")
    lines.append(f"- Median Max Drawdown: {result.median_max_drawdown:.4f}{result.unit}")
    lines.append(f"- P95 Max Drawdown: {result.p95_max_drawdown:.4f}{result.unit}")
    lines.append(f"- Probability of Loss: {result.probability_of_loss_pct:.2f}%")
    lines.append(f"- Probability of Ruin: {result.probability_of_ruin_pct:.2f}%")
    if result.warnings:
        lines.append("\n## Warnings")
        for w in result.warnings:
            lines.append(f"- {w}")
    if result.blockers:
        lines.append("\n## Blockers")
        for b in result.blockers:
            lines.append(f"- {b}")
    return "\n".join(lines)


def save_monte_carlo(result: MonteCarloResult) -> tuple[Path, Path]:
    MC_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = MC_DIR / f"monte_carlo_{stamp}.json"
    report_path = MC_DIR / f"monte_carlo_report_{stamp}.md"
    json_path.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(format_monte_carlo_report(result), encoding="utf-8")
    return json_path, report_path
