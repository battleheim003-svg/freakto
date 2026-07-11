"""Freakto v10.1.5 - Replay Evaluation Recorder and historical backfill.

The v10 replay engine already stores horizon-specific metrics such as
``net_signed_return_after_6c_pct``.  This module converts those fields into a
stable canonical schema for optimization and can safely backfill existing
replay CSV files.

Research only.  It never changes Decision Engine weights and never sends
Paper or Live orders.
"""
from __future__ import annotations

import json
import math
import os
import shutil
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

VERSION = "v10.1.5"
DEFAULT_REPLAY_FILE = Path("logs") / "market_replay" / "market_replay_evaluations.csv"
CANONICAL_COLUMNS = [
    "evaluation_recorder_version",
    "primary_evaluation_horizon_candles",
    "primary_evaluation_horizon_label",
    "exit_price",
    "market_return_pct",
    "gross_return_pct",
    "net_return_pct",
    "win",
    "direction_correct",
    "target_hit",
    "outcome_label",
    "evaluation_metric_source",
    "return",
    "net_return",
]


@dataclass
class RecorderReport:
    version: str
    input_file: str
    rows_total: int
    rows_directional: int
    rows_complete: int
    rows_recorded: int
    rows_pending: int
    rows_neutral: int
    primary_horizon_candles: int
    primary_horizon_label: str
    gross_source_column: str
    net_source_column: str
    market_source_column: str
    schema_status: str
    apply_requested: bool
    backup_file: str = ""
    output_file: str = ""
    blockers: List[str] = None
    warnings: List[str] = None

    def __post_init__(self) -> None:
        self.blockers = list(self.blockers or [])
        self.warnings = list(self.warnings or [])


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or pd.isna(value):
            return None
        text = str(value).strip()
        if not text or text.lower() in {"nan", "none", "null"}:
            return None
        return float(text)
    except Exception:
        return None


def _truthy(value: Any) -> Optional[bool]:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


def _available_horizons(columns: Iterable[str]) -> List[int]:
    result: set[int] = set()
    prefix = "net_signed_return_after_"
    suffix = "c_pct"
    for column in columns:
        if column.startswith(prefix) and column.endswith(suffix):
            raw = column[len(prefix) : -len(suffix)]
            try:
                result.add(int(raw))
            except ValueError:
                pass
    return sorted(result)


def _choose_horizon(frame: pd.DataFrame, requested: int = 0) -> int:
    horizons = _available_horizons(frame.columns)
    if requested > 0:
        return requested
    if "primary_evaluation_horizon_candles" in frame.columns:
        values = pd.to_numeric(frame["primary_evaluation_horizon_candles"], errors="coerce").dropna()
        if len(values):
            value = int(values.mode().iloc[0])
            if value > 0:
                return value
    if 6 in horizons:
        return 6
    return max(horizons) if horizons else 0


def _horizon_label(frame: pd.DataFrame, horizon: int) -> str:
    if horizon <= 0:
        return "UNKNOWN"
    timeframe = "4h"
    if "timeframe" in frame.columns:
        values = frame["timeframe"].dropna().astype(str)
        if len(values):
            timeframe = values.mode().iloc[0]
    unit = timeframe.strip().lower()
    multiplier_hours = 4.0
    try:
        if unit.endswith("h"):
            multiplier_hours = float(unit[:-1])
        elif unit.endswith("d"):
            multiplier_hours = float(unit[:-1]) * 24.0
        elif unit.endswith("m"):
            multiplier_hours = float(unit[:-1]) / 60.0
    except Exception:
        multiplier_hours = 4.0
    total_hours = multiplier_hours * horizon
    if total_hours >= 24 and abs(total_hours % 24) < 1e-9:
        return f"{int(total_hours / 24)}d"
    if abs(total_hours - round(total_hours)) < 1e-9:
        return f"{int(round(total_hours))}h"
    return f"{total_hours:.2f}h"


def _source_columns(frame: pd.DataFrame, horizon: int) -> Tuple[str, str, str, str]:
    candidates = [
        (
            f"market_return_after_{horizon}c_pct",
            f"gross_signed_return_after_{horizon}c_pct",
            f"net_signed_return_after_{horizon}c_pct",
            f"direction_correct_after_{horizon}c",
        )
    ]
    # Compatibility aliases from v10 for the standard 4h/24h primary horizon.
    if horizon == 6:
        candidates.append((
            "market_return_after_24h_pct",
            "return_after_24h_pct",
            "net_return_after_24h_pct",
            "direction_correct_after_6c",
        ))
    for market, gross, net, correct in candidates:
        if gross in frame.columns and net in frame.columns:
            return market if market in frame.columns else "", gross, net, correct if correct in frame.columns else ""
    return "", "", "", ""


def record_canonical_metrics(
    frame: pd.DataFrame,
    *,
    primary_horizon_candles: int = 0,
) -> Tuple[pd.DataFrame, RecorderReport]:
    work = frame.copy()
    horizon = _choose_horizon(work, primary_horizon_candles)
    label = _horizon_label(work, horizon)
    market_col, gross_col, net_col, correct_col = _source_columns(work, horizon)
    blockers: List[str] = []
    warnings: List[str] = []

    if horizon <= 0:
        blockers.append("هیچ horizon metric در Replay CSV پیدا نشد.")
    if not gross_col or not net_col:
        blockers.append("ستون‌های gross/net horizon برای ساخت canonical metrics پیدا نشد.")

    side = work.get("side", pd.Series("", index=work.index)).astype(str).str.upper()
    directional = side.isin(["LONG", "SHORT"])
    neutral = ~directional
    complete = work.get("evaluation_status", pd.Series("", index=work.index)).astype(str).eq("COMPLETE")

    gross = pd.to_numeric(work[gross_col], errors="coerce") if gross_col else pd.Series(float("nan"), index=work.index)
    net = pd.to_numeric(work[net_col], errors="coerce") if net_col else pd.Series(float("nan"), index=work.index)
    market = pd.to_numeric(work[market_col], errors="coerce") if market_col else pd.Series(float("nan"), index=work.index)
    entry = pd.to_numeric(work.get("entry_price", pd.Series(float("nan"), index=work.index)), errors="coerce")
    exit_price = entry * (1.0 + market / 100.0)

    direction_correct = (
        work[correct_col].map(_truthy) if correct_col else (gross > 0)
    )
    target_hit = work.get("target_1_hit", pd.Series(False, index=work.index)).map(_truthy)
    recorded = directional & complete & net.notna()

    work["evaluation_recorder_version"] = VERSION
    work["primary_evaluation_horizon_candles"] = horizon if horizon > 0 else None
    work["primary_evaluation_horizon_label"] = label
    work["exit_price"] = exit_price.where(market.notna())
    work["market_return_pct"] = market
    work["gross_return_pct"] = gross.where(directional)
    work["net_return_pct"] = net.where(directional)
    work["win"] = (net > 0).where(recorded)
    work["direction_correct"] = pd.Series(direction_correct, index=work.index).where(directional)
    work["target_hit"] = pd.Series(target_hit, index=work.index).where(directional)
    work["outcome_label"] = "PENDING"
    work.loc[neutral, "outcome_label"] = "NEUTRAL"
    work.loc[recorded & (net > 0), "outcome_label"] = "WIN"
    work.loc[recorded & (net <= 0), "outcome_label"] = "LOSS"
    work["evaluation_metric_source"] = f"{gross_col}|{net_col}" if gross_col and net_col else "MISSING"
    # Compatibility aliases for v10.1.0-v10.1.4 prototypes.
    work["return"] = work["gross_return_pct"]
    work["net_return"] = work["net_return_pct"]

    pending = directional & ~recorded
    if int(pending.sum()):
        warnings.append(f"{int(pending.sum())} directional rows هنوز metric کامل ندارند و PENDING ماندند.")

    status = "CANONICAL_METRICS_RECORDED" if not blockers else "CANONICAL_METRICS_BLOCKED"
    report = RecorderReport(
        version=VERSION,
        input_file="",
        rows_total=int(len(work)),
        rows_directional=int(directional.sum()),
        rows_complete=int(complete.sum()),
        rows_recorded=int(recorded.sum()),
        rows_pending=int(pending.sum()),
        rows_neutral=int(neutral.sum()),
        primary_horizon_candles=int(horizon),
        primary_horizon_label=label,
        gross_source_column=gross_col,
        net_source_column=net_col,
        market_source_column=market_col,
        schema_status=status,
        apply_requested=False,
        blockers=blockers,
        warnings=warnings,
    )
    return work, report


def _atomic_write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.stem + "_", suffix=".tmp.csv", dir=str(path.parent))
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        frame.to_csv(temp_path, index=False, encoding="utf-8-sig")
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def backfill_replay_file(
    path: str | Path = DEFAULT_REPLAY_FILE,
    *,
    apply: bool = False,
    primary_horizon_candles: int = 0,
) -> Tuple[pd.DataFrame, RecorderReport]:
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"Replay evaluations file not found: {target}")
    source = pd.read_csv(target, encoding="utf-8-sig")
    repaired, report = record_canonical_metrics(
        source,
        primary_horizon_candles=primary_horizon_candles,
    )
    report.input_file = str(target)
    report.apply_requested = bool(apply)
    report.output_file = str(target)

    if apply and not report.blockers:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup = target.with_name(f"{target.name}.bak_v1015_{timestamp}")
        shutil.copy2(target, backup)
        _atomic_write_csv(repaired, target)
        report.backup_file = str(backup)
    return repaired, report


def report_to_dict(report: RecorderReport) -> Dict[str, Any]:
    return asdict(report)


def format_recorder_console(report: RecorderReport) -> str:
    lines = [
        "=" * 110,
        f"🧾 Freakto Replay Evaluation Recorder {VERSION}",
        "=" * 110,
        f"Status                 : {report.schema_status}",
        f"Input                  : {report.input_file}",
        f"Rows Total/Directional : {report.rows_total} / {report.rows_directional}",
        f"Complete / Recorded    : {report.rows_complete} / {report.rows_recorded}",
        f"Pending / Neutral      : {report.rows_pending} / {report.rows_neutral}",
        f"Primary Horizon        : {report.primary_horizon_label} ({report.primary_horizon_candles} candles)",
        f"Gross Source           : {report.gross_source_column or 'NOT_FOUND'}",
        f"Net Source             : {report.net_source_column or 'NOT_FOUND'}",
        f"Market Source          : {report.market_source_column or 'NOT_FOUND'}",
        f"Mode                   : {'APPLY' if report.apply_requested else 'DRY_RUN'}",
    ]
    if report.backup_file:
        lines.append(f"Backup                 : {report.backup_file}")
    if report.blockers:
        lines += ["", "Blockers:"] + [f"⛔ {item}" for item in report.blockers]
    if report.warnings:
        lines += ["", "Warnings:"] + [f"⚠️ {item}" for item in report.warnings]
    lines += [
        "",
        "Safety:",
        "⚠️ این ابزار فقط schema تحقیقاتی Replay را استاندارد می‌کند؛ هیچ Paper/Live فعال نمی‌کند.",
        "=" * 110,
    ]
    return "\n".join(lines)
