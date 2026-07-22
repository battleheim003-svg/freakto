"""
engine.portfolio_memory

Freakto v5.0 Portfolio Memory Engine

Creates symbol-level memory from portfolio scans, decisions, decision evaluations,
and paper-trade results. The goal is to answer: which symbols repeatedly produce
useful setups, which are mostly noise, and where do we need more data?
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

LOGS_DIR = Path("logs")
MEMORY_DIR = LOGS_DIR / "portfolio_memory"
PORTFOLIO_FILE = LOGS_DIR / "portfolio_scans.csv"
DECISIONS_FILE = LOGS_DIR / "decisions.csv"
DECISION_EVALS_FILE = LOGS_DIR / "decision_evaluations.csv"
PAPER_TRADES_FILE = LOGS_DIR / "paper_trades.csv"
PAPER_EVALS_FILE = LOGS_DIR / "paper_trade_evaluations.csv"

GOOD_RECS = {"ELITE", "ACTIONABLE", "WATCHLIST"}
MONITOR_RECS = {"MONITOR"}


@dataclass
class SymbolMemory:
    symbol: str
    scan_count: int = 0
    decision_count: int = 0
    complete_evaluations: int = 0
    paper_trades: int = 0
    closed_paper_trades: int = 0
    latest_side: str = "UNKNOWN"
    latest_recommendation: str = "UNKNOWN"
    latest_mtf: str = "UNKNOWN"
    avg_score: float = 0.0
    avg_confidence: float = 0.0
    avg_opportunity: float = 0.0
    max_opportunity: float = 0.0
    avg_rr: float = 0.0
    best_rr: float = 0.0
    directional_win_rate: float = 0.0
    target_1_hit_rate: float = 0.0
    avg_24h_return_pct: float = 0.0
    paper_win_rate: float = 0.0
    paper_expectancy_r: float = 0.0
    paper_profit_factor: float = 0.0
    actionable_rate: float = 0.0
    monitor_rate: float = 0.0
    ignore_rate: float = 0.0
    dominant_side: str = "UNKNOWN"
    dominant_recommendation: str = "UNKNOWN"
    memory_status: str = "NO_DATA"
    confidence: str = "LOW"
    notes: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)


@dataclass
class PortfolioMemoryResult:
    created_utc: str
    symbols: List[SymbolMemory]
    portfolio_status: str
    best_memory_symbol: str = "NONE"
    best_paper_symbol: str = "NONE"
    total_symbols: int = 0
    total_scans: int = 0
    total_complete_evaluations: int = 0
    total_closed_paper_trades: int = 0
    notes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _num(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(df[column], errors="coerce")


def _mean(df: pd.DataFrame, column: str) -> float:
    values = _num(df, column).dropna()
    return round(float(values.mean()), 4) if not values.empty else 0.0


def _max(df: pd.DataFrame, column: str) -> float:
    values = _num(df, column).dropna()
    return round(float(values.max()), 4) if not values.empty else 0.0


def _last_str(df: pd.DataFrame, column: str, default: str = "UNKNOWN") -> str:
    if df.empty or column not in df.columns:
        return default
    values = df[column].dropna().astype(str)
    if values.empty:
        return default
    value = values.iloc[-1].strip()
    return value or default


def _dominant(df: pd.DataFrame, column: str, default: str = "UNKNOWN") -> str:
    if df.empty or column not in df.columns:
        return default
    counts = df[column].dropna().astype(str).str.strip().replace("", pd.NA).dropna().value_counts()
    return str(counts.index[0]) if not counts.empty else default


def _pct(value: float, total: float) -> float:
    return round((value / total * 100.0), 2) if total else 0.0


def _profit_factor(values: pd.Series) -> float:
    v = pd.to_numeric(values, errors="coerce").dropna()
    if v.empty:
        return 0.0
    gross_pos = float(v[v > 0].sum())
    gross_neg = abs(float(v[v < 0].sum()))
    if gross_neg == 0:
        return round(gross_pos, 4) if gross_pos else 0.0
    return round(gross_pos / gross_neg, 4)


def _first_existing(df: pd.DataFrame, options: List[str]) -> Optional[str]:
    for column in options:
        if column in df.columns:
            return column
    return None


def _decision_return_column(evals: pd.DataFrame) -> Optional[str]:
    for column in ["return_after_24h_pct", "return_after_12h_pct", "return_after_4h_pct"]:
        if column in evals.columns and pd.to_numeric(evals[column], errors="coerce").notna().any():
            return column
    return None


def _evaluation_symbol_frame(decisions: pd.DataFrame, evals: pd.DataFrame, symbol: str) -> pd.DataFrame:
    if evals.empty:
        return pd.DataFrame()
    frame = evals.copy()
    if "symbol" not in frame.columns and not decisions.empty and "decision_id" in frame.columns and "decision_id" in decisions.columns:
        cols = ["decision_id", "symbol"]
        for extra in ["regime_label", "confidence_label", "score", "actionability"]:
            if extra in decisions.columns:
                cols.append(extra)
        frame = frame.merge(decisions[cols].drop_duplicates("decision_id"), on="decision_id", how="left")
    if "symbol" not in frame.columns:
        return pd.DataFrame()
    return frame[frame["symbol"].astype(str) == symbol].copy()


def _paper_symbol_frame(paper_trades: pd.DataFrame, paper_evals: pd.DataFrame, symbol: str) -> pd.DataFrame:
    if paper_evals.empty:
        return pd.DataFrame()
    frame = paper_evals.copy()
    if "symbol" not in frame.columns and not paper_trades.empty:
        left_key = _first_existing(frame, ["paper_trade_id", "trade_id", "id"])
        right_key = _first_existing(paper_trades, ["paper_trade_id", "trade_id", "id"])
        if left_key and right_key:
            frame = frame.merge(paper_trades[[right_key, "symbol"]].drop_duplicates(right_key), left_on=left_key, right_on=right_key, how="left")
    if "symbol" not in frame.columns:
        return pd.DataFrame()
    return frame[frame["symbol"].astype(str) == symbol].copy()


def _build_symbol_memory(symbol: str, portfolio: pd.DataFrame, decisions: pd.DataFrame, evals: pd.DataFrame, paper_trades: pd.DataFrame, paper_evals: pd.DataFrame) -> SymbolMemory:
    scans = portfolio[portfolio["symbol"].astype(str) == symbol].copy() if "symbol" in portfolio.columns else pd.DataFrame()
    decs = decisions[decisions["symbol"].astype(str) == symbol].copy() if "symbol" in decisions.columns else pd.DataFrame()
    sym_evals = _evaluation_symbol_frame(decisions, evals, symbol)
    sym_paper = paper_trades[paper_trades["symbol"].astype(str) == symbol].copy() if "symbol" in paper_trades.columns else pd.DataFrame()
    sym_paper_evals = _paper_symbol_frame(paper_trades, paper_evals, symbol)

    mem = SymbolMemory(symbol=symbol)
    mem.scan_count = int(len(scans))
    mem.decision_count = int(len(decs))
    mem.paper_trades = int(len(sym_paper))

    if not scans.empty:
        mem.latest_side = _last_str(scans, "side")
        mem.latest_recommendation = _last_str(scans, "recommendation")
        mem.latest_mtf = _last_str(scans, "mtf_direction")
        mem.avg_score = _mean(scans, "score")
        mem.avg_confidence = _mean(scans, "confidence")
        mem.avg_opportunity = _mean(scans, "opportunity_score")
        mem.max_opportunity = _max(scans, "opportunity_score")
        mem.avg_rr = _mean(scans, "first_rr")
        mem.best_rr = _max(scans, "best_rr") or _max(scans, "first_rr")
        mem.dominant_side = _dominant(scans, "side")
        mem.dominant_recommendation = _dominant(scans, "recommendation")
        recs = scans["recommendation"].fillna("").astype(str).str.upper() if "recommendation" in scans.columns else pd.Series(dtype="str")
        mem.actionable_rate = _pct(recs.isin(GOOD_RECS).sum(), len(recs)) if len(recs) else 0.0
        mem.monitor_rate = _pct(recs.isin(MONITOR_RECS).sum(), len(recs)) if len(recs) else 0.0
        mem.ignore_rate = _pct((recs == "IGNORE").sum(), len(recs)) if len(recs) else 0.0

    if not sym_evals.empty:
        if "evaluation_status" in sym_evals.columns:
            complete = sym_evals[sym_evals["evaluation_status"].astype(str).str.upper() == "COMPLETE"].copy()
        else:
            complete = sym_evals.copy()
        ret_col = _decision_return_column(complete)
        if ret_col:
            returns = pd.to_numeric(complete[ret_col], errors="coerce").dropna()
            mem.complete_evaluations = int(len(returns))
            mem.directional_win_rate = _pct((returns > 0).sum(), len(returns))
            mem.avg_24h_return_pct = round(float(returns.mean()), 4) if len(returns) else 0.0
        else:
            mem.complete_evaluations = int(len(complete))
        if "target_1_hit" in complete.columns and len(complete):
            t1 = complete["target_1_hit"].astype(str).str.lower().isin(["true", "1", "yes", "y"])
            mem.target_1_hit_rate = _pct(t1.sum(), len(t1))

    if not sym_paper_evals.empty:
        r_col = _first_existing(sym_paper_evals, ["r_multiple", "r", "result_r", "return_r"])
        result_col = _first_existing(sym_paper_evals, ["result", "status", "outcome"])
        if r_col:
            r = pd.to_numeric(sym_paper_evals[r_col], errors="coerce").dropna()
        else:
            r = pd.Series(dtype="float64")
        if len(r):
            mem.closed_paper_trades = int(len(r))
            mem.paper_win_rate = _pct((r > 0).sum(), len(r))
            mem.paper_expectancy_r = round(float(r.mean()), 4)
            mem.paper_profit_factor = _profit_factor(r)
        elif result_col:
            res = sym_paper_evals[result_col].astype(str).str.upper()
            closed = res[res.isin(["WIN", "LOSS", "FLAT", "CLOSED"])]
            mem.closed_paper_trades = int(len(closed))
            wins = res.isin(["WIN"]).sum()
            mem.paper_win_rate = _pct(wins, len(closed)) if len(closed) else 0.0

    # Status + confidence
    if mem.scan_count == 0 and mem.decision_count == 0 and mem.paper_trades == 0:
        mem.memory_status = "NO_DATA"
        mem.blockers.append("برای این نماد هنوز داده حافظه وجود ندارد.")
    elif mem.closed_paper_trades >= 30 and mem.paper_expectancy_r > 0 and mem.paper_win_rate >= 55:
        mem.memory_status = "SYMBOL_PAPER_EDGE"
        mem.notes.append("Paper edge نماد مثبت و دارای حداقل نمونه است.")
    elif mem.complete_evaluations >= 30 and mem.directional_win_rate >= 55 and mem.avg_24h_return_pct > 0:
        mem.memory_status = "SYMBOL_EDGE_EARLY"
        mem.notes.append("Decision edge اولیه برای این نماد مثبت است.")
    elif mem.actionable_rate > 0 or mem.monitor_rate > 0:
        mem.memory_status = "OBSERVATION_ACTIVE"
        mem.notes.append("نماد در حال رصد است اما هنوز Edge کافی ندارد.")
    else:
        mem.memory_status = "OBSERVATION_ONLY"
        mem.notes.append("حافظه نماد فعلاً فقط مشاهده‌ای است.")

    if mem.complete_evaluations < 30:
        mem.blockers.append(f"Complete evaluations کمتر از 30 است: {mem.complete_evaluations}")
    if mem.closed_paper_trades < 30:
        mem.blockers.append(f"Closed paper trades کمتر از 30 است: {mem.closed_paper_trades}")

    if mem.closed_paper_trades >= 30:
        mem.confidence = "HIGH" if mem.paper_expectancy_r > 0 and mem.paper_win_rate >= 55 else "MEDIUM"
    elif mem.complete_evaluations >= 30:
        mem.confidence = "MEDIUM"
    elif mem.scan_count >= 10 or mem.decision_count >= 10:
        mem.confidence = "LOW_MEDIUM"
    else:
        mem.confidence = "LOW"

    return mem


def build_portfolio_memory() -> PortfolioMemoryResult:
    portfolio = _load_csv(PORTFOLIO_FILE)
    decisions = _load_csv(DECISIONS_FILE)
    evals = _load_csv(DECISION_EVALS_FILE)
    paper_trades = _load_csv(PAPER_TRADES_FILE)
    paper_evals = _load_csv(PAPER_EVALS_FILE)

    symbols = set()
    for frame in [portfolio, decisions, evals, paper_trades, paper_evals]:
        if not frame.empty and "symbol" in frame.columns:
            symbols.update(frame["symbol"].dropna().astype(str).tolist())

    memories = [_build_symbol_memory(symbol, portfolio, decisions, evals, paper_trades, paper_evals) for symbol in sorted(symbols)]

    total_scans = sum(m.scan_count for m in memories)
    total_complete = sum(m.complete_evaluations for m in memories)
    total_closed = sum(m.closed_paper_trades for m in memories)

    best_memory = "NONE"
    if memories:
        best = sorted(memories, key=lambda m: (m.paper_expectancy_r, m.avg_24h_return_pct, m.avg_opportunity, m.scan_count), reverse=True)[0]
        best_memory = best.symbol

    paper_candidates = [m for m in memories if m.closed_paper_trades > 0]
    best_paper = "NONE"
    if paper_candidates:
        best_paper = sorted(paper_candidates, key=lambda m: (m.paper_expectancy_r, m.paper_win_rate), reverse=True)[0].symbol

    warnings: List[str] = []
    notes: List[str] = []
    if not memories:
        status = "NO_MEMORY_DATA"
        warnings.append("هیچ داده‌ای برای Portfolio Memory پیدا نشد.")
    elif total_closed < 30:
        status = "MEMORY_BUILDING"
        warnings.append(f"Closed paper trades کل پورتفو کمتر از 30 است: {total_closed}")
    elif any(m.memory_status == "SYMBOL_PAPER_EDGE" for m in memories):
        status = "SYMBOL_EDGE_OBSERVED"
        notes.append("حداقل یک نماد Paper Edge اولیه نشان می‌دهد.")
    else:
        status = "OBSERVATION_MEMORY"
        notes.append("حافظه پورتفو فعال است اما هنوز Edge قطعی دیده نشده است.")

    return PortfolioMemoryResult(
        created_utc=datetime.now(timezone.utc).isoformat(),
        symbols=memories,
        portfolio_status=status,
        best_memory_symbol=best_memory,
        best_paper_symbol=best_paper,
        total_symbols=len(memories),
        total_scans=total_scans,
        total_complete_evaluations=total_complete,
        total_closed_paper_trades=total_closed,
        notes=notes,
        warnings=warnings,
    )


def format_portfolio_memory_console(result: PortfolioMemoryResult) -> str:
    lines: List[str] = []
    lines.append("=" * 110)
    lines.append("🧠 Freakto Portfolio Memory Engine v5.0")
    lines.append("=" * 110)
    lines.append(f"Created UTC       : {result.created_utc}")
    lines.append(f"Portfolio Status  : {result.portfolio_status}")
    lines.append(f"Symbols           : {result.total_symbols}")
    lines.append(f"Total scans       : {result.total_scans}")
    lines.append(f"Complete evals    : {result.total_complete_evaluations}")
    lines.append(f"Closed paper      : {result.total_closed_paper_trades}")
    lines.append(f"Best memory symbol: {result.best_memory_symbol}")
    lines.append(f"Best paper symbol : {result.best_paper_symbol}")
    if result.warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in result.warnings:
            lines.append(f"⚠️ {warning}")
    for m in result.symbols:
        lines.append("-" * 110)
        lines.append(f"Symbol        : {m.symbol}")
        lines.append(f"Status        : {m.memory_status} | Confidence {m.confidence}")
        lines.append(f"Scans/Dec/Eval: {m.scan_count} / {m.decision_count} / {m.complete_evaluations}")
        lines.append(f"Latest        : {m.latest_side} | Rec {m.latest_recommendation} | MTF {m.latest_mtf}")
        lines.append(f"Avg Score/Conf/Opp: {m.avg_score:.2f} / {m.avg_confidence:.2f}% / {m.avg_opportunity:.2f}")
        lines.append(f"Directional/T1/Avg24: {m.directional_win_rate:.2f}% / {m.target_1_hit_rate:.2f}% / {m.avg_24h_return_pct:.4f}%")
        lines.append(f"Paper        : closed {m.closed_paper_trades} | win {m.paper_win_rate:.2f}% | exp {m.paper_expectancy_r:.4f}R | PF {m.paper_profit_factor:.4f}")
        lines.append(f"Rec rates    : actionable {m.actionable_rate:.2f}% | monitor {m.monitor_rate:.2f}% | ignore {m.ignore_rate:.2f}%")
        for note in m.notes[:2]:
            lines.append(f"Note         : {note}")
        for blocker in m.blockers[:3]:
            lines.append(f"Blocker      : {blocker}")
    lines.append("=" * 110)
    return "\n".join(lines)


def format_portfolio_memory_report(result: PortfolioMemoryResult) -> str:
    lines = ["# Freakto Portfolio Memory Engine v5.0", "", f"Created UTC: {result.created_utc}", ""]
    lines.append(f"- Portfolio Status: **{result.portfolio_status}**")
    lines.append(f"- Total Symbols: {result.total_symbols}")
    lines.append(f"- Total Scans: {result.total_scans}")
    lines.append(f"- Complete Evaluations: {result.total_complete_evaluations}")
    lines.append(f"- Closed Paper Trades: {result.total_closed_paper_trades}")
    lines.append(f"- Best Memory Symbol: {result.best_memory_symbol}")
    lines.append(f"- Best Paper Symbol: {result.best_paper_symbol}")
    if result.warnings:
        lines.append("\n## Warnings")
        for warning in result.warnings:
            lines.append(f"- {warning}")
    lines.append("\n## Symbol Memory")
    for m in result.symbols:
        lines.append(f"### {m.symbol}")
        lines.append(f"- Status: {m.memory_status} ({m.confidence})")
        lines.append(f"- Scans / Decisions / Complete Evals: {m.scan_count} / {m.decision_count} / {m.complete_evaluations}")
        lines.append(f"- Latest: {m.latest_side} | {m.latest_recommendation} | MTF {m.latest_mtf}")
        lines.append(f"- Avg Score / Confidence / Opportunity: {m.avg_score:.2f} / {m.avg_confidence:.2f}% / {m.avg_opportunity:.2f}")
        lines.append(f"- Directional Win / T1 Hit / Avg24: {m.directional_win_rate:.2f}% / {m.target_1_hit_rate:.2f}% / {m.avg_24h_return_pct:.4f}%")
        lines.append(f"- Paper: closed {m.closed_paper_trades}, win {m.paper_win_rate:.2f}%, expectancy {m.paper_expectancy_r:.4f}R, PF {m.paper_profit_factor:.4f}")
        for note in m.notes:
            lines.append(f"- Note: {note}")
        for blocker in m.blockers:
            lines.append(f"- Blocker: {blocker}")
        lines.append("")
    return "\n".join(lines)


def save_portfolio_memory(result: PortfolioMemoryResult) -> tuple[Path, Path]:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = MEMORY_DIR / f"portfolio_memory_{stamp}.json"
    report_path = MEMORY_DIR / f"portfolio_memory_report_{stamp}.md"
    json_path.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(format_portfolio_memory_report(result), encoding="utf-8")
    return json_path, report_path
