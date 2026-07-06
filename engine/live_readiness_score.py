"""
engine.live_readiness_score

Freakto v4.7.1 Advanced Live Readiness Score

Combines edge validation, regime matrix, paper trading, strategy lab, and
walk-forward checks into a conservative live-test readiness score.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from .edge_validation import EdgeValidationResult, run_edge_validation
from .regime_matrix import RegimeMatrixResult, run_regime_matrix
from .trade_readiness import GlobalReadinessStats, load_global_readiness_stats

LOGS_DIR = Path("logs")
READINESS_DIR = LOGS_DIR / "readiness"


@dataclass
class ScoreComponent:
    name: str
    score: int
    max_score: int
    status: str
    notes: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)


@dataclass
class AdvancedReadinessResult:
    created_utc: str
    level: str
    score: int
    live_ready: bool
    paper_ready: bool
    allowed_risk_pct: float
    components: List[ScoreComponent]
    blockers: List[str]
    warnings: List[str]
    conclusion: str
    edge_quality: str
    regime_verdict: str
    complete_evaluations: int
    closed_paper_trades: int
    paper_expectancy_r: float
    decision_profit_factor: float


def _clamp(value: float, max_value: int) -> int:
    return max(0, min(max_value, int(round(value))))


def _data_sufficiency(stats: GlobalReadinessStats) -> ScoreComponent:
    score = 0
    notes: List[str] = []
    blockers: List[str] = []

    decision_score = _clamp((stats.complete_evaluations / 100) * 12, 12)
    paper_score = _clamp((stats.closed_paper_trades / 30) * 8, 8)
    score = decision_score + paper_score

    notes.append(f"Complete evaluations: {stats.complete_evaluations}/100")
    notes.append(f"Closed paper trades: {stats.closed_paper_trades}/30")

    if stats.complete_evaluations < 100:
        blockers.append(f"Complete evaluations هنوز کافی نیست: {stats.complete_evaluations}/100")
    if stats.closed_paper_trades < 30:
        blockers.append(f"Closed paper trades هنوز کافی نیست: {stats.closed_paper_trades}/30")

    status = "PASS" if not blockers else ("PARTIAL" if score >= 8 else "LOW")
    return ScoreComponent("Data Sufficiency", score, 20, status, notes, blockers)


def _decision_edge(edge: EdgeValidationResult) -> ScoreComponent:
    m = edge.decision_edge
    score = 0
    notes: List[str] = []
    blockers: List[str] = []

    if m.sample_count > 0:
        score += _clamp((m.win_rate / 65) * 7, 7)
        if m.expectancy > 0:
            score += 6
        if m.profit_factor >= 1.2:
            score += 5
        elif m.profit_factor >= 1.0:
            score += 3
        if m.stop_hit_rate <= 35:
            score += 3
        if m.sharpe_like > 0:
            score += 2
    notes.append(f"Decision quality: {m.quality}")
    notes.append(f"Directional Win {m.win_rate:.2f}% | Expectancy {m.expectancy:.4f}{m.unit} | PF {m.profit_factor:.4f}")
    notes.append(f"Stop {m.stop_hit_rate:.2f}% | Sharpe-like {m.sharpe_like:.4f}")

    if m.sample_count < 100:
        blockers.append(f"Decision sample کمتر از 100 است: {m.sample_count}")
    if m.expectancy <= 0:
        blockers.append("Decision expectancy مثبت نیست.")
    if m.profit_factor < 1.0 and m.sample_count >= 10:
        blockers.append(f"Decision Profit Factor زیر 1 است: {m.profit_factor:.4f}")

    status = "PASS" if not blockers and score >= 17 else ("PARTIAL" if score >= 10 else "LOW")
    return ScoreComponent("Decision Edge", min(score, 23), 23, status, notes, blockers)


def _paper_edge(edge: EdgeValidationResult) -> ScoreComponent:
    m = edge.paper_edge
    score = 0
    notes: List[str] = []
    blockers: List[str] = []

    if m.sample_count > 0:
        score += _clamp((m.win_rate / 65) * 6, 6)
        if m.expectancy > 0:
            score += 7
        if m.profit_factor >= 1.2:
            score += 4
        elif m.profit_factor >= 1.0:
            score += 2
        if m.max_drawdown >= -5:
            score += 3
    notes.append(f"Paper quality: {m.quality}")
    notes.append(f"Closed {m.sample_count} | Paper Win {m.win_rate:.2f}% | Expectancy {m.expectancy:.4f}R | PF {m.profit_factor:.4f}")
    notes.append(f"Max drawdown {m.max_drawdown:.4f}R")

    if m.sample_count < 30:
        blockers.append(f"Paper sample کمتر از 30 معامله بسته‌شده است: {m.sample_count}")
    if m.expectancy <= 0:
        blockers.append("Paper expectancy هنوز مثبت نیست.")
    if m.win_rate < 55 and m.sample_count >= 10:
        blockers.append(f"Paper Trade Win Rate کمتر از 55% است: {m.win_rate:.2f}%")

    status = "PASS" if not blockers and score >= 15 else ("PARTIAL" if score >= 8 else "LOW")
    return ScoreComponent("Paper Edge", min(score, 20), 20, status, notes, blockers)


def _regime_stability(regime: RegimeMatrixResult) -> ScoreComponent:
    score = 0
    notes: List[str] = []
    blockers: List[str] = []
    positive_rows = [r for r in regime.rows if r.verdict == "REGIME_POSITIVE"]

    if regime.known_regime_samples >= 30:
        score += 8
    elif regime.known_regime_samples > 0:
        score += _clamp((regime.known_regime_samples / 30) * 8, 8)

    if positive_rows:
        score += 5
    if regime.best_regime != "UNKNOWN":
        score += 3
    if regime.overall_verdict in {"REGIME_EDGE_EMERGING", "REGIME_DATA_COLLECTING"}:
        score += 2

    notes.append(f"Regime verdict: {regime.overall_verdict}")
    notes.append(f"Known/Unknown: {regime.known_regime_samples}/{regime.unknown_regime_samples}")
    notes.append(f"Best/Worst: {regime.best_regime}/{regime.worst_regime}")

    if regime.known_regime_samples < 30:
        blockers.append(f"Regime-labeled samples کمتر از 30 است: {regime.known_regime_samples}")
    if not positive_rows:
        blockers.append("هنوز هیچ رژیم با Edge مثبت قابل اتکا مشخص نشده است.")

    status = "PASS" if not blockers and score >= 14 else ("PARTIAL" if score >= 6 else "LOW")
    return ScoreComponent("Regime Stability", min(score, 18), 18, status, notes, blockers)


def _validation_stability(stats: GlobalReadinessStats) -> ScoreComponent:
    score = 0
    notes: List[str] = []
    blockers: List[str] = []

    if stats.strategy_test_passed:
        score += 5
        notes.append("Strategy Lab اجرا شده و نمونه دارد.")
    else:
        blockers.append("Strategy Lab معتبر هنوز اجرا نشده یا نمونه ندارد.")

    if stats.walk_forward_passed:
        score += 7
        notes.append("Walk-Forward Validation اجرا شده و test sample دارد.")
    else:
        blockers.append("Walk-Forward معتبر هنوز اجرا نشده یا نمونه ندارد.")

    status = "PASS" if not blockers else ("PARTIAL" if score > 0 else "LOW")
    return ScoreComponent("Validation Stability", score, 12, status, notes, blockers)


def _operational_safety(stats: GlobalReadinessStats) -> ScoreComponent:
    score = 5
    notes = ["Auto-live trading در پروژه فعال نیست.", "Readiness Gate قبل از هر تست عملی باید بررسی شود."]
    blockers: List[str] = []
    if stats.stop_hit_rate <= 35:
        score += 2
        notes.append(f"Stop Hit Rate کنترل‌شده است: {stats.stop_hit_rate:.2f}%")
    else:
        blockers.append(f"Stop Hit Rate بالاست: {stats.stop_hit_rate:.2f}%")
    return ScoreComponent("Operational Safety", min(score, 7), 7, "PASS" if not blockers else "PARTIAL", notes, blockers)


def assess_advanced_live_readiness() -> AdvancedReadinessResult:
    stats = load_global_readiness_stats()
    edge = run_edge_validation()
    regime = run_regime_matrix()

    components = [
        _data_sufficiency(stats),
        _decision_edge(edge),
        _paper_edge(edge),
        _regime_stability(regime),
        _validation_stability(stats),
        _operational_safety(stats),
    ]
    total = sum(c.score for c in components)
    blockers = [b for c in components for b in c.blockers]
    warnings: List[str] = []

    if edge.decision_edge.sample_count < 30:
        warnings.append("Decision edge هنوز بسیار کم‌نمونه است.")
    if edge.paper_edge.sample_count == 0:
        warnings.append("Paper Trading هنوز نتیجه بسته‌شده ندارد.")
    if regime.unknown_regime_samples > regime.known_regime_samples:
        warnings.append("Regime Matrix برای لاگ‌های قدیمی هنوز UNKNOWN زیادی دارد؛ چند روز داده جدید لازم است.")

    hard_live_gates = (
        stats.complete_evaluations >= 100
        and edge.paper_edge.sample_count >= 30
        and edge.paper_edge.expectancy > 0
        and edge.paper_edge.win_rate >= 55
        and edge.decision_edge.profit_factor >= 1.0
        and regime.known_regime_samples >= 30
        and total >= 80
        and not blockers
    )

    if hard_live_gates:
        level = "MICRO_LIVE_READY"
        live_ready = True
        paper_ready = True
        allowed = 0.25
        conclusion = "Micro Live Test با ریسک بسیار کوچک مجاز است؛ اجرای خودکار سفارش همچنان مجاز نیست."
    elif total >= 55 and stats.complete_evaluations >= 30:
        level = "PAPER_TRADING_PHASE"
        live_ready = False
        paper_ready = True
        allowed = 0.0
        conclusion = "پروژه در فاز Paper/Forward Test است؛ پول واقعی هنوز مجاز نیست."
    else:
        level = "RESEARCH_ONLY"
        live_ready = False
        paper_ready = False
        allowed = 0.0
        conclusion = "پروژه هنوز در Research/Observation است؛ داده و Paper Trade بیشتری لازم است."

    return AdvancedReadinessResult(
        created_utc=datetime.now(timezone.utc).isoformat(),
        level=level,
        score=max(0, min(100, int(total))),
        live_ready=live_ready,
        paper_ready=paper_ready,
        allowed_risk_pct=allowed,
        components=components,
        blockers=blockers,
        warnings=warnings,
        conclusion=conclusion,
        edge_quality=edge.combined_quality,
        regime_verdict=regime.overall_verdict,
        complete_evaluations=stats.complete_evaluations,
        closed_paper_trades=stats.closed_paper_trades,
        paper_expectancy_r=stats.paper_expectancy_r,
        decision_profit_factor=edge.decision_edge.profit_factor,
    )


def save_advanced_readiness(result: AdvancedReadinessResult) -> tuple[Path, Path]:
    READINESS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = READINESS_DIR / f"advanced_live_readiness_{stamp}.json"
    report_path = READINESS_DIR / f"advanced_live_readiness_report_{stamp}.md"
    json_path.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(format_advanced_readiness_report(result), encoding="utf-8")
    return json_path, report_path


def format_advanced_readiness_console(result: AdvancedReadinessResult) -> str:
    lines: List[str] = []
    lines.append("=" * 110)
    lines.append("🚦 Freakto Advanced Live Readiness Score v4.7.1")
    lines.append("=" * 110)
    lines.append(f"Created UTC       : {result.created_utc}")
    lines.append(f"Readiness Level   : {result.level}")
    lines.append(f"Readiness Score   : {result.score}/100")
    lines.append(f"Paper Ready       : {result.paper_ready}")
    lines.append(f"Live Ready        : {result.live_ready}")
    lines.append(f"Allowed Risk      : {result.allowed_risk_pct:.2f}%")
    lines.append(f"Edge Quality      : {result.edge_quality}")
    lines.append(f"Regime Verdict    : {result.regime_verdict}")
    lines.append("")
    lines.append("Core Stats:")
    lines.append(f"- Complete evaluations: {result.complete_evaluations}")
    lines.append(f"- Closed paper trades: {result.closed_paper_trades}")
    lines.append(f"- Paper expectancy: {result.paper_expectancy_r:.4f}R")
    lines.append(f"- Decision Profit Factor: {result.decision_profit_factor:.4f}")
    for component in result.components:
        lines.append("-" * 110)
        lines.append(f"Component : {component.name}")
        lines.append(f"Score     : {component.score}/{component.max_score}")
        lines.append(f"Status    : {component.status}")
        for note in component.notes[:4]:
            lines.append(f"Note      : {note}")
        for blocker in component.blockers[:4]:
            lines.append(f"Blocker   : {blocker}")
    if result.warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in result.warnings:
            lines.append(f"⚠️ {warning}")
    if result.blockers:
        lines.append("")
        lines.append("Hard Blockers:")
        for blocker in result.blockers[:10]:
            lines.append(f"⛔ {blocker}")
    lines.append("")
    lines.append(f"Conclusion: {result.conclusion}")
    lines.append("=" * 110)
    return "\n".join(lines)


def format_advanced_readiness_report(result: AdvancedReadinessResult) -> str:
    lines = ["# Freakto Advanced Live Readiness Score v4.7.1", "", f"Created UTC: {result.created_utc}", ""]
    lines.append(f"- Readiness Level: **{result.level}**")
    lines.append(f"- Readiness Score: **{result.score}/100**")
    lines.append(f"- Paper Ready: {result.paper_ready}")
    lines.append(f"- Live Ready: {result.live_ready}")
    lines.append(f"- Allowed Risk: {result.allowed_risk_pct:.2f}%")
    lines.append(f"- Conclusion: {result.conclusion}")
    lines.append("")
    lines.append("## Components")
    for c in result.components:
        lines.append(f"### {c.name}")
        lines.append(f"- Score: {c.score}/{c.max_score}")
        lines.append(f"- Status: {c.status}")
        for note in c.notes:
            lines.append(f"- Note: {note}")
        for blocker in c.blockers:
            lines.append(f"- Blocker: {blocker}")
        lines.append("")
    if result.warnings:
        lines.append("## Warnings")
        for warning in result.warnings:
            lines.append(f"- {warning}")
    if result.blockers:
        lines.append("## Hard Blockers")
        for blocker in result.blockers:
            lines.append(f"- {blocker}")
    return "\n".join(lines)
