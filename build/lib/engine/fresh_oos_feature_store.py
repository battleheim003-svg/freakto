"""Fresh out-of-sample Feature Store v2 for Freakto.

This module intentionally separates entry-time features from future outcome paths.
It is research-only and never changes score weights, Paper, or Live settings.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

FEATURE_STORE_VERSION = "2.0.0"
RESEARCH_MODE = "FRESH_OOS_RESEARCH_ONLY"
DEFAULT_OUTPUT_DIR = Path("logs") / "fresh_oos_v2"
DEFAULT_FREEZE_DIR = DEFAULT_OUTPUT_DIR / "development_freeze"
DEFAULT_STORE_DIR = DEFAULT_OUTPUT_DIR / "feature_store_v2"

OHLCV_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")
OUTCOME_ONLY_COLUMNS = {
    "win",
    "outcome_label",
    "net_return_pct",
    "gross_return_pct",
    "market_return_pct",
    "target_hit",
    "target_1_hit",
    "target_2_hit",
    "target_3_hit",
    "stop_hit",
    "mfe_pct",
    "mae_pct",
    "first_exit_reason",
    "first_exit_candle_offset",
    "direction_correct",
}
ENTRY_FEATURE_CANDIDATES = (
    "open",
    "high",
    "low",
    "close",
    "volume",
    "sma_10",
    "sma_30",
    "ema_10",
    "rsi_14",
    "macd",
    "macd_signal",
    "macd_diff",
    "atr",
    "atr_pct",
    "volume_sma_20",
    "volume_ratio",
    "bb_upper",
    "bb_middle",
    "bb_lower",
)


@dataclass(frozen=True)
class DevelopmentFreezeManifest:
    schema_version: str
    dataset_id: str
    created_utc: str
    source_path: str
    source_sha256: str
    snapshot_path: str
    snapshot_sha256: str
    selected_run_id: str
    row_count: int
    directional_rows: int
    min_timestamp_utc: str
    cutoff_timestamp_utc: str
    symbols: List[str]
    timeframes: List[str]
    providers: List[str]
    research_lock: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CostProfile:
    provider: str
    symbol: str
    fee_bps_per_side: float
    slippage_bps_per_side: float
    source: str

    @property
    def round_trip_cost_pct(self) -> float:
        return 2.0 * (self.fee_bps_per_side + self.slippage_bps_per_side) / 100.0


@dataclass
class FeatureStoreBuildResult:
    status: str
    feature_rows: int
    path_rows: int
    complete_path_rows: int
    pending_path_rows: int
    feature_file: str
    path_file: str
    manifest_file: str
    validation_errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class CostProfileRegistry:
    """Resolve exchange/symbol execution assumptions without silently inventing precision."""

    DEFAULTS: Dict[str, Tuple[float, float]] = {
        "okx": (10.0, 5.0),
        "bybit": (10.0, 6.0),
        "kucoin": (10.0, 7.0),
        "kraken": (20.0, 8.0),
        "binance": (10.0, 5.0),
        "default": (15.0, 10.0),
    }

    def __init__(self, custom_profiles: Optional[Mapping[str, Mapping[str, Any]]] = None):
        self.custom_profiles = dict(custom_profiles or {})

    @classmethod
    def from_json(cls, path: str | Path | None) -> "CostProfileRegistry":
        if not path:
            return cls()
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"cost profile file not found: {file_path}")
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("cost profile JSON must contain an object")
        return cls(payload)

    def resolve(
        self,
        provider: Any,
        symbol: Any,
        *,
        recorded_fee_bps: Any = None,
        recorded_slippage_bps: Any = None,
    ) -> CostProfile:
        provider_key = str(provider or "unknown").strip().lower()
        symbol_key = str(symbol or "*").strip().upper()
        fee = _finite_float(recorded_fee_bps)
        slippage = _finite_float(recorded_slippage_bps)
        if fee is not None and slippage is not None and fee >= 0 and slippage >= 0:
            return CostProfile(provider_key, symbol_key, fee, slippage, "RECORDED_REPLAY_ESTIMATE")

        keys = [f"{provider_key}:{symbol_key}", f"{provider_key}:*", provider_key, "default"]
        for key in keys:
            item = self.custom_profiles.get(key)
            if not isinstance(item, Mapping):
                continue
            custom_fee = _finite_float(item.get("fee_bps_per_side"))
            custom_slippage = _finite_float(item.get("slippage_bps_per_side"))
            if custom_fee is None or custom_slippage is None or custom_fee < 0 or custom_slippage < 0:
                continue
            source = str(item.get("source") or f"CUSTOM_PROFILE:{key}")
            return CostProfile(provider_key, symbol_key, custom_fee, custom_slippage, source)

        default_fee, default_slippage = self.DEFAULTS.get(provider_key, self.DEFAULTS["default"])
        return CostProfile(provider_key, symbol_key, default_fee, default_slippage, "CONSERVATIVE_BUILTIN_FALLBACK")


def _finite_float(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _timestamp_column(frame: pd.DataFrame) -> str:
    for column in ("candle_timestamp", "feature_cutoff_timestamp", "timestamp_utc", "timestamp"):
        if column in frame.columns:
            return column
    raise ValueError("dataset has no recognized timestamp column")


def _latest_run(frame: pd.DataFrame) -> Tuple[str, pd.DataFrame]:
    if "run_id" not in frame.columns or frame["run_id"].dropna().empty:
        return "UNSPECIFIED_RUN", frame.copy()
    run_ids = sorted(frame["run_id"].dropna().astype(str).unique().tolist())
    replay_ids = [item for item in run_ids if item.startswith("market_replay_")]
    run_id = (replay_ids or run_ids)[-1]
    selected = frame[frame["run_id"].astype(str) == run_id].copy()
    return run_id, selected.reset_index(drop=True)


def freeze_development_dataset(
    source_csv: str | Path,
    output_dir: str | Path = DEFAULT_FREEZE_DIR,
    *,
    force: bool = False,
) -> DevelopmentFreezeManifest:
    source = Path(source_csv)
    if not source.exists():
        raise FileNotFoundError(f"development replay file not found: {source}")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "development_freeze_manifest.json"
    if manifest_path.exists() and not force:
        return load_freeze_manifest(manifest_path, verify=True)

    frame = pd.read_csv(source, low_memory=False)
    if frame.empty:
        raise ValueError("development replay dataset is empty")
    run_id, selected = _latest_run(frame)
    ts_col = _timestamp_column(selected)
    timestamps = pd.to_datetime(selected[ts_col], utc=True, errors="coerce")
    source_ts_col = _timestamp_column(frame)
    source_timestamps = pd.to_datetime(frame[source_ts_col], utc=True, errors="coerce").dropna()
    if timestamps.notna().sum() == 0 or source_timestamps.empty:
        raise ValueError("development replay has no valid timestamps")
    selected = selected.loc[timestamps.notna()].copy()
    timestamps = timestamps.loc[timestamps.notna()]
    selected[ts_col] = timestamps.astype(str)
    global_cutoff = source_timestamps.max()

    source_hash = sha256_file(source)
    dataset_id = hashlib.sha256(
        f"{source_hash}|{run_id}|{len(selected)}|{global_cutoff.isoformat()}".encode("utf-8")
    ).hexdigest()[:20]
    snapshot_path = output / f"development_{dataset_id}.csv.gz"
    selected.to_csv(snapshot_path, index=False, compression="gzip")
    snapshot_hash = sha256_file(snapshot_path)

    symbols = sorted(selected.get("symbol", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
    timeframes = sorted(selected.get("timeframe", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
    providers = sorted(selected.get("provider", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
    directional = selected.get("side", pd.Series(dtype=str)).astype(str).isin(["LONG", "SHORT"])
    manifest = DevelopmentFreezeManifest(
        schema_version="1.0.0",
        dataset_id=dataset_id,
        created_utc=utc_now_iso(),
        source_path=str(source),
        source_sha256=source_hash,
        snapshot_path=str(snapshot_path),
        snapshot_sha256=snapshot_hash,
        selected_run_id=run_id,
        row_count=int(len(selected)),
        directional_rows=int(directional.sum()),
        min_timestamp_utc=timestamps.min().isoformat(),
        cutoff_timestamp_utc=global_cutoff.isoformat(),
        symbols=symbols,
        timeframes=timeframes,
        providers=providers,
        research_lock={
            "frozen": True,
            "retuning_on_fresh_oos_forbidden": True,
            "threshold_selection_forbidden": True,
            "paper_live_enabled": False,
            "source_run_only": True,
            "cutoff_uses_all_known_source_rows": True,
        },
    )
    manifest_path.write_text(json.dumps(asdict(manifest), ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def load_freeze_manifest(path: str | Path, *, verify: bool = True) -> DevelopmentFreezeManifest:
    manifest_path = Path(path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = DevelopmentFreezeManifest(**payload)
    if verify:
        snapshot = Path(manifest.snapshot_path)
        if not snapshot.exists():
            raise FileNotFoundError(f"frozen snapshot is missing: {snapshot}")
        actual = sha256_file(snapshot)
        if actual != manifest.snapshot_sha256:
            raise ValueError("frozen development snapshot hash mismatch")
    return manifest


def strictly_fresh_rows(frame: pd.DataFrame, cutoff_utc: str) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame(columns=list(frame.columns) if isinstance(frame, pd.DataFrame) else [])
    ts_col = _timestamp_column(frame)
    timestamps = pd.to_datetime(frame[ts_col], utc=True, errors="coerce")
    cutoff = pd.Timestamp(cutoff_utc)
    if cutoff.tzinfo is None:
        cutoff = cutoff.tz_localize("UTC")
    mask = timestamps.notna() & (timestamps > cutoff)
    result = frame.loc[mask].copy()
    result[ts_col] = timestamps.loc[mask].astype(str)
    return result.reset_index(drop=True)


def _parse_targets(value: Any) -> List[float]:
    if isinstance(value, (list, tuple)):
        items = list(value)
    else:
        text = str(value or "").strip()
        if not text:
            return []
        try:
            decoded = json.loads(text)
            items = decoded if isinstance(decoded, list) else [decoded]
        except Exception:
            items = [item.strip() for item in text.replace("[", "").replace("]", "").split(",")]
    targets: List[float] = []
    for item in items:
        number = _finite_float(str(item).replace("`", "").replace(",", ""))
        if number is not None:
            targets.append(number)
    return targets


def _parse_price(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).replace("`", "").replace(",", "").strip()
    if not text or text.lower() in {"none", "nan", "null", "---"} or "نامشخص" in text:
        return None
    if " - " in text:
        parts = [_finite_float(item) for item in text.split(" - ")]
        parts = [item for item in parts if item is not None]
        return sum(parts) / len(parts) if parts else None
    return _finite_float(text)


def _ensure_history(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    missing = [column for column in OHLCV_COLUMNS if column not in work.columns]
    if missing:
        raise ValueError(f"history is missing required columns: {missing}")
    work["timestamp"] = pd.to_datetime(work["timestamp"], utc=True, errors="coerce")
    for column in OHLCV_COLUMNS[1:]:
        work[column] = pd.to_numeric(work[column], errors="coerce")
    return work.dropna(subset=list(OHLCV_COLUMNS)).sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)


def _add_features_causally(history: pd.DataFrame) -> pd.DataFrame:
    try:
        from features import add_features  # type: ignore
    except Exception:
        return history.copy()
    featured = add_features(history.copy())
    featured["timestamp"] = pd.to_datetime(featured["timestamp"], utc=True, errors="coerce")
    return featured.sort_values("timestamp").reset_index(drop=True)


def _history_key(symbol: Any, timeframe: Any) -> Tuple[str, str]:
    return str(symbol or "").strip(), str(timeframe or "").strip()


def _path_touch_state(side: str, high: float, low: float, stop: Optional[float], target: Optional[float]) -> Tuple[bool, bool, bool]:
    if side == "LONG":
        stop_hit = stop is not None and low <= stop
        target_hit = target is not None and high >= target
    elif side == "SHORT":
        stop_hit = stop is not None and high >= stop
        target_hit = target is not None and low <= target
    else:
        stop_hit = False
        target_hit = False
    return bool(stop_hit), bool(target_hit), bool(stop_hit and target_hit)


def _signed_return(side: str, entry: float, close: float) -> float:
    raw = ((close - entry) / entry) * 100.0
    return raw if side == "LONG" else -raw if side == "SHORT" else 0.0


def build_feature_store_v2(
    replay_rows: pd.DataFrame,
    histories: Mapping[Tuple[str, str], pd.DataFrame],
    output_dir: str | Path = DEFAULT_STORE_DIR,
    *,
    max_path_candles: int = 24,
    cost_registry: Optional[CostProfileRegistry] = None,
    development_cutoff_utc: str = "",
) -> FeatureStoreBuildResult:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    feature_file = output / "fresh_oos_features_v2.csv.gz"
    path_file = output / "fresh_oos_outcome_paths_v2.csv.gz"
    manifest_file = output / "feature_store_v2_manifest.json"
    registry = cost_registry or CostProfileRegistry()

    if replay_rows is None or replay_rows.empty:
        empty_features = pd.DataFrame()
        empty_paths = pd.DataFrame()
        empty_features.to_csv(feature_file, index=False, compression="gzip")
        empty_paths.to_csv(path_file, index=False, compression="gzip")
        manifest_file.write_text(json.dumps({
            "schema_version": FEATURE_STORE_VERSION,
            "status": "READY_AWAITING_FRESH_DATA",
            "feature_rows": 0,
            "path_rows": 0,
            "research_mode": RESEARCH_MODE,
            "paper_live_enabled": False,
        }, indent=2), encoding="utf-8")
        return FeatureStoreBuildResult(
            "READY_AWAITING_FRESH_DATA", 0, 0, 0, 0,
            str(feature_file), str(path_file), str(manifest_file), [], []
        )

    rows = replay_rows.copy()
    ts_col = _timestamp_column(rows)
    rows[ts_col] = pd.to_datetime(rows[ts_col], utc=True, errors="coerce")
    rows = rows.dropna(subset=[ts_col]).sort_values(ts_col).reset_index(drop=True)
    validation_errors: List[str] = []
    warnings: List[str] = []
    if development_cutoff_utc:
        cutoff = pd.Timestamp(development_cutoff_utc)
        if cutoff.tzinfo is None:
            cutoff = cutoff.tz_localize("UTC")
        overlap = rows[ts_col] <= cutoff
        if overlap.any():
            validation_errors.append(f"{int(overlap.sum())} replay rows overlap the frozen development cutoff")
            rows = rows.loc[~overlap].reset_index(drop=True)

    prepared_histories: Dict[Tuple[str, str], Tuple[pd.DataFrame, pd.DataFrame]] = {}
    for key, history in histories.items():
        raw = _ensure_history(history)
        prepared_histories[key] = (raw, _add_features_causally(raw))

    feature_records: List[Dict[str, Any]] = []
    path_records: List[Dict[str, Any]] = []
    complete_paths = 0
    pending_paths = 0
    seen_ids: set[str] = set()

    for position, row in rows.iterrows():
        symbol = str(row.get("symbol") or "").strip()
        timeframe = str(row.get("timeframe") or "").strip()
        key = _history_key(symbol, timeframe)
        if key not in prepared_histories:
            warnings.append(f"history unavailable for {symbol} {timeframe}")
            continue
        raw_history, featured_history = prepared_histories[key]
        cutoff_ts = pd.Timestamp(row.get("feature_cutoff_timestamp") or row.get(ts_col))
        execution_ts_value = row.get("execution_timestamp")
        execution_ts = pd.Timestamp(execution_ts_value) if pd.notna(execution_ts_value) and str(execution_ts_value) else None
        if cutoff_ts.tzinfo is None:
            cutoff_ts = cutoff_ts.tz_localize("UTC")
        if execution_ts is not None and execution_ts.tzinfo is None:
            execution_ts = execution_ts.tz_localize("UTC")

        cutoff_matches = featured_history.index[featured_history["timestamp"] == cutoff_ts].tolist()
        if not cutoff_matches:
            cutoff_matches = featured_history.index[featured_history["timestamp"] <= cutoff_ts].tolist()
        if not cutoff_matches:
            warnings.append(f"feature cutoff missing for {symbol} {timeframe} {cutoff_ts.isoformat()}")
            continue
        cutoff_idx = int(cutoff_matches[-1])
        if execution_ts is None:
            execution_idx = cutoff_idx + max(1, int(_finite_float(row.get("execution_delay_candles")) or 1))
            if execution_idx < len(raw_history):
                execution_ts = pd.Timestamp(raw_history.iloc[execution_idx]["timestamp"])
        else:
            execution_matches = raw_history.index[raw_history["timestamp"] == execution_ts].tolist()
            execution_idx = int(execution_matches[0]) if execution_matches else cutoff_idx + 1
        if execution_ts is None or execution_idx >= len(raw_history) or execution_idx <= cutoff_idx:
            warnings.append(f"execution candle unavailable or non-causal for {symbol} {timeframe} {cutoff_ts.isoformat()}")
            continue

        decision_id = str(row.get("decision_id") or "").strip()
        if not decision_id:
            raw_id = f"FRESH_OOS_V2|{symbol}|{timeframe}|{cutoff_ts.isoformat()}|{position}"
            decision_id = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:20]
        if decision_id in seen_ids:
            validation_errors.append(f"duplicate decision_id: {decision_id}")
            continue
        seen_ids.add(decision_id)

        feature_candle = featured_history.iloc[cutoff_idx]
        execution_candle = raw_history.iloc[execution_idx]
        entry_price = _finite_float(row.get("entry_price")) or float(execution_candle["open"])
        side = str(row.get("side") or "NEUTRAL").upper()
        cost = registry.resolve(
            row.get("provider"), symbol,
            recorded_fee_bps=row.get("fee_bps_per_side"),
            recorded_slippage_bps=row.get("slippage_bps_per_side"),
        )
        feature_record: Dict[str, Any] = {
            "feature_store_version": FEATURE_STORE_VERSION,
            "research_mode": RESEARCH_MODE,
            "decision_id": decision_id,
            "run_id": row.get("run_id", ""),
            "symbol": symbol,
            "timeframe": timeframe,
            "provider": row.get("provider", ""),
            "feature_cutoff_timestamp": cutoff_ts.isoformat(),
            "execution_timestamp": execution_ts.isoformat(),
            "decision_time_basis": row.get("decision_time_basis", "AFTER_BAR_CLOSE"),
            "execution_price_basis": row.get("execution_price_basis", "NEXT_AVAILABLE_BAR_OPEN"),
            "side": side,
            "score": row.get("score", ""),
            "confidence_label": row.get("confidence_label", ""),
            "risk_label": row.get("risk_label", ""),
            "actionability": row.get("actionability", ""),
            "is_actionable": row.get("is_actionable", False),
            "entry_price": entry_price,
            "stop_price": _parse_price(row.get("stop_zone")),
            "targets_json": json.dumps(_parse_targets(row.get("targets")), ensure_ascii=False),
            "regime_label": row.get("regime_label", ""),
            "regime_confidence": row.get("regime_confidence", ""),
            "trend_score": row.get("trend_score", ""),
            "momentum_score": row.get("momentum_score", ""),
            "volume_score": row.get("volume_score", ""),
            "structure_score": row.get("structure_score", ""),
            "regime_score": row.get("regime_score", ""),
            "risk_penalty": row.get("risk_penalty", ""),
            "historical_edge_score": row.get("historical_edge_score", ""),
            "adaptive_adjustment": row.get("adaptive_adjustment", ""),
            "fee_bps_per_side": cost.fee_bps_per_side,
            "slippage_bps_per_side": cost.slippage_bps_per_side,
            "round_trip_cost_pct": cost.round_trip_cost_pct,
            "execution_cost_source": cost.source,
            "development_cutoff_utc": development_cutoff_utc,
            "fresh_oos_locked": True,
            "retuning_allowed": False,
            "paper_live_enabled": False,
        }
        for column in ENTRY_FEATURE_CANDIDATES:
            if column in feature_candle.index:
                feature_record[f"feature_{column}"] = feature_candle.get(column)
        # Preserve model-contract and external entry-time fields, but never outcomes.
        for column in rows.columns:
            if column in OUTCOME_ONLY_COLUMNS or column in feature_record or column.startswith("net_") or column.startswith("gross_"):
                continue
            if column.startswith("model_") or column in {
                "news_sentiment_score", "onchain_signal_score", "cross_exchange_volume_ratio",
                "execution_volatility_multiplier", "execution_liquidity_multiplier",
            }:
                feature_record[column] = row.get(column)
        feature_records.append(feature_record)

        stop = feature_record["stop_price"]
        targets = _parse_targets(row.get("targets"))
        target_1 = targets[0] if targets else None
        available = len(raw_history) - execution_idx
        path_length = min(max(0, int(max_path_candles)), max(0, available))
        if path_length >= max_path_candles:
            complete_paths += 1
        else:
            pending_paths += 1
        first_exit_reason = "NO_EXIT"
        first_exit_offset: Optional[int] = None
        for offset in range(path_length):
            candle = raw_history.iloc[execution_idx + offset]
            high = float(candle["high"])
            low = float(candle["low"])
            close = float(candle["close"])
            stop_hit, target_hit, ambiguous = _path_touch_state(side, high, low, stop, target_1)
            if first_exit_offset is None:
                if ambiguous:
                    first_exit_reason = "STOP_FIRST_CONSERVATIVE_AMBIGUOUS"
                    first_exit_offset = offset
                elif stop_hit:
                    first_exit_reason = "STOP"
                    first_exit_offset = offset
                elif target_hit:
                    first_exit_reason = "TARGET_1"
                    first_exit_offset = offset
            gross = _signed_return(side, entry_price, close)
            path_records.append({
                "feature_store_version": FEATURE_STORE_VERSION,
                "decision_id": decision_id,
                "symbol": symbol,
                "timeframe": timeframe,
                "provider": row.get("provider", ""),
                "side": side,
                "path_offset": offset,
                "path_timestamp": pd.Timestamp(candle["timestamp"]).isoformat(),
                "open": float(candle["open"]),
                "high": high,
                "low": low,
                "close": close,
                "volume": float(candle["volume"]),
                "gross_signed_return_pct": round(gross, 10),
                "net_signed_return_pct": round(gross - cost.round_trip_cost_pct, 10) if side in {"LONG", "SHORT"} else 0.0,
                "stop_hit_this_candle": stop_hit,
                "target_1_hit_this_candle": target_hit,
                "same_candle_ambiguity": ambiguous,
                "first_exit_reason_so_far": first_exit_reason,
                "first_exit_offset": first_exit_offset,
                "path_complete_for_requested_horizon": path_length >= max_path_candles,
                "outcome_only": True,
            })

    features = pd.DataFrame(feature_records)
    paths = pd.DataFrame(path_records)
    feature_outcome_overlap = OUTCOME_ONLY_COLUMNS.intersection(features.columns)
    if feature_outcome_overlap:
        validation_errors.append(f"outcome leakage columns found in feature table: {sorted(feature_outcome_overlap)}")
    if not paths.empty and not features.empty:
        unknown_paths = set(paths["decision_id"]) - set(features["decision_id"])
        if unknown_paths:
            validation_errors.append(f"{len(unknown_paths)} path decision IDs have no feature row")
        path_times = pd.to_datetime(paths["path_timestamp"], utc=True, errors="coerce")
        execution_map = features.set_index("decision_id")["execution_timestamp"].to_dict()
        bad_order = 0
        for idx, path_row in paths.iterrows():
            execution_time = pd.Timestamp(execution_map.get(path_row["decision_id"]))
            offset = int(path_row.get("path_offset", -1))
            if path_times.iloc[idx] < execution_time or (offset == 0 and path_times.iloc[idx] != execution_time) or (offset > 0 and path_times.iloc[idx] <= execution_time):
                bad_order += 1
        if bad_order:
            validation_errors.append(f"{bad_order} outcome path rows violate execution/path ordering")

    features.to_csv(feature_file, index=False, compression="gzip")
    paths.to_csv(path_file, index=False, compression="gzip")
    status = "COMPLETE" if len(features) and not validation_errors else "FAILED_VALIDATION" if validation_errors else "READY_AWAITING_FRESH_DATA"
    manifest_payload = {
        "schema_version": FEATURE_STORE_VERSION,
        "created_utc": utc_now_iso(),
        "status": status,
        "research_mode": RESEARCH_MODE,
        "feature_rows": int(len(features)),
        "path_rows": int(len(paths)),
        "complete_path_rows": int(complete_paths),
        "pending_path_rows": int(pending_paths),
        "feature_file": str(feature_file),
        "feature_sha256": sha256_file(feature_file),
        "path_file": str(path_file),
        "path_sha256": sha256_file(path_file),
        "max_path_candles": int(max_path_candles),
        "development_cutoff_utc": development_cutoff_utc,
        "entry_outcome_separation": True,
        "retuning_allowed": False,
        "paper_live_enabled": False,
        "validation_errors": validation_errors,
        "warnings": sorted(set(warnings))[:100],
    }
    manifest_file.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return FeatureStoreBuildResult(
        status=status,
        feature_rows=int(len(features)),
        path_rows=int(len(paths)),
        complete_path_rows=int(complete_paths),
        pending_path_rows=int(pending_paths),
        feature_file=str(feature_file),
        path_file=str(path_file),
        manifest_file=str(manifest_file),
        validation_errors=validation_errors,
        warnings=sorted(set(warnings)),
    )


def verify_frozen_source_unchanged(manifest: DevelopmentFreezeManifest) -> bool:
    source = Path(manifest.source_path)
    return source.exists() and sha256_file(source) == manifest.source_sha256
