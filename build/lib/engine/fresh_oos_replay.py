"""Fresh out-of-sample replay orchestration and fixed-benchmark audit."""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from engine.fresh_oos_feature_store import (
    DEFAULT_FREEZE_DIR,
    DEFAULT_OUTPUT_DIR,
    CostProfileRegistry,
    DevelopmentFreezeManifest,
    build_feature_store_v2,
    freeze_development_dataset,
    load_freeze_manifest,
    strictly_fresh_rows,
)

VERSION = "2.0.0"
FIXED_SCORE_THRESHOLD = 70.0


@dataclass
class FreshOOSConfig:
    development_replay_csv: str = str(Path("logs") / "market_replay" / "market_replay_evaluations.csv")
    output_dir: str = str(DEFAULT_OUTPUT_DIR)
    symbols: List[str] = field(default_factory=lambda: ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
    timeframes: List[str] = field(default_factory=lambda: ["4h"])
    data_dir: str = str(Path("data") / "market_replay")
    max_path_candles: int = 24
    min_fresh_directional_rows: int = 300
    min_rows_per_symbol: int = 50
    min_positive_time_folds: int = 3
    fixed_score_threshold: float = FIXED_SCORE_THRESHOLD
    cost_profile_file: str = ""
    run_replay: bool = False
    force_refreeze: bool = False
    strict_no_overlap: bool = True


@dataclass(frozen=True)
class FixedBenchmarkMetrics:
    sample_count: int
    win_count: int
    loss_count: int
    win_rate: float
    expectancy: float
    median_return: float
    profit_factor: float
    total_return: float
    max_drawdown: float
    positive_time_folds: int
    total_time_folds: int


@dataclass
class FreshOOSReport:
    status: str
    mode: str
    development_dataset_id: str
    development_cutoff_utc: str
    source_replay_rows: int
    fresh_rows: int
    fresh_directional_rows: int
    fixed_threshold: float
    all_directional: Dict[str, Any]
    fixed_gate: Dict[str, Any]
    by_symbol: List[Dict[str, Any]]
    by_side: List[Dict[str, Any]]
    by_regime: List[Dict[str, Any]]
    coverage: Dict[str, Any]
    blockers: List[str]
    warnings: List[str]
    feature_store: Dict[str, Any]
    promotion_applied: bool = False
    paper_live_enabled: bool = False


def _finite_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()


def _max_drawdown(returns: Sequence[float]) -> float:
    if not returns:
        return 0.0
    equity = np.cumsum(np.asarray(returns, dtype=float))
    peaks = np.maximum.accumulate(np.r_[0.0, equity])
    drawdowns = np.r_[0.0, equity] - peaks
    return float(drawdowns.min())


def fixed_metrics(frame: pd.DataFrame, *, return_column: str = "net_return_pct", folds: int = 4) -> FixedBenchmarkMetrics:
    if frame is None or frame.empty or return_column not in frame.columns:
        return FixedBenchmarkMetrics(0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, folds)
    work = frame.copy()
    values = pd.to_numeric(work[return_column], errors="coerce")
    work = work.loc[values.notna()].copy()
    values = values.loc[values.notna()].astype(float)
    if values.empty:
        return FixedBenchmarkMetrics(0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, folds)
    wins = values[values > 0]
    losses = values[values <= 0]
    gross_profit = float(wins.sum())
    gross_loss = abs(float(losses.sum()))
    pf = gross_profit / gross_loss if gross_loss > 0 else float("inf") if gross_profit > 0 else 0.0
    ts_col = next((c for c in ("candle_timestamp", "feature_cutoff_timestamp", "timestamp_utc", "timestamp") if c in work.columns), "")
    if ts_col:
        work["__ts"] = pd.to_datetime(work[ts_col], utc=True, errors="coerce")
        work["__ret"] = values.values
        work = work.sort_values("__ts")
        chunks = [work.iloc[indexes] for indexes in np.array_split(np.arange(len(work)), folds) if len(indexes)]
        positive = sum(float(chunk["__ret"].mean()) > 0 for chunk in chunks)
        total_folds = len(chunks)
        ordered_returns = work["__ret"].astype(float).tolist()
    else:
        chunks = [values.iloc[indexes] for indexes in np.array_split(np.arange(len(values)), folds) if len(indexes)]
        positive = sum(float(chunk.mean()) > 0 for chunk in chunks)
        total_folds = len(chunks)
        ordered_returns = values.tolist()
    return FixedBenchmarkMetrics(
        sample_count=int(len(values)),
        win_count=int((values > 0).sum()),
        loss_count=int((values <= 0).sum()),
        win_rate=float((values > 0).mean()),
        expectancy=float(values.mean()),
        median_return=float(values.median()),
        profit_factor=float(pf),
        total_return=float(values.sum()),
        max_drawdown=_max_drawdown(ordered_returns),
        positive_time_folds=int(positive),
        total_time_folds=int(total_folds),
    )


def _metric_dict(metrics: FixedBenchmarkMetrics) -> Dict[str, Any]:
    payload = asdict(metrics)
    if math.isinf(payload["profit_factor"]):
        payload["profit_factor"] = "inf"
    return payload


def _timestamp_column(frame: pd.DataFrame) -> str:
    for column in ("candle_timestamp", "feature_cutoff_timestamp", "timestamp_utc", "timestamp"):
        if column in frame.columns:
            return column
    raise ValueError("no timestamp column")


def _normalize_replay(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    if "net_return_pct" not in work.columns:
        candidates = [c for c in ("net_signed_return_after_6c_pct", "net_return_after_24h_pct") if c in work.columns]
        if candidates:
            work["net_return_pct"] = work[candidates[0]]
    if "score" not in work.columns:
        work["score"] = np.nan
    if "side" not in work.columns:
        work["side"] = "NEUTRAL"
    ts_col = _timestamp_column(work)
    work[ts_col] = pd.to_datetime(work[ts_col], utc=True, errors="coerce")
    return work.dropna(subset=[ts_col]).sort_values(ts_col).reset_index(drop=True)


def _coverage(frame: pd.DataFrame, config: FreshOOSConfig) -> Dict[str, Any]:
    directional = frame[frame.get("side", pd.Series(dtype=str)).astype(str).isin(["LONG", "SHORT"])].copy()
    symbol_counts = directional.get("symbol", pd.Series(dtype=str)).astype(str).value_counts().to_dict()
    timeframe_counts = directional.get("timeframe", pd.Series(dtype=str)).astype(str).value_counts().to_dict()
    provider_counts = directional.get("provider", pd.Series(dtype=str)).astype(str).value_counts().to_dict()
    requested_pairs = [f"{s}|{t}" for s in config.symbols for t in config.timeframes]
    observed_pairs = set(
        directional.get("symbol", pd.Series(dtype=str)).astype(str)
        + "|"
        + directional.get("timeframe", pd.Series(dtype=str)).astype(str)
    ) if len(directional) else set()
    return {
        "requested_symbols": config.symbols,
        "requested_timeframes": config.timeframes,
        "requested_pairs": requested_pairs,
        "observed_pairs": sorted(observed_pairs),
        "missing_pairs": sorted(set(requested_pairs) - observed_pairs),
        "symbol_counts": {str(k): int(v) for k, v in symbol_counts.items()},
        "timeframe_counts": {str(k): int(v) for k, v in timeframe_counts.items()},
        "provider_counts": {str(k): int(v) for k, v in provider_counts.items()},
    }


def _group_metrics(frame: pd.DataFrame, column: str, *, return_column: str = "net_return_pct") -> List[Dict[str, Any]]:
    if column not in frame.columns:
        return []
    records: List[Dict[str, Any]] = []
    for key, group in frame.groupby(column, dropna=False):
        metrics = _metric_dict(fixed_metrics(group, return_column=return_column))
        records.append({"key": str(key), **metrics})
    return sorted(records, key=lambda item: item["key"])


def _load_histories(config: FreshOOSConfig) -> Dict[Tuple[str, str], pd.DataFrame]:
    histories: Dict[Tuple[str, str], pd.DataFrame] = {}
    try:
        from engine.historical_data_store import load_history  # type: ignore
    except Exception:
        return histories
    for timeframe in config.timeframes:
        for symbol in config.symbols:
            try:
                frame = load_history(symbol, timeframe, config.data_dir)
            except Exception:
                continue
            if isinstance(frame, pd.DataFrame) and not frame.empty:
                histories[(symbol, timeframe)] = frame
    return histories


def _timeframe_delta(timeframe: str) -> pd.Timedelta:
    text = str(timeframe).strip().lower()
    if len(text) < 2:
        raise ValueError(f"unsupported timeframe: {timeframe}")
    count = int(text[:-1])
    unit = text[-1]
    units = {"m": "min", "h": "h", "d": "D", "w": "W"}
    if count <= 0 or unit not in units:
        raise ValueError(f"unsupported timeframe: {timeframe}")
    return pd.Timedelta(count, unit=units[unit])


def _next_candle_timestamp(cutoff_utc: str, timeframe: str) -> str:
    cutoff = pd.Timestamp(cutoff_utc)
    if cutoff.tzinfo is None:
        cutoff = cutoff.tz_localize("UTC")
    return (cutoff + _timeframe_delta(timeframe)).isoformat()


def _warmup_start_timestamp(
    cutoff_utc: str,
    timeframe: str,
    *,
    min_window: int,
    horizons: Sequence[int],
    execution_delay_candles: int = 1,
    adaptive_evaluation_horizon: bool = True,
    safety_candles: int = 8,
) -> str:
    """Return a causal pre-roll start while keeping OOS output post-cutoff only.

    MarketReplayConfig.start_utc filters the OHLCV frame before feature
    calculation. Starting exactly after the development cutoff can therefore
    leave only a handful of fresh candles and break indicators that require a
    longer warm-up (for example RSI-14). The pre-roll is feature context only;
    `_run_replay_after_cutoff` removes every replay row at or before the frozen
    cutoff before returning it.
    """
    positive_horizons = [int(value) for value in horizons if int(value) > 0]
    max_horizon = max(positive_horizons or [1])
    if adaptive_evaluation_horizon:
        max_horizon *= 2
    required_candles = (
        max(1, int(min_window))
        + max_horizon
        + max(1, int(execution_delay_candles))
        + max(0, int(safety_candles))
    )
    cutoff = pd.Timestamp(cutoff_utc)
    if cutoff.tzinfo is None:
        cutoff = cutoff.tz_localize("UTC")
    return (cutoff - (_timeframe_delta(timeframe) * required_candles)).isoformat()


def _run_replay_after_cutoff(config: FreshOOSConfig, manifest: DevelopmentFreezeManifest) -> pd.DataFrame:
    try:
        from engine.market_replay import MarketReplayConfig, run_market_replay  # type: ignore
    except Exception as exc:
        raise RuntimeError(f"current market replay engine is unavailable: {exc}") from exc
    all_rows: List[pd.DataFrame] = []
    for timeframe in config.timeframes:
        horizons = sorted(set([1, 3, 6, 12, max(24, int(config.max_path_candles))]))
        min_window = 120
        execution_delay = 1
        adaptive_horizon = True
        replay_config = MarketReplayConfig(
            symbols=list(config.symbols),
            timeframe=timeframe,
            # IMPORTANT: this is a causal feature warm-up range, not the OOS
            # decision boundary. Returned rows are filtered against the frozen
            # cutoff below. Starting at the next candle caused short-frame
            # indicator failures when only a few fresh candles existed.
            start_utc=_warmup_start_timestamp(
                manifest.cutoff_timestamp_utc,
                timeframe,
                min_window=min_window,
                horizons=horizons,
                execution_delay_candles=execution_delay,
                adaptive_evaluation_horizon=adaptive_horizon,
            ),
            data_dir=config.data_dir,
            min_window=min_window,
            horizons=horizons,
            include_neutral=True,
            execution_delay_candles=execution_delay,
            adaptive_evaluation_horizon=adaptive_horizon,
            strict_leakage_audit=True,
            source="FRESH_OOS_REPLAY_V2",
        )
        run_id = "fresh_oos_v2_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + "_" + timeframe
        _run, _summary, rows = run_market_replay(replay_config, run_id=run_id, save=False)
        if isinstance(rows, pd.DataFrame) and not rows.empty:
            fresh_rows = strictly_fresh_rows(rows, manifest.cutoff_timestamp_utc)
            if not fresh_rows.empty:
                all_rows.append(fresh_rows)
    return pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()


def run_fresh_oos_pipeline(config: FreshOOSConfig) -> FreshOOSReport:
    output = Path(config.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    freeze_dir = output / "development_freeze"
    manifest = freeze_development_dataset(
        config.development_replay_csv,
        freeze_dir,
        force=config.force_refreeze,
    )
    source_frame = pd.read_csv(config.development_replay_csv, low_memory=False)
    if config.run_replay:
        replay_rows = _run_replay_after_cutoff(config, manifest)
    else:
        replay_rows = strictly_fresh_rows(source_frame, manifest.cutoff_timestamp_utc)
    fresh = _normalize_replay(replay_rows) if not replay_rows.empty else pd.DataFrame()

    blockers: List[str] = []
    warnings: List[str] = []
    if not fresh.empty:
        ts_col = _timestamp_column(fresh)
        cutoff = pd.Timestamp(manifest.cutoff_timestamp_utc)
        overlap = fresh[ts_col] <= cutoff
        if overlap.any():
            blockers.append(f"{int(overlap.sum())} rows overlap the development cutoff")
            if config.strict_no_overlap:
                fresh = fresh.loc[~overlap].reset_index(drop=True)
    directional = fresh[fresh.get("side", pd.Series(dtype=str)).astype(str).isin(["LONG", "SHORT"])].copy() if not fresh.empty else pd.DataFrame()
    all_metrics = fixed_metrics(directional)
    gate = directional[pd.to_numeric(directional.get("score", np.nan), errors="coerce") >= config.fixed_score_threshold].copy() if not directional.empty else pd.DataFrame()
    gate_metrics = fixed_metrics(gate)
    coverage = _coverage(fresh, config) if not fresh.empty else _coverage(pd.DataFrame(), config)

    if len(directional) < config.min_fresh_directional_rows:
        blockers.append(
            f"fresh directional sample count {len(directional)} is below required {config.min_fresh_directional_rows}"
        )
    for symbol in config.symbols:
        count = int(coverage["symbol_counts"].get(symbol, 0))
        if count < config.min_rows_per_symbol:
            warnings.append(f"{symbol} has only {count} fresh directional rows")
    if coverage["missing_pairs"]:
        warnings.append(f"missing requested symbol/timeframe pairs: {coverage['missing_pairs']}")

    fixed_pass = (
        gate_metrics.sample_count >= config.min_fresh_directional_rows
        and gate_metrics.expectancy > 0
        and gate_metrics.profit_factor >= 1.05
        and gate_metrics.positive_time_folds >= config.min_positive_time_folds
        and not blockers
    )
    if len(directional) < config.min_fresh_directional_rows:
        status = "READY_AWAITING_FRESH_DATA"
    elif fixed_pass:
        status = "PASS_FIXED_BENCHMARK_RESEARCH_ONLY"
    else:
        status = "COMPLETE_NO_PROMOTION"
        blockers.append("fixed, pre-registered benchmark did not satisfy untouched OOS promotion constraints")

    histories = _load_histories(config)
    registry = CostProfileRegistry.from_json(config.cost_profile_file) if config.cost_profile_file else CostProfileRegistry()
    store_result = build_feature_store_v2(
        fresh,
        histories,
        output / "feature_store_v2",
        max_path_candles=config.max_path_candles,
        cost_registry=registry,
        development_cutoff_utc=manifest.cutoff_timestamp_utc,
    )
    if store_result.validation_errors:
        blockers.extend(store_result.validation_errors)
        status = "FAILED_DATA_INTEGRITY"
    if len(fresh) and store_result.feature_rows < len(fresh):
        blockers.append(
            f"feature store covers {store_result.feature_rows}/{len(fresh)} fresh replay rows; historical OHLCV coverage is incomplete"
        )
        status = "FAILED_DATA_COVERAGE"
    warnings.extend(store_result.warnings)

    report = FreshOOSReport(
        status=status,
        mode="FRESH_OOS_FIXED_BENCHMARK_ONLY",
        development_dataset_id=manifest.dataset_id,
        development_cutoff_utc=manifest.cutoff_timestamp_utc,
        source_replay_rows=int(len(source_frame)),
        fresh_rows=int(len(fresh)),
        fresh_directional_rows=int(len(directional)),
        fixed_threshold=float(config.fixed_score_threshold),
        all_directional=_metric_dict(all_metrics),
        fixed_gate=_metric_dict(gate_metrics),
        by_symbol=_group_metrics(directional, "symbol"),
        by_side=_group_metrics(directional, "side"),
        by_regime=_group_metrics(directional, "regime_label"),
        coverage=coverage,
        blockers=sorted(set(blockers)),
        warnings=sorted(set(warnings)),
        feature_store=asdict(store_result),
        promotion_applied=False,
        paper_live_enabled=False,
    )
    report_path = output / "fresh_oos_report.json"
    report_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
    _write_markdown_report(report, output / "fresh_oos_report.md")
    _write_coverage_csv(report, output / "fresh_oos_coverage.csv")
    return report


def _write_coverage_csv(report: FreshOOSReport, path: Path) -> None:
    rows: List[Dict[str, Any]] = []
    for section, records in (("SYMBOL", report.by_symbol), ("SIDE", report.by_side), ("REGIME", report.by_regime)):
        for record in records:
            rows.append({"section": section, **record})
    pd.DataFrame(rows).to_csv(path, index=False)


def _write_markdown_report(report: FreshOOSReport, path: Path) -> None:
    lines = [
        "# Freakto Fresh OOS Replay & Feature Store v2",
        "",
        f"- Status: `{report.status}`",
        f"- Mode: `{report.mode}`",
        f"- Development dataset: `{report.development_dataset_id}`",
        f"- Development cutoff: `{report.development_cutoff_utc}`",
        f"- Fresh rows: `{report.fresh_rows}`",
        f"- Fresh directional rows: `{report.fresh_directional_rows}`",
        f"- Fixed score threshold: `{report.fixed_threshold}`",
        f"- Promotion applied: `{report.promotion_applied}`",
        f"- Paper/Live enabled: `{report.paper_live_enabled}`",
        "",
        "## Fixed benchmark",
        "",
        f"- Samples: `{report.fixed_gate.get('sample_count', 0)}`",
        f"- Expectancy: `{report.fixed_gate.get('expectancy', 0.0):.6f}%`",
        f"- Profit factor: `{report.fixed_gate.get('profit_factor', 0.0)}`",
        f"- Positive folds: `{report.fixed_gate.get('positive_time_folds', 0)}/{report.fixed_gate.get('total_time_folds', 0)}`",
        "",
        "## Blockers",
    ]
    lines.extend([f"- {item}" for item in report.blockers] or ["- None"])
    lines.extend(["", "## Warnings"])
    lines.extend([f"- {item}" for item in report.warnings] or ["- None"])
    lines.extend([
        "",
        "## Safety",
        "",
        "The fresh dataset is never used for threshold or weight selection. This pipeline is research-only and does not enable Paper or Live trading.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
