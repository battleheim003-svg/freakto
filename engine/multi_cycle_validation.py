"""Cross-cycle replay validation, drift diagnostics and regime stability.

The validator is intentionally descriptive. It never tunes thresholds, mutates
runtime weights, promotes a model, or enables Paper/Live trading.
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

VERSION = "2.0.0"
DEFAULT_OUTPUT_DIR = Path("logs") / "multi_cycle_archive_v2"
RETURN_CANDIDATES = (
    "net_signed_return_after_6c_pct",
    "net_return_pct",
    "net_return_after_24h_pct",
    "net_signed_return_after_12c_pct",
)
TIMESTAMP_CANDIDATES = ("candle_timestamp", "timestamp_utc", "timestamp", "feature_cutoff_timestamp")


@dataclass(frozen=True)
class ReturnMetrics:
    sample_count: int
    win_count: int
    loss_count: int
    win_rate: float
    expectancy: float
    median_return: float
    profit_factor: float
    total_return: float
    max_drawdown: float


@dataclass
class MultiCycleValidationConfig:
    output_dir: str = str(DEFAULT_OUTPUT_DIR)
    fixed_score_threshold: float = 70.0
    rolling_window_days: int = 365
    rolling_step_days: int = 180
    expanding_min_train_days: int = 730
    expanding_test_days: int = 180
    min_window_samples: int = 50
    psi_bins: int = 10
    drift_features: List[str] = field(
        default_factory=lambda: ["score", "atr_pct", "rsi_14", "trend_score", "momentum_score", "volume_score", "structure_score"]
    )


@dataclass
class MultiCycleValidationReport:
    status: str
    mode: str
    version: str
    fixed_score_threshold: float
    by_window: List[Dict[str, Any]]
    rolling_windows: List[Dict[str, Any]]
    expanding_windows: List[Dict[str, Any]]
    drift: List[Dict[str, Any]]
    regime_stability: List[Dict[str, Any]]
    blockers: List[str]
    warnings: List[str]
    promotion_applied: bool = False
    paper_live_enabled: bool = False


def _timestamp_column(frame: pd.DataFrame) -> str:
    for column in TIMESTAMP_CANDIDATES:
        if column in frame.columns:
            return column
    raise ValueError("Replay rows do not contain a supported timestamp column")


def _return_column(frame: pd.DataFrame) -> str:
    for column in RETURN_CANDIDATES:
        if column in frame.columns:
            return column
    raise ValueError("Replay rows do not contain a supported net-return column")


def normalize_replay_rows(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    work = frame.copy()
    ts_col = _timestamp_column(work)
    ret_col = _return_column(work)
    work["__timestamp"] = pd.to_datetime(work[ts_col], utc=True, errors="coerce")
    work["__return"] = pd.to_numeric(work[ret_col], errors="coerce")
    if "score" not in work.columns:
        work["score"] = np.nan
    work["score"] = pd.to_numeric(work["score"], errors="coerce")
    if "side" not in work.columns:
        work["side"] = "NEUTRAL"
    work["side"] = work["side"].astype(str).str.upper()
    if "regime" not in work.columns:
        work["regime"] = "UNKNOWN"
    work["regime"] = work["regime"].fillna("UNKNOWN").astype(str).str.upper()
    return work.dropna(subset=["__timestamp", "__return"]).sort_values("__timestamp").reset_index(drop=True)


def max_drawdown(returns: Sequence[float]) -> float:
    if not returns:
        return 0.0
    equity = np.cumsum(np.asarray(returns, dtype=float))
    peaks = np.maximum.accumulate(np.r_[0.0, equity])
    drawdowns = np.r_[0.0, equity] - peaks
    return float(drawdowns.min())


def return_metrics(frame: pd.DataFrame) -> ReturnMetrics:
    if frame is None or frame.empty:
        return ReturnMetrics(0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    work = normalize_replay_rows(frame) if "__return" not in frame.columns else frame.copy()
    values = pd.to_numeric(work["__return"], errors="coerce").dropna().astype(float)
    if values.empty:
        return ReturnMetrics(0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    wins = values[values > 0]
    losses = values[values <= 0]
    gross_profit = float(wins.sum())
    gross_loss = abs(float(losses.sum()))
    pf = gross_profit / gross_loss if gross_loss > 0 else float("inf") if gross_profit > 0 else 0.0
    return ReturnMetrics(
        sample_count=int(len(values)),
        win_count=int((values > 0).sum()),
        loss_count=int((values <= 0).sum()),
        win_rate=float((values > 0).mean()),
        expectancy=float(values.mean()),
        median_return=float(values.median()),
        profit_factor=float(pf),
        total_return=float(values.sum()),
        max_drawdown=max_drawdown(values.tolist()),
    )


def metric_payload(metrics: ReturnMetrics) -> Dict[str, Any]:
    payload = asdict(metrics)
    if math.isinf(payload["profit_factor"]):
        payload["profit_factor"] = "inf"
    return payload


def fixed_gate(frame: pd.DataFrame, threshold: float) -> pd.DataFrame:
    work = normalize_replay_rows(frame)
    if work.empty:
        return work
    return work[
        work["side"].isin(["LONG", "SHORT"])
        & work["score"].ge(float(threshold))
    ].copy()


def rolling_validation(
    frame: pd.DataFrame,
    *,
    window_days: int = 365,
    step_days: int = 180,
    min_samples: int = 50,
    label: str = "",
) -> List[Dict[str, Any]]:
    work = normalize_replay_rows(frame)
    if work.empty:
        return []
    start = work["__timestamp"].min().floor("D")
    end = work["__timestamp"].max()
    records: List[Dict[str, Any]] = []
    cursor = start
    while cursor <= end:
        window_end = cursor + pd.Timedelta(days=max(1, int(window_days)))
        chunk = work[(work["__timestamp"] >= cursor) & (work["__timestamp"] < window_end)]
        metrics = return_metrics(chunk)
        if metrics.sample_count >= max(1, int(min_samples)):
            records.append(
                {
                    "window": label,
                    "start_utc": cursor.isoformat(),
                    "end_utc": window_end.isoformat(),
                    **metric_payload(metrics),
                }
            )
        cursor += pd.Timedelta(days=max(1, int(step_days)))
    return records


def expanding_validation(
    frame: pd.DataFrame,
    *,
    min_train_days: int = 730,
    test_days: int = 180,
    min_samples: int = 50,
    label: str = "",
) -> List[Dict[str, Any]]:
    work = normalize_replay_rows(frame)
    if work.empty:
        return []
    origin = work["__timestamp"].min().floor("D")
    final = work["__timestamp"].max()
    split = origin + pd.Timedelta(days=max(1, int(min_train_days)))
    records: List[Dict[str, Any]] = []
    while split < final:
        test_end = split + pd.Timedelta(days=max(1, int(test_days)))
        train = work[(work["__timestamp"] >= origin) & (work["__timestamp"] < split)]
        test = work[(work["__timestamp"] >= split) & (work["__timestamp"] < test_end)]
        train_metrics = return_metrics(train)
        test_metrics = return_metrics(test)
        if train_metrics.sample_count >= min_samples and test_metrics.sample_count >= min_samples:
            records.append(
                {
                    "window": label,
                    "train_start_utc": origin.isoformat(),
                    "train_end_utc": split.isoformat(),
                    "test_start_utc": split.isoformat(),
                    "test_end_utc": test_end.isoformat(),
                    "train": metric_payload(train_metrics),
                    "test": metric_payload(test_metrics),
                    "no_overlap": bool(train["__timestamp"].max() < test["__timestamp"].min()),
                }
            )
        split = test_end
    return records


def population_stability_index(reference: Sequence[float], current: Sequence[float], bins: int = 10) -> float:
    ref = pd.Series(reference, dtype=float).replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
    cur = pd.Series(current, dtype=float).replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
    if len(ref) < 2 or len(cur) < 2:
        return 0.0
    quantiles = np.linspace(0, 1, max(2, int(bins)) + 1)
    edges = np.unique(np.quantile(ref, quantiles))
    if len(edges) < 3:
        low = min(float(ref.min()), float(cur.min()))
        high = max(float(ref.max()), float(cur.max()))
        if low == high:
            return 0.0
        edges = np.linspace(low, high, max(2, int(bins)) + 1)
    edges[0] = -np.inf
    edges[-1] = np.inf
    ref_hist, _ = np.histogram(ref, bins=edges)
    cur_hist, _ = np.histogram(cur, bins=edges)
    eps = 1e-6
    ref_pct = np.maximum(ref_hist / max(1, ref_hist.sum()), eps)
    cur_pct = np.maximum(cur_hist / max(1, cur_hist.sum()), eps)
    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def categorical_l1(reference: pd.Series, current: pd.Series) -> float:
    ref = reference.fillna("UNKNOWN").astype(str).value_counts(normalize=True)
    cur = current.fillna("UNKNOWN").astype(str).value_counts(normalize=True)
    keys = sorted(set(ref.index) | set(cur.index))
    return float(sum(abs(float(ref.get(key, 0.0)) - float(cur.get(key, 0.0))) for key in keys))


def drift_diagnostics(
    frame: pd.DataFrame,
    *,
    features: Sequence[str],
    recent_days: int = 365,
    psi_bins: int = 10,
    label: str = "",
) -> List[Dict[str, Any]]:
    work = normalize_replay_rows(frame)
    if work.empty:
        return []
    cutoff = work["__timestamp"].max() - pd.Timedelta(days=max(1, int(recent_days)))
    reference = work[work["__timestamp"] < cutoff]
    recent = work[work["__timestamp"] >= cutoff]
    if reference.empty or recent.empty:
        return []
    records: List[Dict[str, Any]] = []
    ref_metrics = return_metrics(reference)
    recent_metrics = return_metrics(recent)
    records.append(
        {
            "window": label,
            "feature": "OUTCOME",
            "reference_rows": int(len(reference)),
            "recent_rows": int(len(recent)),
            "psi": None,
            "reference_mean": ref_metrics.expectancy,
            "recent_mean": recent_metrics.expectancy,
            "mean_delta": recent_metrics.expectancy - ref_metrics.expectancy,
            "win_rate_delta": recent_metrics.win_rate - ref_metrics.win_rate,
        }
    )
    for feature in features:
        if feature not in work.columns:
            continue
        ref_values = pd.to_numeric(reference[feature], errors="coerce").dropna()
        recent_values = pd.to_numeric(recent[feature], errors="coerce").dropna()
        if len(ref_values) < 2 or len(recent_values) < 2:
            continue
        records.append(
            {
                "window": label,
                "feature": feature,
                "reference_rows": int(len(ref_values)),
                "recent_rows": int(len(recent_values)),
                "psi": population_stability_index(ref_values, recent_values, bins=psi_bins),
                "reference_mean": float(ref_values.mean()),
                "recent_mean": float(recent_values.mean()),
                "mean_delta": float(recent_values.mean() - ref_values.mean()),
                "win_rate_delta": None,
            }
        )
    for feature in ("side", "regime", "symbol"):
        if feature in work.columns:
            records.append(
                {
                    "window": label,
                    "feature": f"{feature.upper()}_DISTRIBUTION",
                    "reference_rows": int(len(reference)),
                    "recent_rows": int(len(recent)),
                    "psi": None,
                    "reference_mean": None,
                    "recent_mean": None,
                    "mean_delta": categorical_l1(reference[feature], recent[feature]),
                    "win_rate_delta": None,
                }
            )
    return records


def regime_stability(frames: Mapping[str, pd.DataFrame], min_samples: int = 30) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for window, frame in frames.items():
        work = normalize_replay_rows(frame)
        if work.empty or "regime" not in work.columns:
            continue
        for regime, group in work.groupby("regime", dropna=False):
            metrics = return_metrics(group)
            if metrics.sample_count < max(1, int(min_samples)):
                continue
            records.append({"window": window, "regime": str(regime), **metric_payload(metrics)})
    # Add an across-window consistency count for each regime.
    by_regime: Dict[str, List[Dict[str, Any]]] = {}
    for row in records:
        by_regime.setdefault(str(row["regime"]), []).append(row)
    for regime, rows in by_regime.items():
        records.append(
            {
                "window": "ALL_WINDOWS",
                "regime": regime,
                "sample_count": int(sum(int(row["sample_count"]) for row in rows)),
                "win_count": int(sum(int(row["win_count"]) for row in rows)),
                "loss_count": int(sum(int(row["loss_count"]) for row in rows)),
                "win_rate": float(np.mean([float(row["win_rate"]) for row in rows])),
                "expectancy": float(np.mean([float(row["expectancy"]) for row in rows])),
                "median_return": float(np.mean([float(row["median_return"]) for row in rows])),
                "profit_factor": float(np.mean([float(row["profit_factor"]) for row in rows if row["profit_factor"] != "inf"]))
                if any(row["profit_factor"] != "inf" for row in rows)
                else "inf",
                "total_return": float(sum(float(row["total_return"]) for row in rows)),
                "max_drawdown": float(min(float(row["max_drawdown"]) for row in rows)),
                "positive_windows": int(sum(float(row["expectancy"]) > 0 for row in rows)),
                "total_windows": int(len(rows)),
            }
        )
    return records


def load_replay_files(output_dir: str | Path) -> Dict[str, pd.DataFrame]:
    root = Path(output_dir) / "replays"
    frames: Dict[str, pd.DataFrame] = {}
    for path in sorted(root.glob("*_replay.csv.gz")):
        name = path.name.replace("_replay.csv.gz", "").upper()
        try:
            frames[name] = pd.read_csv(path, compression="gzip", low_memory=False)
        except Exception:
            continue
    return frames


def run_multi_cycle_validation(
    frames: Mapping[str, pd.DataFrame],
    config: MultiCycleValidationConfig,
) -> MultiCycleValidationReport:
    blockers: List[str] = []
    warnings: List[str] = []
    by_window: List[Dict[str, Any]] = []
    rolling: List[Dict[str, Any]] = []
    expanding: List[Dict[str, Any]] = []
    drift: List[Dict[str, Any]] = []

    if not frames:
        warnings.append("No multi-cycle replay files are available yet.")
    for window, raw in frames.items():
        try:
            work = normalize_replay_rows(raw)
        except Exception as exc:
            blockers.append(f"{window}: invalid replay schema: {type(exc).__name__}: {exc}")
            continue
        directional = work[work["side"].isin(["LONG", "SHORT"])]
        gate = fixed_gate(work, config.fixed_score_threshold)
        by_window.append(
            {
                "window": window,
                "all_directional": metric_payload(return_metrics(directional)),
                "fixed_gate": metric_payload(return_metrics(gate)),
                "first_timestamp_utc": work["__timestamp"].min().isoformat() if len(work) else "",
                "last_timestamp_utc": work["__timestamp"].max().isoformat() if len(work) else "",
            }
        )
        rolling.extend(
            rolling_validation(
                directional,
                window_days=config.rolling_window_days,
                step_days=config.rolling_step_days,
                min_samples=config.min_window_samples,
                label=window,
            )
        )
        expanding.extend(
            expanding_validation(
                directional,
                min_train_days=config.expanding_min_train_days,
                test_days=config.expanding_test_days,
                min_samples=config.min_window_samples,
                label=window,
            )
        )
        drift.extend(
            drift_diagnostics(
                directional,
                features=config.drift_features,
                psi_bins=config.psi_bins,
                label=window,
            )
        )

    regimes = regime_stability(frames, min_samples=max(30, config.min_window_samples // 2))
    if blockers:
        status = "FAIL_CLOSED"
    elif not frames:
        status = "READY_AWAITING_REPLAYS"
    else:
        status = "COMPLETE_NO_PROMOTION"

    report = MultiCycleValidationReport(
        status=status,
        mode="FIXED_BENCHMARK_MULTI_CYCLE_AUDIT_ONLY",
        version=VERSION,
        fixed_score_threshold=float(config.fixed_score_threshold),
        by_window=by_window,
        rolling_windows=rolling,
        expanding_windows=expanding,
        drift=drift,
        regime_stability=regimes,
        blockers=blockers,
        warnings=warnings,
        promotion_applied=False,
        paper_live_enabled=False,
    )
    output = Path(config.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "multi_cycle_validation_report.json").write_text(
        json.dumps(asdict(report), ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    pd.DataFrame(by_window).to_json(output / "multi_cycle_window_summary.json", orient="records", indent=2)
    pd.DataFrame(rolling).to_csv(output / "rolling_validation.csv", index=False, encoding="utf-8-sig")
    # Flatten expanding nested dictionaries for a useful CSV.
    expanding_rows: List[Dict[str, Any]] = []
    for row in expanding:
        flat = {key: value for key, value in row.items() if key not in {"train", "test"}}
        flat.update({f"train_{key}": value for key, value in row.get("train", {}).items()})
        flat.update({f"test_{key}": value for key, value in row.get("test", {}).items()})
        expanding_rows.append(flat)
    pd.DataFrame(expanding_rows).to_csv(output / "expanding_validation.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(drift).to_csv(output / "drift_diagnostics.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(regimes).to_csv(output / "regime_stability.csv", index=False, encoding="utf-8-sig")
    return report
