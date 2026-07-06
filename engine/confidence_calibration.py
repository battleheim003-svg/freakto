"""
engine.confidence_calibration

Freakto v5.0 Confidence Calibration Engine

Checks whether internal confidence labels/buckets match observed outcomes. This
is not a predictive model; it is a validation layer that shows calibration gaps.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import pandas as pd

LOGS_DIR = Path("logs")
CAL_DIR = LOGS_DIR / "confidence_calibration"
DECISIONS_FILE = LOGS_DIR / "decisions.csv"
DECISION_EVALS_FILE = LOGS_DIR / "decision_evaluations.csv"

CONFIDENCE_MIDPOINTS = {
    "VERY LOW": 10.0,
    "LOW": 25.0,
    "MEDIUM-LOW": 40.0,
    "MEDIUM": 55.0,
    "MEDIUM-HIGH": 67.5,
    "HIGH": 80.0,
    "VERY HIGH": 90.0,
}


@dataclass
class CalibrationBucket:
    bucket: str
    sample_count: int
    predicted_confidence: float
    directional_win_rate: float
    target_1_hit_rate: float
    avg_return_pct: float
    calibration_gap: float
    target_gap: float
    verdict: str
    notes: List[str] = field(default_factory=list)


@dataclass
class ConfidenceCalibrationResult:
    created_utc: str
    source: str
    sample_count: int
    overall_directional_win_rate: float
    overall_target_1_hit_rate: float
    mean_calibration_error: float
    confidence_quality: str
    label_buckets: List[CalibrationBucket]
    score_buckets: List[CalibrationBucket]
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


def _pct(n: float, d: float) -> float:
    return round(float(n) / float(d) * 100.0, 2) if d else 0.0


def _bool_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series([False] * len(frame), index=frame.index)
    return frame[column].astype(str).str.lower().isin(["true", "1", "yes", "y", "win"])


def _return_column(frame: pd.DataFrame) -> Optional[str]:
    for column in ["return_after_24h_pct", "return_after_12h_pct", "return_after_4h_pct"]:
        if column in frame.columns and pd.to_numeric(frame[column], errors="coerce").notna().any():
            return column
    return None


def _label_midpoint(label: str) -> float:
    key = str(label).strip().upper().replace("_", "-")
    return CONFIDENCE_MIDPOINTS.get(key, 50.0)


def _score_bucket(score: float) -> str:
    try:
        s = float(score)
    except Exception:
        return "score_unknown"
    lower = int(s // 10 * 10)
    upper = lower + 9
    return f"score_{lower}_{upper}"


def _score_bucket_midpoint(bucket: str) -> float:
    if bucket == "score_unknown":
        return 50.0
    try:
        parts = bucket.split("_")
        return (float(parts[1]) + float(parts[2])) / 2.0
    except Exception:
        return 50.0


def _prepare_frame() -> pd.DataFrame:
    evals = _load_csv(DECISION_EVALS_FILE)
    decisions = _load_csv(DECISIONS_FILE)
    if evals.empty:
        return pd.DataFrame()
    frame = evals.copy()
    if "evaluation_status" in frame.columns:
        frame = frame[frame["evaluation_status"].astype(str).str.upper() == "COMPLETE"].copy()
    ret_col = _return_column(frame)
    if not ret_col:
        return pd.DataFrame()
    frame["evaluated_return"] = pd.to_numeric(frame[ret_col], errors="coerce")
    frame = frame.dropna(subset=["evaluated_return"])
    if not decisions.empty and "decision_id" in frame.columns and "decision_id" in decisions.columns:
        cols = ["decision_id"]
        for col in ["confidence_label", "score", "symbol", "side", "actionability"]:
            if col in decisions.columns and col not in frame.columns:
                cols.append(col)
        if len(cols) > 1:
            frame = frame.merge(decisions[cols].drop_duplicates("decision_id"), on="decision_id", how="left")
    if "confidence_label" not in frame.columns:
        frame["confidence_label"] = "UNKNOWN"
    if "score" not in frame.columns:
        frame["score"] = 50
    frame["directional_win"] = frame["evaluated_return"] > 0
    frame["target_1_hit_bool"] = _bool_series(frame, "target_1_hit")
    frame["confidence_midpoint"] = frame["confidence_label"].map(_label_midpoint)
    frame["score_bucket"] = frame["score"].map(_score_bucket)
    return frame


def _bucket_from_group(bucket: str, group: pd.DataFrame, predicted: float) -> CalibrationBucket:
    n = len(group)
    dir_win = _pct(group["directional_win"].sum(), n)
    t1 = _pct(group["target_1_hit_bool"].sum(), n)
    avg_ret = round(float(group["evaluated_return"].mean()), 4) if n else 0.0
    gap = round(dir_win - predicted, 2)
    target_gap = round(t1 - predicted, 2)
    notes: List[str] = []
    if n < 10:
        verdict = "LOW_SAMPLE"
        notes.append("نمونه کمتر از 10 است؛ Calibration فقط برای رصد است.")
    elif abs(gap) <= 10:
        verdict = "WELL_CALIBRATED_DIRECTIONAL"
        notes.append("Directional Win با confidence داخلی نزدیک است.")
    elif gap > 10:
        verdict = "UNDER_CONFIDENT"
        notes.append("عملکرد واقعی بالاتر از confidence داخلی بوده است.")
    else:
        verdict = "OVER_CONFIDENT"
        notes.append("confidence داخلی از عملکرد واقعی بالاتر بوده است.")
    if t1 < predicted - 15:
        notes.append("Target 1 Hit نسبت به confidence پایین‌تر است؛ برای اهداف قیمتی محافظه‌کار باشید.")
    return CalibrationBucket(
        bucket=str(bucket),
        sample_count=int(n),
        predicted_confidence=round(float(predicted), 2),
        directional_win_rate=dir_win,
        target_1_hit_rate=t1,
        avg_return_pct=avg_ret,
        calibration_gap=gap,
        target_gap=target_gap,
        verdict=verdict,
        notes=notes,
    )


def run_confidence_calibration() -> ConfidenceCalibrationResult:
    frame = _prepare_frame()
    if frame.empty:
        return ConfidenceCalibrationResult(
            created_utc=datetime.now(timezone.utc).isoformat(),
            source="decision_evaluations",
            sample_count=0,
            overall_directional_win_rate=0.0,
            overall_target_1_hit_rate=0.0,
            mean_calibration_error=0.0,
            confidence_quality="NO_DATA",
            label_buckets=[],
            score_buckets=[],
            warnings=["داده کافی برای Confidence Calibration وجود ندارد."],
            blockers=["decision_evaluations.csv خالی است یا return قابل ارزیابی ندارد."],
        )

    n = len(frame)
    label_buckets: List[CalibrationBucket] = []
    for label, group in frame.groupby("confidence_label", dropna=False):
        label_buckets.append(_bucket_from_group(str(label), group, _label_midpoint(str(label))))

    score_buckets: List[CalibrationBucket] = []
    for bucket, group in frame.groupby("score_bucket", dropna=False):
        score_buckets.append(_bucket_from_group(str(bucket), group, _score_bucket_midpoint(str(bucket))))

    all_buckets = label_buckets + score_buckets
    weighted_error = 0.0
    total_weight = 0
    for b in all_buckets:
        weighted_error += abs(b.calibration_gap) * b.sample_count
        total_weight += b.sample_count
    mean_error = round(weighted_error / total_weight, 2) if total_weight else 0.0

    overall_dir = _pct(frame["directional_win"].sum(), n)
    overall_t1 = _pct(frame["target_1_hit_bool"].sum(), n)

    warnings: List[str] = []
    blockers: List[str] = []
    notes: List[str] = []
    if n < 30:
        quality = "LOW_SAMPLE_CALIBRATION"
        warnings.append(f"Calibration sample کمتر از 30 است: {n}")
    elif mean_error <= 10:
        quality = "CALIBRATION_OK"
        notes.append("میانگین خطای Calibration قابل قبول است.")
    elif mean_error <= 20:
        quality = "CALIBRATION_MIXED"
        warnings.append("Calibration متوسط است؛ برخی confidence bucketها نیاز به داده بیشتر دارند.")
    else:
        quality = "CALIBRATION_WEAK"
        blockers.append("Confidence داخلی با outcome واقعی فاصله زیادی دارد.")

    if n < 100:
        blockers.append(f"برای استفاده عملی، حداقل 100 ارزیابی لازم است: {n}/100")

    label_buckets.sort(key=lambda b: b.predicted_confidence)
    score_buckets.sort(key=lambda b: b.predicted_confidence)

    return ConfidenceCalibrationResult(
        created_utc=datetime.now(timezone.utc).isoformat(),
        source="decision_evaluations",
        sample_count=int(n),
        overall_directional_win_rate=overall_dir,
        overall_target_1_hit_rate=overall_t1,
        mean_calibration_error=mean_error,
        confidence_quality=quality,
        label_buckets=label_buckets,
        score_buckets=score_buckets,
        notes=notes,
        warnings=warnings,
        blockers=blockers,
    )


def format_confidence_calibration_console(result: ConfidenceCalibrationResult) -> str:
    lines: List[str] = []
    lines.append("=" * 110)
    lines.append("🎯 Freakto Confidence Calibration Engine v5.0")
    lines.append("=" * 110)
    lines.append(f"Created UTC       : {result.created_utc}")
    lines.append(f"Quality           : {result.confidence_quality}")
    lines.append(f"Samples           : {result.sample_count}")
    lines.append(f"Overall Dir Win   : {result.overall_directional_win_rate:.2f}%")
    lines.append(f"Overall T1 Hit    : {result.overall_target_1_hit_rate:.2f}%")
    lines.append(f"Mean Calib Error  : {result.mean_calibration_error:.2f} pts")
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
    if result.label_buckets:
        lines.append("-" * 110)
        lines.append("Confidence Label Buckets")
        for b in result.label_buckets:
            lines.append(f"{b.bucket:14} | n={b.sample_count:3} | Pred {b.predicted_confidence:5.1f}% | Dir {b.directional_win_rate:6.2f}% | T1 {b.target_1_hit_rate:6.2f}% | Gap {b.calibration_gap:+6.2f} | {b.verdict}")
    if result.score_buckets:
        lines.append("-" * 110)
        lines.append("Score Buckets")
        for b in result.score_buckets:
            lines.append(f"{b.bucket:14} | n={b.sample_count:3} | Pred {b.predicted_confidence:5.1f}% | Dir {b.directional_win_rate:6.2f}% | T1 {b.target_1_hit_rate:6.2f}% | Gap {b.calibration_gap:+6.2f} | {b.verdict}")
    lines.append("=" * 110)
    return "\n".join(lines)


def format_confidence_calibration_report(result: ConfidenceCalibrationResult) -> str:
    lines = ["# Freakto Confidence Calibration Engine v5.0", "", f"Created UTC: {result.created_utc}", ""]
    lines.append(f"- Quality: **{result.confidence_quality}**")
    lines.append(f"- Samples: {result.sample_count}")
    lines.append(f"- Overall Directional Win: {result.overall_directional_win_rate:.2f}%")
    lines.append(f"- Overall Target 1 Hit: {result.overall_target_1_hit_rate:.2f}%")
    lines.append(f"- Mean Calibration Error: {result.mean_calibration_error:.2f} pts")
    if result.warnings:
        lines.append("\n## Warnings")
        for w in result.warnings:
            lines.append(f"- {w}")
    if result.blockers:
        lines.append("\n## Blockers")
        for b in result.blockers:
            lines.append(f"- {b}")
    lines.append("\n## Confidence Label Buckets")
    for b in result.label_buckets:
        lines.append(f"- **{b.bucket}**: n={b.sample_count}, predicted={b.predicted_confidence:.1f}%, directional={b.directional_win_rate:.2f}%, T1={b.target_1_hit_rate:.2f}%, gap={b.calibration_gap:+.2f}, verdict={b.verdict}")
    lines.append("\n## Score Buckets")
    for b in result.score_buckets:
        lines.append(f"- **{b.bucket}**: n={b.sample_count}, predicted={b.predicted_confidence:.1f}%, directional={b.directional_win_rate:.2f}%, T1={b.target_1_hit_rate:.2f}%, gap={b.calibration_gap:+.2f}, verdict={b.verdict}")
    return "\n".join(lines)


def save_confidence_calibration(result: ConfidenceCalibrationResult) -> tuple[Path, Path]:
    CAL_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = CAL_DIR / f"confidence_calibration_{stamp}.json"
    report_path = CAL_DIR / f"confidence_calibration_report_{stamp}.md"
    json_path.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(format_confidence_calibration_report(result), encoding="utf-8")
    return json_path, report_path
