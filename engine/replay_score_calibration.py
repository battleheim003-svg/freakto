"""Freakto v10.2.0 - Replay Score Calibration & Feature Attribution Lab.

Analyzes whether the final decision score and its component features have a
stable relationship with future net returns in chronological Train /
Validation / Test splits.  Thresholds for feature gates are learned from the
TRAIN split only and then applied unchanged to Validation and Test.

Research only.  This module never changes Decision Engine weights and never
places Paper or Live orders.
"""
from __future__ import annotations

import itertools
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from engine.replay_evaluation_recorder import record_canonical_metrics
from engine.replay_schema_adapter import normalize_metrics

VERSION = "v10.2.0"
DEFAULT_FILE = Path("logs") / "market_replay" / "market_replay_evaluations.csv"
OUTPUT_DIR = Path("logs") / "market_replay" / "calibration"
SPLITS = ("TRAIN_60", "VALIDATION_20", "TEST_20")

SCORE_BANDS: Tuple[Tuple[float, float, str], ...] = (
    (-math.inf, 39, "0_39"),
    (40, 49, "40_49"),
    (50, 59, "50_59"),
    (60, 69, "60_69"),
    (70, 79, "70_79"),
    (80, 89, "80_89"),
    (90, math.inf, "90_PLUS"),
)

FEATURES: Tuple[Tuple[str, str], ...] = (
    ("decision_aligned_score", "Decision Aligned Score"),
    ("trend_score", "Trend Score"),
    ("momentum_score", "Momentum Score"),
    ("volume_score", "Volume Score"),
    ("structure_score", "Structure Score"),
    ("regime_score", "Regime Score"),
    ("risk_penalty", "Risk Penalty / Risk Relief"),
    ("regime_confidence", "Regime Confidence"),
)


@dataclass
class Metric:
    samples: int
    win_rate_pct: float
    avg_gross_return_pct: float
    avg_net_return_pct: float
    median_net_return_pct: float
    profit_factor: float
    max_drawdown_proxy_pct: float


@dataclass
class CalibrationSavePaths:
    json_path: str
    report_path: str
    score_bands_csv: str
    feature_attribution_csv: str
    interactions_csv: str
    segments_csv: str
    observations_csv: str


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
        return default if math.isnan(number) or math.isinf(number) else number
    except Exception:
        return default


def _profit_factor(values: pd.Series) -> float:
    series = pd.to_numeric(values, errors="coerce").dropna()
    wins = series[series > 0]
    losses = series[series < 0]
    loss_sum = abs(float(losses.sum()))
    if loss_sum > 0:
        return float(wins.sum()) / loss_sum
    return 999.0 if len(wins) else 0.0


def _metric(frame: pd.DataFrame) -> Metric:
    net = pd.to_numeric(frame.get("normalized_net_return", pd.Series(dtype=float)), errors="coerce").dropna()
    gross = pd.to_numeric(frame.get("normalized_gross_return", pd.Series(dtype=float)), errors="coerce").dropna()
    equity = net.fillna(0.0).cumsum()
    drawdown = equity - equity.cummax() if len(equity) else pd.Series(dtype=float)
    return Metric(
        samples=int(len(net)),
        win_rate_pct=round(float((net > 0).mean() * 100), 2) if len(net) else 0.0,
        avg_gross_return_pct=round(float(gross.mean()), 6) if len(gross) else 0.0,
        avg_net_return_pct=round(float(net.mean()), 6) if len(net) else 0.0,
        median_net_return_pct=round(float(net.median()), 6) if len(net) else 0.0,
        profit_factor=round(_profit_factor(net), 4),
        max_drawdown_proxy_pct=round(float(drawdown.min()), 6) if len(drawdown) else 0.0,
    )


def _spearman(left: pd.Series, right: pd.Series) -> float:
    a = pd.to_numeric(left, errors="coerce")
    b = pd.to_numeric(right, errors="coerce")
    valid = a.notna() & b.notna()
    if int(valid.sum()) < 3 or a[valid].nunique() < 2 or b[valid].nunique() < 2:
        return 0.0
    result = a[valid].corr(b[valid], method="spearman")
    return round(_safe_float(result), 6)


def _prepare(frame: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any], List[str], List[str]]:
    canonical, recorder = record_canonical_metrics(frame)
    normalized, schema = normalize_metrics(canonical)
    blockers = list(recorder.blockers)
    warnings = list(recorder.warnings)

    required = ["normalized_score", "normalized_gross_return", "normalized_net_return"]
    missing = [column for column in required if column not in normalized.columns]
    if missing:
        blockers.append("Missing normalized replay metrics: " + ", ".join(missing))

    if "normalized_side" in normalized.columns:
        normalized = normalized[normalized["normalized_side"].isin(["LONG", "SHORT"])]
    if "normalized_status" in normalized.columns:
        normalized = normalized[normalized["normalized_status"] == "COMPLETE"]
    normalized = normalized[normalized["normalized_net_return"].notna()].copy()

    if normalized.empty:
        blockers.append("No complete directional Replay rows with net return were found.")

    if "long_score" in normalized.columns and "short_score" in normalized.columns and "normalized_side" in normalized.columns:
        long_values = pd.to_numeric(normalized["long_score"], errors="coerce")
        short_values = pd.to_numeric(normalized["short_score"], errors="coerce")
        normalized["decision_aligned_score"] = long_values.where(normalized["normalized_side"] == "LONG", short_values)

    if "replay_split" in normalized.columns and "normalized_split" not in normalized.columns:
        normalized["normalized_split"] = normalized["replay_split"].astype(str)

    split_values = set(normalized.get("normalized_split", pd.Series(dtype=str)).dropna().astype(str))
    missing_splits = [split for split in SPLITS if split not in split_values]
    if missing_splits:
        blockers.append("Missing chronological splits: " + ", ".join(missing_splits))

    return normalized, {"schema": schema, "recorder": asdict(recorder)}, blockers, warnings


def _filter_split(frame: pd.DataFrame, split: str) -> pd.DataFrame:
    if split == "ALL":
        return frame
    return frame[frame.get("normalized_split", pd.Series("", index=frame.index)).astype(str) == split]


def _score_band(value: float) -> str:
    for low, high, label in SCORE_BANDS:
        if low <= value <= high:
            return label
    return "UNKNOWN"


def _score_band_midpoint(label: str) -> float:
    mapping = {
        "0_39": 20.0,
        "40_49": 44.5,
        "50_59": 54.5,
        "60_69": 64.5,
        "70_79": 74.5,
        "80_89": 84.5,
        "90_PLUS": 95.0,
    }
    return mapping.get(label, 0.0)


def _band_analysis(frame: pd.DataFrame) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    work = frame.copy()
    work["score_band"] = pd.to_numeric(work["normalized_score"], errors="coerce").map(
        lambda value: _score_band(float(value)) if pd.notna(value) else "UNKNOWN"
    )
    rows: List[Dict[str, Any]] = []
    split_summaries: Dict[str, Any] = {}

    for split in ("ALL",) + SPLITS:
        part = _filter_split(work, split)
        usable_for_curve: List[Tuple[float, float]] = []
        band_rows: List[Dict[str, Any]] = []
        for _, _, label in SCORE_BANDS:
            band = part[part["score_band"] == label]
            metric = _metric(band)
            row = {"split": split, "score_band": label, **asdict(metric)}
            rows.append(row)
            band_rows.append(row)
            if metric.samples >= 20:
                usable_for_curve.append((_score_band_midpoint(label), metric.avg_net_return_pct))

        if len(usable_for_curve) >= 3:
            curve = pd.DataFrame(usable_for_curve, columns=["score", "avg_net"])
            monotonicity = _spearman(curve["score"], curve["avg_net"])
            violations = int((curve["avg_net"].diff().dropna() < 0).sum())
        else:
            monotonicity = 0.0
            violations = 0

        low = [row for row in band_rows if row["score_band"] in {"50_59", "60_69"} and row["samples"] >= 20]
        high = [row for row in band_rows if row["score_band"] in {"70_79", "80_89", "90_PLUS"} and row["samples"] >= 20]
        low_avg = sum(row["avg_net_return_pct"] * row["samples"] for row in low) / max(1, sum(row["samples"] for row in low)) if low else 0.0
        high_avg = sum(row["avg_net_return_pct"] * row["samples"] for row in high) / max(1, sum(row["samples"] for row in high)) if high else 0.0
        split_summaries[split] = {
            "band_monotonicity_spearman": round(monotonicity, 6),
            "adjacent_band_violations": violations,
            "high_minus_low_avg_net_pct": round(high_avg - low_avg, 6),
            "low_score_avg_net_pct": round(low_avg, 6),
            "high_score_avg_net_pct": round(high_avg, 6),
        }

    test = split_summaries.get("TEST_20", {})
    validation = split_summaries.get("VALIDATION_20", {})
    if test.get("band_monotonicity_spearman", 0.0) < 0 or test.get("high_minus_low_avg_net_pct", 0.0) < 0:
        verdict = "SCORE_INVERTED_OR_MISCALIBRATED"
    elif (
        test.get("band_monotonicity_spearman", 0.0) >= 0.35
        and validation.get("band_monotonicity_spearman", 0.0) >= 0.20
        and test.get("high_minus_low_avg_net_pct", 0.0) > 0
    ):
        verdict = "SCORE_MONOTONIC_RESEARCH_SIGNAL"
    else:
        verdict = "SCORE_WEAK_OR_NON_MONOTONIC"

    return rows, {"verdict": verdict, "splits": split_summaries}


def _feature_thresholds(train: pd.DataFrame, feature: str) -> Tuple[Optional[float], Optional[float]]:
    values = pd.to_numeric(train.get(feature, pd.Series(dtype=float)), errors="coerce").dropna()
    if len(values) < 50 or values.nunique() < 4:
        return None, None
    return float(values.quantile(0.25)), float(values.quantile(0.75))


def _feature_analysis(frame: pd.DataFrame) -> List[Dict[str, Any]]:
    train = _filter_split(frame, "TRAIN_60")
    rows: List[Dict[str, Any]] = []

    for feature, label in FEATURES:
        if feature not in frame.columns:
            continue
        q25, q75 = _feature_thresholds(train, feature)
        values_all = pd.to_numeric(frame[feature], errors="coerce")
        unique_values = int(values_all.nunique(dropna=True))
        if q25 is None or q75 is None or q25 == q75:
            rows.append({
                "feature": feature,
                "label": label,
                "unique_values": unique_values,
                "train_q25": q25,
                "train_q75": q75,
                "verdict": "LOW_VARIANCE_OR_INSUFFICIENT_DATA",
            })
            continue

        item: Dict[str, Any] = {
            "feature": feature,
            "label": label,
            "unique_values": unique_values,
            "train_q25": round(q25, 6),
            "train_q75": round(q75, 6),
        }
        signs: List[int] = []
        for split in SPLITS:
            part = _filter_split(frame, split).copy()
            values = pd.to_numeric(part[feature], errors="coerce")
            valid = values.notna()
            part = part[valid]
            values = values[valid]
            low = part[values <= q25]
            high = part[values >= q75]
            low_metric = _metric(low)
            high_metric = _metric(high)
            spread = high_metric.avg_net_return_pct - low_metric.avg_net_return_pct
            corr = _spearman(values, part["normalized_net_return"])
            item[f"{split.lower()}_correlation"] = corr
            item[f"{split.lower()}_low_samples"] = low_metric.samples
            item[f"{split.lower()}_high_samples"] = high_metric.samples
            item[f"{split.lower()}_low_avg_net_pct"] = low_metric.avg_net_return_pct
            item[f"{split.lower()}_high_avg_net_pct"] = high_metric.avg_net_return_pct
            item[f"{split.lower()}_high_minus_low_pct"] = round(spread, 6)
            signs.append(1 if spread > 0 else (-1 if spread < 0 else 0))

        train_spread, val_spread, test_spread = (
            item.get("train_60_high_minus_low_pct", 0.0),
            item.get("validation_20_high_minus_low_pct", 0.0),
            item.get("test_20_high_minus_low_pct", 0.0),
        )
        test_high_n = int(item.get("test_20_high_samples", 0))
        val_high_n = int(item.get("validation_20_high_samples", 0))
        if min(test_high_n, val_high_n) < 50:
            verdict = "LOW_OUT_OF_SAMPLE_FEATURE_COVERAGE"
        elif train_spread > 0 and val_spread > 0 and test_spread > 0:
            verdict = "STABLE_POSITIVE_ASSOCIATION"
        elif train_spread < 0 and val_spread < 0 and test_spread < 0:
            verdict = "STABLE_INVERSE_ASSOCIATION"
        elif val_spread * test_spread < 0:
            verdict = "UNSTABLE_VALIDATION_TEST_SIGN_FLIP"
        elif test_spread < 0:
            verdict = "NEGATIVE_TEST_ASSOCIATION"
        else:
            verdict = "WEAK_OR_MIXED_ASSOCIATION"
        item["verdict"] = verdict
        item["stability_score"] = round(
            (1 if train_spread * test_spread > 0 else 0)
            + (1 if val_spread * test_spread > 0 else 0)
            + min(1.0, abs(test_spread)),
            4,
        )
        rows.append(item)

    rows.sort(
        key=lambda item: (
            item.get("verdict") == "STABLE_POSITIVE_ASSOCIATION",
            item.get("test_20_high_minus_low_pct", -999.0),
        ),
        reverse=True,
    )
    return rows


def _condition_metric(frame: pd.DataFrame, conditions: Sequence[Tuple[str, float]]) -> Metric:
    mask = pd.Series(True, index=frame.index)
    for feature, threshold in conditions:
        values = pd.to_numeric(frame.get(feature, pd.Series(float("nan"), index=frame.index)), errors="coerce")
        mask &= values >= threshold
    return _metric(frame[mask])


def _interaction_analysis(frame: pd.DataFrame, feature_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    eligible = [
        row for row in feature_rows
        if row.get("train_q75") is not None
        and row.get("verdict") != "LOW_VARIANCE_OR_INSUFFICIENT_DATA"
        and row.get("feature") in frame.columns
    ]
    eligible = eligible[:8]
    rows: List[Dict[str, Any]] = []

    for left, right in itertools.combinations(eligible, 2):
        conditions = [
            (str(left["feature"]), float(left["train_q75"])),
            (str(right["feature"]), float(right["train_q75"])),
        ]
        metrics = {split: _condition_metric(_filter_split(frame, split), conditions) for split in SPLITS}
        train_m, val_m, test_m = metrics["TRAIN_60"], metrics["VALIDATION_20"], metrics["TEST_20"]
        if test_m.samples < 50 or val_m.samples < 50:
            verdict = "LOW_OUT_OF_SAMPLE_INTERACTION"
        elif (
            train_m.avg_net_return_pct > 0
            and val_m.avg_net_return_pct > 0
            and test_m.avg_net_return_pct > 0
            and val_m.profit_factor > 1.0
            and test_m.profit_factor > 1.0
        ):
            verdict = "FORWARD_SHADOW_INTERACTION_CANDIDATE"
        elif train_m.avg_net_return_pct > 0 and test_m.avg_net_return_pct <= 0:
            verdict = "OVERFIT_INTERACTION"
        elif test_m.avg_net_return_pct <= 0:
            verdict = "REJECT_TEST_NET_NON_POSITIVE"
        else:
            verdict = "RESEARCH_ONLY_UNSTABLE_INTERACTION"

        stability = min(train_m.avg_net_return_pct, val_m.avg_net_return_pct, test_m.avg_net_return_pct)
        rows.append({
            "interaction": f"{left['feature']}>={left['train_q75']} & {right['feature']}>={right['train_q75']}",
            "feature_1": left["feature"],
            "feature_1_threshold": left["train_q75"],
            "feature_2": right["feature"],
            "feature_2_threshold": right["train_q75"],
            "train_samples": train_m.samples,
            "train_avg_net_pct": train_m.avg_net_return_pct,
            "train_profit_factor": train_m.profit_factor,
            "validation_samples": val_m.samples,
            "validation_avg_net_pct": val_m.avg_net_return_pct,
            "validation_profit_factor": val_m.profit_factor,
            "test_samples": test_m.samples,
            "test_win_rate_pct": test_m.win_rate_pct,
            "test_avg_net_pct": test_m.avg_net_return_pct,
            "test_profit_factor": test_m.profit_factor,
            "robustness_floor_pct": round(stability, 6),
            "verdict": verdict,
        })

    rows.sort(
        key=lambda item: (
            item["verdict"] == "FORWARD_SHADOW_INTERACTION_CANDIDATE",
            item["test_avg_net_pct"],
            item["test_samples"],
        ),
        reverse=True,
    )
    return rows


def _segment_analysis(frame: pd.DataFrame) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    dimensions = [
        ("symbol", "SYMBOL"),
        ("regime_label", "REGIME"),
        ("normalized_side", "SIDE"),
    ]
    for column, dimension in dimensions:
        if column not in frame.columns:
            continue
        for value in sorted(frame[column].dropna().astype(str).unique()):
            item: Dict[str, Any] = {"dimension": dimension, "value": value}
            for split in ("ALL", "VALIDATION_20", "TEST_20"):
                part = _filter_split(frame, split)
                part = part[part[column].astype(str) == value]
                metric = _metric(part)
                prefix = split.lower()
                item[f"{prefix}_samples"] = metric.samples
                item[f"{prefix}_win_rate_pct"] = metric.win_rate_pct
                item[f"{prefix}_avg_net_pct"] = metric.avg_net_return_pct
                item[f"{prefix}_profit_factor"] = metric.profit_factor
            if item.get("test_20_samples", 0) < 50:
                verdict = "LOW_TEST_SAMPLE"
            elif item.get("validation_20_avg_net_pct", 0.0) > 0 and item.get("test_20_avg_net_pct", 0.0) > 0:
                verdict = "STABLE_POSITIVE_SEGMENT_RESEARCH"
            elif item.get("test_20_avg_net_pct", 0.0) <= 0:
                verdict = "NEGATIVE_TEST_SEGMENT"
            else:
                verdict = "UNSTABLE_SEGMENT"
            item["verdict"] = verdict
            rows.append(item)
    rows.sort(key=lambda item: (item.get("test_20_avg_net_pct", -999.0), item.get("test_20_samples", 0)), reverse=True)
    return rows


def _recommendations(score_calibration: Dict[str, Any], features: List[Dict[str, Any]], interactions: List[Dict[str, Any]], segments: List[Dict[str, Any]]) -> List[str]:
    recommendations: List[str] = []
    if score_calibration.get("verdict") == "SCORE_INVERTED_OR_MISCALIBRATED":
        recommendations.append("Score نهایی در Test monotonic نیست؛ بالا بردن Threshold به‌تنهایی ممنوع و وزن‌ها باید فقط در Shadow بازطراحی شوند.")
    inverse = [row for row in features if row.get("verdict") == "STABLE_INVERSE_ASSOCIATION"]
    positive = [row for row in features if row.get("verdict") == "STABLE_POSITIVE_ASSOCIATION"]
    if inverse:
        recommendations.append("Featureهای با رابطه معکوس پایدار برای کاهش وزن/بازتعریف در Candidate Config بررسی شوند: " + ", ".join(row["feature"] for row in inverse[:4]))
    if positive:
        recommendations.append("Featureهای مثبت پایدار فقط به‌عنوان Shadow Gate کاندید شوند: " + ", ".join(row["feature"] for row in positive[:4]))
    candidates = [row for row in interactions if row.get("verdict") == "FORWARD_SHADOW_INTERACTION_CANDIDATE"]
    if candidates:
        recommendations.append("Interactionهای پایدار پیدا شد؛ پارامترها را ثابت نگه دار و فقط Forward Shadow اجرا کن.")
    else:
        recommendations.append("هیچ Interaction مقاوم در Validation/Test پیدا نشد؛ Decision Engine فعلی بدون تغییر بماند و Paper/Live ارتقا نگیرد.")
    stable_segments = [row for row in segments if row.get("verdict") == "STABLE_POSITIVE_SEGMENT_RESEARCH"]
    if stable_segments:
        recommendations.append("Segmentهای مثبت پایدار برای تحلیل جداگانه وجود دارند: " + ", ".join(f"{row['dimension']}={row['value']}" for row in stable_segments[:4]))
    recommendations.append("هر تغییر وزن باید با Config جدا، Replay مجدد، Validation/Test قفل‌شده و سپس Forward Shadow تأیید شود.")
    return recommendations


def run_replay_score_calibration(
    path: str | Path = DEFAULT_FILE,
) -> Dict[str, Any]:
    input_path = Path(path)
    if not input_path.exists():
        return {
            "version": VERSION,
            "run_id": "replay_score_calibration_missing",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "status": "SCORE_CALIBRATION_BLOCKED",
            "input_file": str(input_path),
            "rows_total": 0,
            "rows_analyzed": 0,
            "score_calibration": {},
            "score_bands": [],
            "feature_attribution": [],
            "interactions": [],
            "segments": [],
            "forward_shadow_candidates": [],
            "blockers": [f"Replay evaluations file does not exist: {input_path}"],
            "warnings": ["Score Calibration is research-only and never changes strategy settings."],
            "recommendations": [],
        }

    raw = pd.read_csv(input_path, encoding="utf-8-sig")
    frame, schema_info, blockers, warnings = _prepare(raw)
    score_bands: List[Dict[str, Any]] = []
    score_calibration: Dict[str, Any] = {}
    feature_rows: List[Dict[str, Any]] = []
    interactions: List[Dict[str, Any]] = []
    segments: List[Dict[str, Any]] = []

    if not blockers:
        score_bands, score_calibration = _band_analysis(frame)
        feature_rows = _feature_analysis(frame)
        interactions = _interaction_analysis(frame, feature_rows)
        segments = _segment_analysis(frame)

    candidates = [row for row in interactions if row.get("verdict") == "FORWARD_SHADOW_INTERACTION_CANDIDATE"]
    if blockers:
        status = "SCORE_CALIBRATION_BLOCKED"
    elif candidates:
        status = "SCORE_CALIBRATION_WITH_SHADOW_CANDIDATES"
    elif score_calibration.get("verdict") == "SCORE_INVERTED_OR_MISCALIBRATED":
        status = "SCORE_MISCALIBRATED_NO_ROBUST_CANDIDATE"
    else:
        status = "SCORE_CALIBRATION_RESEARCH_ONLY"

    recommendations = _recommendations(score_calibration, feature_rows, interactions, segments) if not blockers else []
    warnings.extend([
        "Feature attribution measures association, not causal importance.",
        "No calibration result is permission for Paper or Live trading.",
        "Interaction thresholds are learned only from TRAIN and applied unchanged to Validation/Test.",
    ])

    return {
        "version": VERSION,
        "run_id": "replay_score_calibration_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "input_file": str(input_path),
        "rows_total": int(len(raw)),
        "rows_analyzed": int(len(frame)),
        "schema": schema_info,
        "score_calibration": score_calibration,
        "score_bands": score_bands,
        "feature_attribution": feature_rows,
        "interactions": interactions,
        "segments": segments,
        "forward_shadow_candidates": candidates,
        "blockers": blockers,
        "warnings": warnings,
        "recommendations": recommendations,
    }


def format_replay_score_calibration_console(report: Dict[str, Any], compact: bool = True) -> str:
    sep = "=" * 122
    lines = [sep, f"🧬 Freakto Score Calibration & Feature Attribution Lab {VERSION}", sep]
    lines.append(f"Status                 : {report.get('status')}")
    lines.append(f"Run ID                 : {report.get('run_id')}")
    lines.append(f"Rows Total / Analyzed  : {report.get('rows_total')} / {report.get('rows_analyzed')}")
    score = report.get("score_calibration", {})
    lines.append(f"Score Verdict          : {score.get('verdict', 'UNKNOWN')}")
    test = score.get("splits", {}).get("TEST_20", {})
    lines.append(f"Test Monotonicity      : {test.get('band_monotonicity_spearman', 0.0)}")
    lines.append(f"Test Band Violations   : {test.get('adjacent_band_violations', 0)}")
    lines.append(f"High-Low Test Net      : {test.get('high_minus_low_avg_net_pct', 0.0)}%")
    lines.append(f"Shadow Candidates      : {len(report.get('forward_shadow_candidates', []))}")

    if report.get("score_bands"):
        lines.append("\nTest Score Bands:")
        for row in report["score_bands"]:
            if row.get("split") == "TEST_20" and row.get("samples", 0) > 0:
                lines.append(
                    f"- {row['score_band']}: n={row['samples']} win={row['win_rate_pct']}% "
                    f"net={row['avg_net_return_pct']}% PF={row['profit_factor']}"
                )

    if report.get("feature_attribution"):
        lines.append("\nFeature Attribution:")
        for row in report["feature_attribution"][:8]:
            lines.append(
                f"- {row.get('feature')}: test_corr={row.get('test_20_correlation', 0.0)} "
                f"test_Q4-Q1={row.get('test_20_high_minus_low_pct', 0.0)}% | {row.get('verdict')}"
            )

    if report.get("interactions"):
        lines.append("\nTop Feature Interactions:")
        for row in report["interactions"][:8]:
            lines.append(
                f"- {row.get('interaction')}: test_n={row.get('test_samples')} "
                f"test_net={row.get('test_avg_net_pct')}% PF={row.get('test_profit_factor')} | {row.get('verdict')}"
            )

    if report.get("segments"):
        lines.append("\nBest Test Segments:")
        for row in report["segments"][:6]:
            lines.append(
                f"- {row.get('dimension')}={row.get('value')}: n={row.get('test_20_samples')} "
                f"net={row.get('test_20_avg_net_pct')}% PF={row.get('test_20_profit_factor')} | {row.get('verdict')}"
            )

    if report.get("blockers"):
        lines.append("\nBlockers:")
        lines.extend(f"⛔ {item}" for item in report["blockers"])
    if report.get("recommendations"):
        lines.append("\nRecommendations:")
        lines.extend(f"→ {item}" for item in report["recommendations"])
    lines.append("\nWarnings:")
    lines.extend(f"⚠️ {item}" for item in report.get("warnings", []))
    lines.append(sep)
    return "\n".join(lines)


def _markdown_table(rows: List[Dict[str, Any]], columns: Sequence[str], limit: int = 30) -> str:
    if not rows:
        return "_No rows._"
    header = "| " + " | ".join(columns) + " |"
    separator = "|" + "|".join("---" for _ in columns) + "|"
    body = []
    for row in rows[:limit]:
        body.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join([header, separator, *body])


def format_replay_score_calibration_markdown(report: Dict[str, Any]) -> str:
    lines = [
        f"# Freakto Score Calibration & Feature Attribution {VERSION}",
        "",
        f"- Status: **{report.get('status')}**",
        f"- Rows analyzed: **{report.get('rows_analyzed')}**",
        f"- Score verdict: **{report.get('score_calibration', {}).get('verdict', 'UNKNOWN')}**",
        f"- Forward Shadow candidates: **{len(report.get('forward_shadow_candidates', []))}**",
        "",
        "## Test Score Bands",
        "",
        _markdown_table(
            [row for row in report.get("score_bands", []) if row.get("split") == "TEST_20" and row.get("samples", 0) > 0],
            ["score_band", "samples", "win_rate_pct", "avg_net_return_pct", "profit_factor"],
        ),
        "",
        "## Feature Attribution",
        "",
        _markdown_table(
            report.get("feature_attribution", []),
            ["feature", "train_q25", "train_q75", "validation_20_high_minus_low_pct", "test_20_high_minus_low_pct", "test_20_correlation", "verdict"],
        ),
        "",
        "## Feature Interactions",
        "",
        _markdown_table(
            report.get("interactions", []),
            ["interaction", "validation_samples", "validation_avg_net_pct", "test_samples", "test_avg_net_pct", "test_profit_factor", "verdict"],
        ),
        "",
        "## Recommendations",
        "",
    ]
    lines.extend(f"- {item}" for item in report.get("recommendations", []))
    lines.extend(["", "## Safety", "", "Research-only. No strategy settings, Paper orders or Live orders are changed."])
    return "\n".join(lines)


def save_replay_score_calibration(report: Dict[str, Any], output_dir: str | Path = OUTPUT_DIR) -> CalibrationSavePaths:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    run_id = str(report.get("run_id") or "replay_score_calibration")
    json_path = directory / f"{run_id}.json"
    report_path = directory / f"{run_id}_report.md"
    score_bands_csv = directory / f"{run_id}_score_bands.csv"
    feature_csv = directory / f"{run_id}_feature_attribution.csv"
    interactions_csv = directory / f"{run_id}_interactions.csv"
    segments_csv = directory / f"{run_id}_segments.csv"
    observations_csv = directory / "replay_score_calibration_observations.csv"

    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    report_path.write_text(format_replay_score_calibration_markdown(report), encoding="utf-8")
    pd.DataFrame(report.get("score_bands", [])).to_csv(score_bands_csv, index=False, encoding="utf-8-sig")
    pd.DataFrame(report.get("feature_attribution", [])).to_csv(feature_csv, index=False, encoding="utf-8-sig")
    pd.DataFrame(report.get("interactions", [])).to_csv(interactions_csv, index=False, encoding="utf-8-sig")
    pd.DataFrame(report.get("segments", [])).to_csv(segments_csv, index=False, encoding="utf-8-sig")

    observation = {
        "generated_utc": report.get("generated_utc"),
        "run_id": report.get("run_id"),
        "status": report.get("status"),
        "rows_analyzed": report.get("rows_analyzed"),
        "score_verdict": report.get("score_calibration", {}).get("verdict"),
        "test_monotonicity": report.get("score_calibration", {}).get("splits", {}).get("TEST_20", {}).get("band_monotonicity_spearman"),
        "test_high_minus_low_net_pct": report.get("score_calibration", {}).get("splits", {}).get("TEST_20", {}).get("high_minus_low_avg_net_pct"),
        "shadow_candidates": len(report.get("forward_shadow_candidates", [])),
    }
    obs_frame = pd.DataFrame([observation])
    obs_frame.to_csv(observations_csv, mode="a", header=not observations_csv.exists(), index=False, encoding="utf-8-sig")

    return CalibrationSavePaths(
        json_path=str(json_path),
        report_path=str(report_path),
        score_bands_csv=str(score_bands_csv),
        feature_attribution_csv=str(feature_csv),
        interactions_csv=str(interactions_csv),
        segments_csv=str(segments_csv),
        observations_csv=str(observations_csv),
    )
