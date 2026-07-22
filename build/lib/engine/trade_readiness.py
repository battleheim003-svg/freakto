"""
engine.trade_readiness

Freakto v4.7.1 Trade Readiness Gate

This module decides whether the system is ready for:
- paper trading a specific candidate
- micro live testing globally
It is intentionally conservative and never places orders.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import pandas as pd

LOGS_DIR = Path("logs")
READINESS_DIR = LOGS_DIR / "readiness"


@dataclass
class ReadinessDecision:
    paper_ready: bool
    live_ready: bool
    level: str
    score: int
    reasons: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    allowed_risk_pct: float = 0.0


@dataclass
class GlobalReadinessStats:
    complete_evaluations: int = 0
    # Legacy field name; equals Target 1 Hit Rate for decision evaluations.
    decision_win_rate: float = 0.0
    decision_directional_win_rate: float = 0.0
    avg_24h_return_pct: float = 0.0
    stop_hit_rate: float = 0.0
    paper_trades: int = 0
    closed_paper_trades: int = 0
    paper_win_rate: float = 0.0
    paper_expectancy_r: float = 0.0
    strategy_test_passed: bool = False
    walk_forward_passed: bool = False


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def load_global_readiness_stats() -> GlobalReadinessStats:
    evals = _load_csv(LOGS_DIR / "decision_evaluations.csv")
    paper = _load_csv(LOGS_DIR / "paper_trades.csv")
    paper_evals = _load_csv(LOGS_DIR / "paper_trade_evaluations.csv")

    stats = GlobalReadinessStats()

    if not evals.empty and "evaluation_status" in evals.columns:
        complete = evals[evals["evaluation_status"].astype(str) == "COMPLETE"].copy()
        stats.complete_evaluations = len(complete)
        if not complete.empty:
            r24 = pd.to_numeric(complete.get("return_after_24h_pct"), errors="coerce")
            stats.avg_24h_return_pct = round(float(r24.dropna().mean()), 4) if not r24.dropna().empty else 0.0
            t1 = complete.get("target_1_hit", pd.Series(dtype=object)).astype(str).str.lower().isin(["true", "1"])
            stop = complete.get("stop_hit", pd.Series(dtype=object)).astype(str).str.lower().isin(["true", "1"])
            stats.decision_win_rate = round(float(t1.mean() * 100), 2) if len(t1) else 0.0
            clean_r24 = r24.dropna()
            stats.decision_directional_win_rate = round(float((clean_r24 > 0).mean() * 100), 2) if len(clean_r24) else 0.0
            stats.stop_hit_rate = round(float(stop.mean() * 100), 2) if len(stop) else 0.0

    if not paper.empty:
        stats.paper_trades = len(paper)

    if not paper_evals.empty and "status" in paper_evals.columns:
        closed = paper_evals[paper_evals["status"].astype(str) == "CLOSED"].copy()
        stats.closed_paper_trades = len(closed)
        if not closed.empty:
            wins = closed[closed["result"].astype(str) == "WIN"]
            stats.paper_win_rate = round(len(wins) / len(closed) * 100, 2)
            r = pd.to_numeric(closed.get("r_multiple"), errors="coerce").dropna()
            stats.paper_expectancy_r = round(float(r.mean()), 4) if not r.empty else 0.0

    # Strategy/walk-forward should count as useful only when they contain samples,
    # not merely because an empty report file exists.
    lab_files = sorted((LOGS_DIR / "strategy_lab").glob("strategy_lab_results_*.csv")) if (LOGS_DIR / "strategy_lab").exists() else []
    wf_files = sorted((LOGS_DIR / "walk_forward").glob("walk_forward_results_*.csv")) if (LOGS_DIR / "walk_forward").exists() else []

    if lab_files:
        lab = _load_csv(lab_files[-1])
        if not lab.empty and "sample_count" in lab.columns:
            samples = pd.to_numeric(lab["sample_count"], errors="coerce").fillna(0)
            stats.strategy_test_passed = bool((samples > 0).any())

    if wf_files:
        wf = _load_csv(wf_files[-1])
        if not wf.empty and "test_samples" in wf.columns:
            samples = pd.to_numeric(wf["test_samples"], errors="coerce").fillna(0)
            stats.walk_forward_passed = bool((samples > 0).any())

    return stats


def assess_candidate_readiness(item=None, market_breadth=None, stats: Optional[GlobalReadinessStats] = None) -> ReadinessDecision:
    stats = stats or load_global_readiness_stats()
    reasons = []
    blockers = []
    warnings = []
    score = 0

    if item is not None:
        rec = str(getattr(item, "recommendation", ""))
        side = str(getattr(item, "side", ""))
        rr = float(getattr(item, "first_rr", 0.0) or 0.0)
        conf = int(getattr(item, "confidence", 0) or 0)
        trade_grade = str(getattr(item, "trade_quality_grade", "") or "")
        mtf_direction = str(getattr(item, "mtf_direction", "") or "")
        mtf_consensus = int(getattr(item, "mtf_consensus", 0) or 0)

        if rec in {"ELITE", "ACTIONABLE", "WATCHLIST"}:
            score += 18
            reasons.append(f"Recommendation قابل بررسی است: {rec}")
        else:
            blockers.append(f"Recommendation برای معامله کافی نیست: {rec}")

        if side in {"LONG", "SHORT"}:
            score += 12
            reasons.append(f"Bias جهت‌دار است: {side}")
        else:
            blockers.append("Bias جهت‌دار نیست.")

        if trade_grade != "Avoid":
            score += 14
            reasons.append(f"Trade Quality برابر Avoid نیست: {trade_grade}")
        else:
            blockers.append("Trade Quality = Avoid")

        if rr >= 1.5:
            score += 16
            reasons.append(f"R:R برای تست عملی کوچک مناسب است: {rr:.2f}")
        elif rr >= 1.2:
            score += 10
            warnings.append(f"R:R برای Paper قابل قبول است اما برای Live ضعیف است: {rr:.2f}")
        else:
            blockers.append(f"R:R کافی نیست: {rr:.2f}")

        if conf >= 65:
            score += 14
            reasons.append(f"Confidence مناسب است: {conf}%")
        elif conf >= 50:
            score += 8
            warnings.append(f"Confidence متوسط است: {conf}%")
        else:
            blockers.append(f"Confidence پایین است: {conf}%")

        if mtf_direction == side and mtf_consensus >= 65:
            score += 12
            reasons.append(f"MTF هم‌راستا است: {mtf_direction}/{mtf_consensus}%")
        elif mtf_direction == side and mtf_consensus >= 50:
            score += 6
            warnings.append(f"MTF نیمه‌هم‌راستا است: {mtf_direction}/{mtf_consensus}%")
        else:
            warnings.append(f"MTF تأیید قوی ندارد: {mtf_direction}/{mtf_consensus}%")

    if market_breadth is not None:
        mode = str(getattr(market_breadth, "market_mode", "UNKNOWN"))
        tone = str(getattr(market_breadth, "risk_tone", "UNKNOWN"))
        if mode == "RISK_OFF":
            blockers.append("Market Breadth در حالت RISK_OFF است.")
        elif mode in {"RISK_ON", "NEUTRAL"}:
            score += 6
            reasons.append(f"Market Mode مانع جدی نیست: {mode}/{tone}")
        else:
            warnings.append(f"Market Mode ترکیبی/احتیاطی است: {mode}/{tone}")

    # Global readiness gates for live testing.
    if stats.complete_evaluations >= 100:
        score += 8
        reasons.append(f"Complete evaluations کافی است: {stats.complete_evaluations}")
    else:
        blockers.append(f"Complete evaluations کمتر از 100 است: {stats.complete_evaluations}")

    if stats.closed_paper_trades >= 30:
        score += 8
        reasons.append(f"Closed paper trades کافی است: {stats.closed_paper_trades}")
    else:
        blockers.append(f"Closed paper trades کمتر از 30 است: {stats.closed_paper_trades}")

    if stats.paper_expectancy_r > 0:
        score += 8
        reasons.append(f"Paper expectancy مثبت است: {stats.paper_expectancy_r:.3f}R")
    else:
        blockers.append(f"Paper expectancy هنوز مثبت/کافی نیست: {stats.paper_expectancy_r:.3f}R")

    paper_ready = (
        item is not None
        and not any("Bias" in b or "Trade Quality" in b or "R:R" in b or "Confidence" in b or "Recommendation" in b for b in blockers)
    )

    live_ready = (
        paper_ready
        and stats.complete_evaluations >= 100
        and stats.closed_paper_trades >= 30
        and stats.paper_expectancy_r > 0
        and stats.paper_win_rate >= 55
        and score >= 78
    )

    if live_ready:
        level = "MICRO_LIVE_READY"
        allowed_risk = 0.25
    elif paper_ready:
        level = "PAPER_READY_ONLY"
        allowed_risk = 0.0
    else:
        level = "NOT_READY"
        allowed_risk = 0.0

    return ReadinessDecision(
        paper_ready=paper_ready,
        live_ready=live_ready,
        level=level,
        score=max(0, min(100, int(score))),
        reasons=reasons,
        blockers=blockers,
        warnings=warnings,
        allowed_risk_pct=allowed_risk,
    )


def assess_global_live_readiness(stats: Optional[GlobalReadinessStats] = None) -> ReadinessDecision:
    stats = stats or load_global_readiness_stats()
    reasons = []
    blockers = []
    warnings = []
    score = 0

    if stats.complete_evaluations >= 100:
        score += 25
        reasons.append(f"Complete evaluations کافی است: {stats.complete_evaluations}")
    else:
        blockers.append(f"Complete evaluations کمتر از 100 است: {stats.complete_evaluations}")

    if stats.decision_win_rate >= 55 and stats.avg_24h_return_pct > 0:
        score += 15
        reasons.append(f"Decision edge مثبت است: Target1 {stats.decision_win_rate:.1f}% | DirWin {stats.decision_directional_win_rate:.1f}% | Avg24 {stats.avg_24h_return_pct:.2f}%")
    else:
        warnings.append(f"Decision edge هنوز قطعی نیست: Target1 {stats.decision_win_rate:.1f}% | DirWin {stats.decision_directional_win_rate:.1f}% | Avg24 {stats.avg_24h_return_pct:.2f}%")

    if stats.paper_trades >= 30 and stats.closed_paper_trades >= 20:
        score += 20
        reasons.append(f"Paper trade sample قابل قبول است: {stats.closed_paper_trades}/{stats.paper_trades}")
    else:
        blockers.append(f"Paper trades کافی نیست: closed {stats.closed_paper_trades} / total {stats.paper_trades}")

    if stats.paper_expectancy_r > 0 and stats.paper_win_rate >= 55:
        score += 20
        reasons.append(f"Paper expectancy مثبت است: {stats.paper_expectancy_r:.3f}R | PaperWin {stats.paper_win_rate:.1f}%")
    else:
        blockers.append(f"Paper expectancy/PaperWin کافی نیست: {stats.paper_expectancy_r:.3f}R | PaperWin {stats.paper_win_rate:.1f}%")

    if stats.stop_hit_rate <= 35:
        score += 8
        reasons.append(f"Stop Hit Rate کنترل‌شده است: {stats.stop_hit_rate:.1f}%")
    else:
        blockers.append(f"Stop Hit Rate بالاست: {stats.stop_hit_rate:.1f}%")

    if stats.strategy_test_passed:
        score += 6
        reasons.append("Strategy Lab اجرا شده است.")
    else:
        warnings.append("Strategy Lab هنوز اجرا نشده است.")

    if stats.walk_forward_passed:
        score += 6
        reasons.append("Walk-Forward Validation اجرا شده است.")
    else:
        warnings.append("Walk-Forward Validation هنوز اجرا نشده است.")

    live_ready = score >= 85 and not blockers
    paper_ready = stats.complete_evaluations >= 30

    if live_ready:
        level = "MICRO_LIVE_READY"
        allowed_risk = 0.25
    elif paper_ready:
        level = "PAPER_TRADING_PHASE"
        allowed_risk = 0.0
    else:
        level = "RESEARCH_ONLY"
        allowed_risk = 0.0

    return ReadinessDecision(
        paper_ready=paper_ready,
        live_ready=live_ready,
        level=level,
        score=max(0, min(100, int(score))),
        reasons=reasons,
        blockers=blockers,
        warnings=warnings,
        allowed_risk_pct=allowed_risk,
    )


def format_readiness_report(decision: ReadinessDecision, stats: Optional[GlobalReadinessStats] = None) -> str:
    stats = stats or load_global_readiness_stats()
    lines = []
    lines.append("=" * 110)
    lines.append("🚦 Freakto Trade Readiness Gate v4.7.1")
    lines.append("=" * 110)
    lines.append(f"Created UTC       : {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"Readiness Level   : {decision.level}")
    lines.append(f"Readiness Score   : {decision.score}/100")
    lines.append(f"Paper Ready       : {decision.paper_ready}")
    lines.append(f"Live Ready        : {decision.live_ready}")
    lines.append(f"Allowed Risk      : {decision.allowed_risk_pct:.2f}%")
    lines.append("")
    lines.append("Data Stats:")
    lines.append(f"- Complete evaluations: {stats.complete_evaluations}")
    lines.append(f"- Decision Target 1 Hit Rate: {stats.decision_win_rate:.2f}%")
    lines.append(f"- Decision Directional Win Rate: {stats.decision_directional_win_rate:.2f}%")
    lines.append(f"- Avg 24h Return: {stats.avg_24h_return_pct:.4f}%")
    lines.append(f"- Stop Hit Rate: {stats.stop_hit_rate:.2f}%")
    lines.append(f"- Paper trades: {stats.paper_trades}")
    lines.append(f"- Closed paper trades: {stats.closed_paper_trades}")
    lines.append(f"- Paper Trade Win Rate: {stats.paper_win_rate:.2f}%")
    lines.append(f"- Paper Expectancy: {stats.paper_expectancy_r:.4f}R")
    if decision.reasons:
        lines.append("")
        lines.append("Reasons:")
        for reason in decision.reasons:
            lines.append(f"✓ {reason}")
    if decision.warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in decision.warnings:
            lines.append(f"⚠️ {warning}")
    if decision.blockers:
        lines.append("")
        lines.append("Blockers:")
        for blocker in decision.blockers:
            lines.append(f"⛔ {blocker}")
    lines.append("")
    if decision.live_ready:
        lines.append("Conclusion: فقط Micro Live Test با ریسک بسیار کوچک مجاز است؛ اجرای خودکار سفارش هنوز پیشنهاد نمی‌شود.")
    elif decision.paper_ready:
        lines.append("Conclusion: پروژه در فاز Paper Trading / Forward Test است و هنوز برای پول واقعی آماده نیست.")
    else:
        lines.append("Conclusion: پروژه هنوز Research/Observation است و باید داده بیشتری جمع کند.")
    lines.append("=" * 110)
    return "\n".join(lines)


def save_readiness_report(text: str) -> Path:
    READINESS_DIR.mkdir(parents=True, exist_ok=True)
    path = READINESS_DIR / f"trade_readiness_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
    path.write_text(text, encoding="utf-8")
    return path
