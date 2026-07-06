"""
engine.strategy_lab

Freakto v4.7.1 Strategy Lab

Lightweight strategy comparison on logged decision evaluations.
This is not a full backtesting engine; it compares decision filters on already
logged/evaluated decisions to reduce overfitting risk before live testing.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List

import pandas as pd

LOGS_DIR = Path("logs")
STRATEGY_DIR = LOGS_DIR / "strategy_lab"
EVALUATIONS_FILE = LOGS_DIR / "decision_evaluations.csv"


@dataclass
class StrategyResult:
    name: str
    sample_count: int
    # Legacy field kept for compatibility; this equals target_1_hit_rate.
    win_rate: float
    directional_win_rate: float
    avg_4h_return_pct: float
    avg_24h_return_pct: float
    stop_rate: float
    t1_hit_rate: float
    expectancy_proxy: float
    verdict: str
    notes: List[str] = field(default_factory=list)


def _load_evaluations() -> pd.DataFrame:
    if not EVALUATIONS_FILE.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(EVALUATIONS_FILE)
    except Exception:
        return pd.DataFrame()
    if df.empty:
        return df
    if "evaluation_status" in df.columns:
        df = df[df["evaluation_status"].astype(str) == "COMPLETE"].copy()
    if "candle_timestamp" in df.columns:
        df["candle_timestamp"] = pd.to_datetime(df["candle_timestamp"], errors="coerce")
    return df


def _bool_rate(series) -> float:
    if series is None or len(series) == 0:
        return 0.0
    values = series.astype(str).str.lower().isin(["true", "1", "yes"])
    return round(float(values.mean() * 100), 2) if len(values) else 0.0


def _strategy_filters() -> list[tuple[str, Callable[[pd.DataFrame], pd.Series], str]]:
    return [
        (
            "Baseline: all complete decisions",
            lambda df: pd.Series([True] * len(df), index=df.index),
            "همه تصمیم‌های COMPLETE بدون فیلتر.",
        ),
        (
            "Score >= 55",
            lambda df: pd.to_numeric(df.get("score"), errors="coerce").fillna(0) >= 55,
            "حداقل Score متوسط.",
        ),
        (
            "Score >= 65",
            lambda df: pd.to_numeric(df.get("score"), errors="coerce").fillna(0) >= 65,
            "فقط تصمیم‌های قوی‌تر.",
        ),
        (
            "Score >= 70",
            lambda df: pd.to_numeric(df.get("score"), errors="coerce").fillna(0) >= 70,
            "فقط تصمیم‌های High Score.",
        ),
        (
            "WATCHLIST or better",
            lambda df: df.get("actionability", pd.Series([], dtype=str)).astype(str).isin(["WATCHLIST", "ACTIONABLE", "HIGH_ACTIONABILITY"]),
            "فقط تصمیم‌هایی که موتور ارزش زیرنظر گرفتن یا بهتر داده.",
        ),
        (
            "LONG only",
            lambda df: df.get("side", pd.Series([], dtype=str)).astype(str) == "LONG",
            "فقط بایاس لانگ.",
        ),
        (
            "No stop hits",
            lambda df: ~df.get("stop_hit", pd.Series([], dtype=str)).astype(str).str.lower().isin(["true", "1", "yes"]),
            "نمونه‌هایی که در گذشته Stop نخورده‌اند؛ فقط برای تشخیص کیفیت نه استفاده اجرایی.",
        ),
    ]


def _evaluate_strategy(name: str, df: pd.DataFrame, mask: pd.Series, description: str) -> StrategyResult:
    subset = df[mask].copy() if len(df) else pd.DataFrame()
    n = len(subset)
    if n == 0:
        return StrategyResult(
            name=name,
            sample_count=0,
            win_rate=0.0,
            directional_win_rate=0.0,
            avg_4h_return_pct=0.0,
            avg_24h_return_pct=0.0,
            stop_rate=0.0,
            t1_hit_rate=0.0,
            expectancy_proxy=0.0,
            verdict="NO_DATA",
            notes=[description, "نمونه‌ای برای این فیلتر وجود ندارد."],
        )

    ret4 = pd.to_numeric(subset.get("return_after_4h_pct"), errors="coerce")
    ret24 = pd.to_numeric(subset.get("return_after_24h_pct"), errors="coerce")
    t1 = _bool_rate(subset.get("target_1_hit", pd.Series(dtype=object)))
    stop = _bool_rate(subset.get("stop_hit", pd.Series(dtype=object)))
    avg4 = round(float(ret4.dropna().mean()), 4) if not ret4.dropna().empty else 0.0
    avg24 = round(float(ret24.dropna().mean()), 4) if not ret24.dropna().empty else 0.0
    direction_returns = ret24.dropna()
    if direction_returns.empty:
        direction_returns = ret4.dropna()
    directional_win = round(float((direction_returns > 0).mean() * 100), 2) if not direction_returns.empty else 0.0
    win_rate = t1  # legacy: target_1_hit_rate
    expectancy = avg24

    notes = [description]
    if n < 20:
        notes.append("نمونه کم است؛ نتیجه فقط سیگنال تحقیقاتی است.")
    if avg24 > 0 and win_rate >= 55:
        verdict = "PROMISING"
        notes.append("بازده 24h و Target 1 Hit هر دو قابل قبول‌اند.")
    elif avg24 > 0:
        verdict = "MIXED_POSITIVE"
        notes.append("بازده متوسط مثبت است اما Target 1 Hit هنوز قطعی نیست.")
    elif win_rate >= 55:
        verdict = "MIXED_WINRATE"
        notes.append("Target 1 Hit بد نیست اما بازده متوسط مثبت نشده است.")
    else:
        verdict = "WEAK"
        notes.append("فعلاً مزیت واضحی نشان نمی‌دهد.")

    return StrategyResult(
        name=name,
        sample_count=n,
        win_rate=round(win_rate, 2),
        directional_win_rate=directional_win,
        avg_4h_return_pct=avg4,
        avg_24h_return_pct=avg24,
        stop_rate=round(stop, 2),
        t1_hit_rate=round(t1, 2),
        expectancy_proxy=round(expectancy, 4),
        verdict=verdict,
        notes=notes,
    )


def run_strategy_lab() -> List[StrategyResult]:
    df = _load_evaluations()
    if df.empty:
        return []
    results = []
    for name, func, desc in _strategy_filters():
        try:
            mask = func(df)
            if len(mask) != len(df):
                mask = pd.Series([False] * len(df), index=df.index)
        except Exception:
            mask = pd.Series([False] * len(df), index=df.index)
        results.append(_evaluate_strategy(name, df, mask, desc))
    return sorted(results, key=lambda r: (r.verdict in {"PROMISING", "MIXED_POSITIVE"}, r.expectancy_proxy, r.win_rate, r.sample_count), reverse=True)


def save_strategy_results(results: List[StrategyResult]) -> tuple[Path, Path]:
    STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    csv_path = STRATEGY_DIR / f"strategy_lab_results_{stamp}.csv"
    report_path = STRATEGY_DIR / f"strategy_lab_report_{stamp}.md"

    rows = []
    for r in results:
        rows.append({
            "name": r.name,
            "sample_count": r.sample_count,
            "target_1_hit_rate": r.t1_hit_rate,
            "directional_win_rate": r.directional_win_rate,
            "legacy_win_rate_equals_target_1_hit_rate": r.win_rate,
            "avg_4h_return_pct": r.avg_4h_return_pct,
            "avg_24h_return_pct": r.avg_24h_return_pct,
            "stop_rate": r.stop_rate,
            "t1_hit_rate": r.t1_hit_rate,
            "expectancy_proxy": r.expectancy_proxy,
            "verdict": r.verdict,
            "notes": " | ".join(r.notes),
        })

    if rows:
        with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    else:
        csv_path.write_text("name,sample_count,verdict\n", encoding="utf-8-sig")

    report_path.write_text(format_strategy_lab_report(results), encoding="utf-8")
    return csv_path, report_path


def format_strategy_lab_console(results: List[StrategyResult]) -> str:
    lines = []
    lines.append("=" * 110)
    lines.append("🧪 Freakto Strategy Lab v4.7.1")
    lines.append("=" * 110)
    if not results:
        lines.append("No complete decision evaluations found. Run: python decision_evaluator.py")
        lines.append("=" * 110)
        return "\n".join(lines)
    lines.append(f"Strategies tested: {len(results)}")
    lines.append("")
    for r in results:
        lines.append("-" * 110)
        lines.append(f"Strategy    : {r.name}")
        lines.append(f"Samples     : {r.sample_count}")
        lines.append(f"Target 1 Hit: {r.t1_hit_rate:.2f}%")
        lines.append(f"Dir Win     : {r.directional_win_rate:.2f}%")
        lines.append(f"Avg 24h     : {r.avg_24h_return_pct:.4f}%")
        lines.append(f"Stop Rate   : {r.stop_rate:.2f}%")
        lines.append(f"Verdict     : {r.verdict}")
        for note in r.notes[:3]:
            lines.append(f"Note        : {note}")
    lines.append("=" * 110)
    return "\n".join(lines)


def format_strategy_lab_report(results: List[StrategyResult]) -> str:
    lines = ["# Freakto Strategy Lab v4.7.1", "", f"Created UTC: {datetime.now(timezone.utc).isoformat()}", ""]
    if not results:
        lines.append("No complete decision evaluations found.")
        return "\n".join(lines)
    lines.append("## Results")
    for r in results:
        lines.append(f"### {r.name}")
        lines.append(f"- Samples: {r.sample_count}")
        lines.append(f"- Target 1 Hit Rate: {r.t1_hit_rate:.2f}%")
        lines.append(f"- Directional Win Rate: {r.directional_win_rate:.2f}%")
        lines.append(f"- Avg 24h Return: {r.avg_24h_return_pct:.4f}%")
        lines.append(f"- Stop Rate: {r.stop_rate:.2f}%")
        lines.append(f"- Verdict: {r.verdict}")
        for note in r.notes:
            lines.append(f"- {note}")
        lines.append("")
    return "\n".join(lines)
