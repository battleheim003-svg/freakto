"""
engine.walk_forward

Freakto v4.7.1 Walk-Forward Validation

Runs simple chronological train/test checks on evaluated decisions to detect
whether a filter works only in-sample and fails out-of-sample.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List

import pandas as pd

LOGS_DIR = Path("logs")
WF_DIR = LOGS_DIR / "walk_forward"
EVALUATIONS_FILE = LOGS_DIR / "decision_evaluations.csv"


@dataclass
class WalkForwardResult:
    strategy: str
    train_samples: int
    test_samples: int
    train_avg24: float
    test_avg24: float
    # Legacy win fields equal Target 1 Hit Rate.
    train_win_rate: float
    test_win_rate: float
    train_directional_win_rate: float
    test_directional_win_rate: float
    stability_gap: float
    verdict: str
    notes: List[str] = field(default_factory=list)


def _load_complete_evals() -> pd.DataFrame:
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
        df = df.dropna(subset=["candle_timestamp"]).sort_values("candle_timestamp")
    return df


def _filters() -> list[tuple[str, Callable[[pd.DataFrame], pd.Series]]]:
    return [
        ("All complete decisions", lambda df: pd.Series([True] * len(df), index=df.index)),
        ("Score >= 55", lambda df: pd.to_numeric(df.get("score"), errors="coerce").fillna(0) >= 55),
        ("Score >= 65", lambda df: pd.to_numeric(df.get("score"), errors="coerce").fillna(0) >= 65),
        ("WATCHLIST or better", lambda df: df.get("actionability", pd.Series([], dtype=str)).astype(str).isin(["WATCHLIST", "ACTIONABLE", "HIGH_ACTIONABILITY"])),
    ]


def _target_1_hit_rate(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    values = df.get("target_1_hit", pd.Series(dtype=object)).astype(str).str.lower().isin(["true", "1", "yes"])
    return round(float(values.mean() * 100), 2) if len(values) else 0.0


def _directional_win_rate(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    ret = pd.to_numeric(df.get("return_after_24h_pct"), errors="coerce").dropna()
    if ret.empty:
        ret = pd.to_numeric(df.get("return_after_12h_pct"), errors="coerce").dropna()
    if ret.empty:
        ret = pd.to_numeric(df.get("return_after_4h_pct"), errors="coerce").dropna()
    return round(float((ret > 0).mean() * 100), 2) if not ret.empty else 0.0


def _avg24(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    ret = pd.to_numeric(df.get("return_after_24h_pct"), errors="coerce").dropna()
    return round(float(ret.mean()), 4) if not ret.empty else 0.0


def _split_train_test(df: pd.DataFrame, train_ratio: float = 0.7) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        return df, df
    split_idx = max(1, int(len(df) * train_ratio))
    if split_idx >= len(df):
        split_idx = max(1, len(df) - 1)
    return df.iloc[:split_idx].copy(), df.iloc[split_idx:].copy()


def _evaluate(strategy: str, train: pd.DataFrame, test: pd.DataFrame) -> WalkForwardResult:
    train_avg = _avg24(train)
    test_avg = _avg24(test)
    train_win = _target_1_hit_rate(train)
    test_win = _target_1_hit_rate(test)
    train_dir = _directional_win_rate(train)
    test_dir = _directional_win_rate(test)
    gap = round(abs(train_avg - test_avg), 4)
    notes = []

    if len(train) < 10 or len(test) < 5:
        verdict = "LOW_SAMPLE"
        notes.append("نمونه train/test کم است؛ نتیجه فقط برای رصد است.")
    elif train_avg > 0 and test_avg > 0 and test_win >= 50:
        verdict = "STABLE_POSITIVE"
        notes.append("هم train و هم test مثبت‌اند؛ نشانه اولیه پایداری دیده می‌شود.")
    elif train_avg > 0 and test_avg <= 0:
        verdict = "OVERFIT_RISK"
        notes.append("در train مثبت است اما در test افت کرده؛ ریسک overfitting وجود دارد.")
    elif test_avg > 0:
        verdict = "TEST_POSITIVE_MIXED"
        notes.append("test مثبت است اما train/نمونه‌ها نیاز به بررسی بیشتر دارند.")
    else:
        verdict = "WEAK"
        notes.append("مزیت out-of-sample واضح نیست.")

    return WalkForwardResult(
        strategy=strategy,
        train_samples=len(train),
        test_samples=len(test),
        train_avg24=train_avg,
        test_avg24=test_avg,
        train_win_rate=train_win,
        test_win_rate=test_win,
        train_directional_win_rate=train_dir,
        test_directional_win_rate=test_dir,
        stability_gap=gap,
        verdict=verdict,
        notes=notes,
    )


def run_walk_forward_validation() -> List[WalkForwardResult]:
    df = _load_complete_evals()
    if df.empty:
        return []
    results = []
    for name, func in _filters():
        try:
            mask = func(df)
        except Exception:
            mask = pd.Series([False] * len(df), index=df.index)
        subset = df[mask].copy()
        train, test = _split_train_test(subset)
        results.append(_evaluate(name, train, test))
    return sorted(results, key=lambda r: (r.verdict == "STABLE_POSITIVE", r.test_avg24, r.test_win_rate), reverse=True)


def save_walk_forward_results(results: List[WalkForwardResult]) -> tuple[Path, Path]:
    WF_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    csv_path = WF_DIR / f"walk_forward_results_{stamp}.csv"
    report_path = WF_DIR / f"walk_forward_report_{stamp}.md"

    rows = []
    for r in results:
        rows.append({
            "strategy": r.strategy,
            "train_samples": r.train_samples,
            "test_samples": r.test_samples,
            "train_avg24": r.train_avg24,
            "test_avg24": r.test_avg24,
            "train_target_1_hit_rate": r.train_win_rate,
            "test_target_1_hit_rate": r.test_win_rate,
            "train_directional_win_rate": r.train_directional_win_rate,
            "test_directional_win_rate": r.test_directional_win_rate,
            "stability_gap": r.stability_gap,
            "verdict": r.verdict,
            "notes": " | ".join(r.notes),
        })

    if rows:
        with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    else:
        csv_path.write_text("strategy,train_samples,test_samples,verdict\n", encoding="utf-8-sig")

    report_path.write_text(format_walk_forward_report(results), encoding="utf-8")
    return csv_path, report_path


def format_walk_forward_console(results: List[WalkForwardResult]) -> str:
    lines = []
    lines.append("=" * 110)
    lines.append("🧭 Freakto Walk-Forward Validation v4.7.1")
    lines.append("=" * 110)
    if not results:
        lines.append("No complete evaluations found. Run: python decision_evaluator.py")
        lines.append("=" * 110)
        return "\n".join(lines)
    for r in results:
        lines.append("-" * 110)
        lines.append(f"Strategy       : {r.strategy}")
        lines.append(f"Train/Test     : {r.train_samples} / {r.test_samples}")
        lines.append(f"Train Avg24    : {r.train_avg24:.4f}% | T1 {r.train_win_rate:.2f}% | Dir {r.train_directional_win_rate:.2f}%")
        lines.append(f"Test Avg24     : {r.test_avg24:.4f}% | T1 {r.test_win_rate:.2f}% | Dir {r.test_directional_win_rate:.2f}%")
        lines.append(f"Stability Gap  : {r.stability_gap:.4f}")
        lines.append(f"Verdict        : {r.verdict}")
        for note in r.notes:
            lines.append(f"Note           : {note}")
    lines.append("=" * 110)
    return "\n".join(lines)


def format_walk_forward_report(results: List[WalkForwardResult]) -> str:
    lines = ["# Freakto Walk-Forward Validation v4.7.1", "", f"Created UTC: {datetime.now(timezone.utc).isoformat()}", ""]
    if not results:
        lines.append("No complete evaluations found.")
        return "\n".join(lines)
    for r in results:
        lines.append(f"## {r.strategy}")
        lines.append(f"- Train/Test samples: {r.train_samples}/{r.test_samples}")
        lines.append(f"- Train Avg24: {r.train_avg24:.4f}% | Target 1 Hit {r.train_win_rate:.2f}% | Directional Win {r.train_directional_win_rate:.2f}%")
        lines.append(f"- Test Avg24: {r.test_avg24:.4f}% | Target 1 Hit {r.test_win_rate:.2f}% | Directional Win {r.test_directional_win_rate:.2f}%")
        lines.append(f"- Stability Gap: {r.stability_gap:.4f}")
        lines.append(f"- Verdict: {r.verdict}")
        for note in r.notes:
            lines.append(f"- {note}")
        lines.append("")
    return "\n".join(lines)
