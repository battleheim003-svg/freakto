"""
Freakto v10.0 - Historical Market Data Store

Builds and validates a local, replay-safe OHLCV archive using paginated CCXT
requests.  The store is deliberately separate from Forward/Paper/Live logs.

Safety rules
------------
* No order is ever created.
* Data is de-duplicated and range-filtered before it is saved.
* A single provider is selected for each symbol/timeframe dataset to avoid
  stitching exchange microstructure together silently.
* Every dataset receives a manifest and a data-quality report.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd


VERSION = "v10.0.0"
DEFAULT_DATA_DIR = Path("data") / "market_replay"
DEFAULT_REPORT_DIR = Path("logs") / "market_replay" / "data_quality"
DEFAULT_EXCHANGE_ORDER = ("kucoin", "okx", "bybit", "kraken")
OHLCV_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


@dataclass
class HistoricalDataRequest:
    symbols: List[str]
    timeframe: str = "4h"
    start_utc: str = ""
    end_utc: str = ""
    years: float = 3.0
    exchange: str = "auto"
    exchange_order: List[str] = field(default_factory=lambda: list(DEFAULT_EXCHANGE_ORDER))
    batch_limit: int = 1000
    max_retries: int = 3
    retry_backoff_seconds: float = 1.5
    min_acceptable_coverage_pct: float = 90.0
    data_dir: str = str(DEFAULT_DATA_DIR)
    update_existing: bool = True
    force_refresh: bool = False


@dataclass
class DatasetQuality:
    symbol: str
    timeframe: str
    provider: str
    requested_start_utc: str
    requested_end_utc: str
    actual_start_utc: str = ""
    actual_end_utc: str = ""
    expected_candles: int = 0
    actual_candles: int = 0
    coverage_pct: float = 0.0
    duplicate_rows_removed: int = 0
    missing_candles_estimate: int = 0
    gap_count: int = 0
    largest_gap_candles: int = 0
    invalid_ohlc_rows: int = 0
    nonpositive_price_rows: int = 0
    zero_volume_rows: int = 0
    monotonic_timestamps: bool = False
    no_future_rows: bool = True
    continuity_status: str = "UNKNOWN"
    readiness_status: str = "NOT_READY"
    warnings: List[str] = field(default_factory=list)


@dataclass
class HistoricalDatasetResult:
    symbol: str
    timeframe: str
    ok: bool
    provider: str = ""
    dataset_path: str = ""
    manifest_path: str = ""
    rows: int = 0
    fetched_rows: int = 0
    used_cache: bool = False
    attempts: List[Dict[str, Any]] = field(default_factory=list)
    quality: Optional[DatasetQuality] = None
    error: str = ""


@dataclass
class HistoricalDataBuildReport:
    run_id: str
    version: str
    started_utc: str
    finished_utc: str
    requested_symbols: int
    completed_symbols: int
    failed_symbols: int
    total_rows: int
    ready_datasets: int
    partial_datasets: int
    results: List[HistoricalDatasetResult]
    blockers: List[str]
    warnings: List[str]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def make_run_id() -> str:
    return "historical_data_" + utc_now().strftime("%Y%m%d_%H%M%S")


def parse_utc(value: Any, *, default: Optional[datetime] = None) -> datetime:
    if value in (None, ""):
        if default is None:
            raise ValueError("datetime value is required")
        return default.astimezone(timezone.utc)

    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts.to_pydatetime()


def resolve_range(request: HistoricalDataRequest) -> Tuple[datetime, datetime]:
    end = parse_utc(request.end_utc, default=utc_now())
    if request.start_utc:
        start = parse_utc(request.start_utc)
    else:
        days = max(1, int(round(float(request.years) * 365.25)))
        start = end - timedelta(days=days)
    if start >= end:
        raise ValueError("start_utc must be earlier than end_utc")
    return start, end


def timeframe_to_milliseconds(timeframe: str) -> int:
    text = str(timeframe).strip().lower()
    if len(text) < 2:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    unit = text[-1]
    try:
        count = int(text[:-1])
    except ValueError as exc:
        raise ValueError(f"Unsupported timeframe: {timeframe}") from exc
    if count <= 0:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    multipliers = {
        "m": 60_000,
        "h": 3_600_000,
        "d": 86_400_000,
        "w": 604_800_000,
    }
    if unit not in multipliers:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    return count * multipliers[unit]


def floor_datetime_to_timeframe(value: datetime, timeframe: str) -> datetime:
    milliseconds = timeframe_to_milliseconds(timeframe)
    epoch_ms = int(value.timestamp() * 1000)
    floored = (epoch_ms // milliseconds) * milliseconds
    return datetime.fromtimestamp(floored / 1000, tz=timezone.utc)


def symbol_slug(symbol: str) -> str:
    return str(symbol).replace("/", "_").replace(":", "_").replace(" ", "").upper()


def dataset_path(symbol: str, timeframe: str, data_dir: Path | str = DEFAULT_DATA_DIR) -> Path:
    return Path(data_dir) / str(timeframe) / f"{symbol_slug(symbol)}.csv.gz"


def manifest_path(symbol: str, timeframe: str, data_dir: Path | str = DEFAULT_DATA_DIR) -> Path:
    return Path(data_dir) / str(timeframe) / f"{symbol_slug(symbol)}.manifest.json"


def quality_report_path(symbol: str, timeframe: str, report_dir: Path | str = DEFAULT_REPORT_DIR) -> Path:
    return Path(report_dir) / f"{symbol_slug(symbol)}_{timeframe}_quality.json"


def _normalise_frame(frame: pd.DataFrame, provider: str = "") -> Tuple[pd.DataFrame, int]:
    if frame is None or frame.empty:
        return pd.DataFrame(columns=OHLCV_COLUMNS + ["provider"]), 0

    work = frame.copy()
    if "timestamp" not in work.columns:
        if isinstance(work.index, pd.DatetimeIndex):
            work = work.reset_index().rename(columns={work.index.name or "index": "timestamp"})
        else:
            raise ValueError("historical data requires a timestamp column")

    raw_timestamp = work["timestamp"]
    if pd.api.types.is_numeric_dtype(raw_timestamp):
        work["timestamp"] = pd.to_datetime(raw_timestamp, unit="ms", utc=True, errors="coerce")
    else:
        work["timestamp"] = pd.to_datetime(raw_timestamp, utc=True, errors="coerce")

    for column in ["open", "high", "low", "close", "volume"]:
        if column not in work.columns:
            work[column] = pd.NA
        work[column] = pd.to_numeric(work[column], errors="coerce")

    work = work.dropna(subset=OHLCV_COLUMNS).copy()
    work = work.sort_values("timestamp")
    before = len(work)
    work = work.drop_duplicates(subset=["timestamp"], keep="last")
    duplicates_removed = before - len(work)
    work["provider"] = str(provider or (work.get("provider", pd.Series([""])).iloc[-1] if len(work) else ""))
    work = work[OHLCV_COLUMNS + ["provider"]].reset_index(drop=True)
    return work, duplicates_removed


def load_history(symbol: str, timeframe: str, data_dir: Path | str = DEFAULT_DATA_DIR) -> pd.DataFrame:
    path = dataset_path(symbol, timeframe, data_dir)
    if not path.exists():
        return pd.DataFrame(columns=OHLCV_COLUMNS + ["provider"])
    frame = pd.read_csv(path, compression="gzip")
    normalised, _ = _normalise_frame(frame)
    return normalised


def save_history(frame: pd.DataFrame, symbol: str, timeframe: str, data_dir: Path | str = DEFAULT_DATA_DIR) -> Path:
    path = dataset_path(symbol, timeframe, data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    work, _ = _normalise_frame(frame, provider=str(frame["provider"].iloc[-1]) if "provider" in frame and len(frame) else "")
    serialised = work.copy()
    serialised["timestamp"] = serialised["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    serialised.to_csv(path, index=False, compression="gzip", encoding="utf-8")
    return path


def evaluate_quality(
    frame: pd.DataFrame,
    *,
    symbol: str,
    timeframe: str,
    provider: str,
    requested_start: datetime,
    requested_end: datetime,
    duplicate_rows_removed: int = 0,
) -> DatasetQuality:
    tf_ms = timeframe_to_milliseconds(timeframe)
    start_ms = int(requested_start.timestamp() * 1000)
    end_ms = int(requested_end.timestamp() * 1000)
    expected = max(0, int(math.floor((end_ms - start_ms) / tf_ms)) + 1)

    work, dedup = _normalise_frame(frame, provider=provider)
    duplicate_rows_removed += dedup
    if not work.empty:
        mask = (work["timestamp"] >= pd.Timestamp(requested_start)) & (work["timestamp"] <= pd.Timestamp(requested_end))
        work = work.loc[mask].copy()

    actual = len(work)
    coverage = min(100.0, (actual / expected * 100.0)) if expected else 0.0
    invalid_ohlc = 0
    nonpositive = 0
    zero_volume = 0
    gap_count = 0
    largest_gap = 0
    missing_estimate = 0
    monotonic = False
    actual_start = ""
    actual_end = ""
    no_future = True

    if actual:
        invalid_mask = (
            (work["high"] < work[["open", "close", "low"]].max(axis=1))
            | (work["low"] > work[["open", "close", "high"]].min(axis=1))
        )
        invalid_ohlc = int(invalid_mask.sum())
        nonpositive = int((work[["open", "high", "low", "close"]] <= 0).any(axis=1).sum())
        zero_volume = int((work["volume"] <= 0).sum())
        diffs = work["timestamp"].diff().dropna().dt.total_seconds().mul(1000)
        gap_units = (diffs / tf_ms).round().astype(int)
        gap_values = gap_units[gap_units > 1]
        gap_count = int(len(gap_values))
        largest_gap = int(gap_values.max() - 1) if len(gap_values) else 0
        missing_estimate = int((gap_values - 1).sum()) if len(gap_values) else 0
        monotonic = bool(work["timestamp"].is_monotonic_increasing)
        actual_start = work["timestamp"].iloc[0].isoformat()
        actual_end = work["timestamp"].iloc[-1].isoformat()
        no_future = bool(work["timestamp"].max() <= pd.Timestamp(requested_end) + pd.Timedelta(milliseconds=tf_ms))

    warnings: List[str] = []
    if coverage < 90:
        warnings.append(f"Coverage کمتر از 90% است: {coverage:.2f}%")
    if gap_count:
        warnings.append(f"{gap_count} شکاف زمانی شناسایی شد؛ missing≈{missing_estimate}")
    if invalid_ohlc:
        warnings.append(f"{invalid_ohlc} ردیف OHLC نامعتبر است")
    if nonpositive:
        warnings.append(f"{nonpositive} ردیف قیمت غیرمثبت دارد")
    if not monotonic and actual:
        warnings.append("Timestampها یکنواخت صعودی نیستند")

    if coverage >= 98 and not gap_count and not invalid_ohlc and not nonpositive and monotonic:
        continuity = "CONTINUOUS"
    elif coverage >= 90 and not invalid_ohlc and not nonpositive and monotonic:
        continuity = "USABLE_WITH_MINOR_GAPS"
    else:
        continuity = "PARTIAL_OR_INVALID"

    requested_days = max(0.0, (requested_end - requested_start).total_seconds() / 86400)
    actual_days = 0.0
    if actual >= 2:
        actual_days = (work["timestamp"].iloc[-1] - work["timestamp"].iloc[0]).total_seconds() / 86400

    if continuity == "CONTINUOUS" and actual_days >= min(requested_days * 0.98, 730):
        readiness = "REPLAY_READY"
    elif coverage >= 90 and actual_days >= min(requested_days * 0.90, 365):
        readiness = "REPLAY_READY_WITH_WARNINGS"
    elif actual:
        readiness = "PARTIAL_HISTORY"
    else:
        readiness = "NO_HISTORY"

    return DatasetQuality(
        symbol=symbol,
        timeframe=timeframe,
        provider=provider,
        requested_start_utc=requested_start.isoformat(),
        requested_end_utc=requested_end.isoformat(),
        actual_start_utc=actual_start,
        actual_end_utc=actual_end,
        expected_candles=expected,
        actual_candles=actual,
        coverage_pct=round(coverage, 3),
        duplicate_rows_removed=duplicate_rows_removed,
        missing_candles_estimate=missing_estimate,
        gap_count=gap_count,
        largest_gap_candles=largest_gap,
        invalid_ohlc_rows=invalid_ohlc,
        nonpositive_price_rows=nonpositive,
        zero_volume_rows=zero_volume,
        monotonic_timestamps=monotonic,
        no_future_rows=no_future,
        continuity_status=continuity,
        readiness_status=readiness,
        warnings=warnings,
    )


def _create_exchange(exchange_name: str):
    import ccxt

    name = str(exchange_name).lower().strip()
    options: Dict[str, Any] = {"enableRateLimit": True, "timeout": 30_000}
    if name == "bybit":
        options["options"] = {"defaultType": "spot"}
    exchange_class = getattr(ccxt, name, None)
    if exchange_class is None:
        raise ValueError(f"Unsupported exchange: {exchange_name}")
    return exchange_class(options)


def _fetch_with_retries(
    exchange,
    *,
    symbol: str,
    timeframe: str,
    since: int,
    limit: int,
    max_retries: int,
    retry_backoff_seconds: float,
):
    last_error: Optional[Exception] = None
    for attempt in range(1, max(1, max_retries) + 1):
        try:
            return exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)
        except Exception as exc:  # CCXT raises many exchange-specific subclasses.
            last_error = exc
            if attempt >= max_retries:
                break
            time.sleep(max(0.0, retry_backoff_seconds) * attempt)
    if last_error is not None:
        raise last_error
    return []


def fetch_exchange_history(
    *,
    exchange_name: str,
    symbol: str,
    timeframe: str,
    start: datetime,
    end: datetime,
    batch_limit: int = 1000,
    max_retries: int = 3,
    retry_backoff_seconds: float = 1.5,
    exchange_factory: Optional[Callable[[str], Any]] = None,
) -> pd.DataFrame:
    factory = exchange_factory or _create_exchange
    exchange = factory(exchange_name)
    tf_ms = timeframe_to_milliseconds(timeframe)
    since = int(floor_datetime_to_timeframe(start, timeframe).timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    batch_limit = max(10, min(int(batch_limit), 1500))
    rows: List[List[Any]] = []
    stagnant_batches = 0

    try:
        if hasattr(exchange, "load_markets"):
            exchange.load_markets()
        if getattr(exchange, "markets", None) and symbol not in exchange.markets:
            raise ValueError(f"{symbol} is not available on {exchange_name}")

        while since <= end_ms:
            batch = _fetch_with_retries(
                exchange,
                symbol=symbol,
                timeframe=timeframe,
                since=since,
                limit=batch_limit,
                max_retries=max_retries,
                retry_backoff_seconds=retry_backoff_seconds,
            )
            if not batch:
                break

            valid_batch = [item[:6] for item in batch if item and len(item) >= 6 and int(item[0]) <= end_ms]
            if valid_batch:
                rows.extend(valid_batch)

            last_timestamp = int(batch[-1][0])
            next_since = last_timestamp + tf_ms
            if next_since <= since:
                stagnant_batches += 1
                next_since = since + tf_ms
            else:
                stagnant_batches = 0
            if stagnant_batches >= 2:
                break
            since = next_since
            if last_timestamp >= end_ms:
                break

    finally:
        close_method = getattr(exchange, "close", None)
        if callable(close_method):
            try:
                close_method()
            except Exception:
                pass

    if not rows:
        return pd.DataFrame(columns=OHLCV_COLUMNS + ["provider"])

    frame = pd.DataFrame(rows, columns=OHLCV_COLUMNS)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
    frame["provider"] = exchange_name
    frame, _ = _normalise_frame(frame, provider=exchange_name)
    mask = (frame["timestamp"] >= pd.Timestamp(start)) & (frame["timestamp"] <= pd.Timestamp(end))
    return frame.loc[mask].reset_index(drop=True)


def _requested_provider_order(request: HistoricalDataRequest) -> List[str]:
    if request.exchange and request.exchange.lower() != "auto":
        return [request.exchange.lower()]
    result: List[str] = []
    for name in request.exchange_order or DEFAULT_EXCHANGE_ORDER:
        key = str(name).lower().strip()
        if key and key not in result:
            result.append(key)
    return result


def build_symbol_history(
    request: HistoricalDataRequest,
    symbol: str,
    *,
    exchange_factory: Optional[Callable[[str], Any]] = None,
) -> HistoricalDatasetResult:
    start, end = resolve_range(request)
    start = floor_datetime_to_timeframe(start, request.timeframe)
    end = floor_datetime_to_timeframe(end, request.timeframe)
    path = dataset_path(symbol, request.timeframe, request.data_dir)
    mpath = manifest_path(symbol, request.timeframe, request.data_dir)

    existing = pd.DataFrame()
    if request.update_existing and not request.force_refresh and path.exists():
        try:
            existing = load_history(symbol, request.timeframe, request.data_dir)
            cached_provider = str(existing["provider"].dropna().iloc[-1]) if len(existing) and "provider" in existing else "cache"
            cached_quality = evaluate_quality(
                existing,
                symbol=symbol,
                timeframe=request.timeframe,
                provider=cached_provider,
                requested_start=start,
                requested_end=end,
            )
            if cached_quality.coverage_pct >= request.min_acceptable_coverage_pct and cached_quality.invalid_ohlc_rows == 0:
                result = HistoricalDatasetResult(
                    symbol=symbol,
                    timeframe=request.timeframe,
                    ok=True,
                    provider=cached_provider,
                    dataset_path=str(path),
                    manifest_path=str(mpath),
                    rows=len(existing),
                    fetched_rows=0,
                    used_cache=True,
                    quality=cached_quality,
                )
                _write_manifest(result, request, mpath)
                _write_quality(result.quality)
                return result
        except Exception:
            existing = pd.DataFrame()

    best_frame = pd.DataFrame()
    best_quality: Optional[DatasetQuality] = None
    best_provider = ""
    attempts: List[Dict[str, Any]] = []

    for provider in _requested_provider_order(request):
        attempt_started = utc_now_iso()
        try:
            fetched = fetch_exchange_history(
                exchange_name=provider,
                symbol=symbol,
                timeframe=request.timeframe,
                start=start,
                end=end,
                batch_limit=request.batch_limit,
                max_retries=request.max_retries,
                retry_backoff_seconds=request.retry_backoff_seconds,
                exchange_factory=exchange_factory,
            )
            combined = fetched
            # Only merge cached data if it comes from the same provider. This keeps
            # the dataset's market microstructure consistent.
            if not existing.empty:
                existing_provider = str(existing["provider"].dropna().iloc[-1]) if "provider" in existing else ""
                if existing_provider == provider:
                    combined = pd.concat([existing, fetched], ignore_index=True)
            combined, duplicates_removed = _normalise_frame(combined, provider=provider)
            quality = evaluate_quality(
                combined,
                symbol=symbol,
                timeframe=request.timeframe,
                provider=provider,
                requested_start=start,
                requested_end=end,
                duplicate_rows_removed=duplicates_removed,
            )
            attempts.append({
                "provider": provider,
                "started_utc": attempt_started,
                "finished_utc": utc_now_iso(),
                "ok": bool(len(combined)),
                "rows": int(len(combined)),
                "coverage_pct": quality.coverage_pct,
                "error": "",
            })
            if best_quality is None or quality.coverage_pct > best_quality.coverage_pct:
                best_frame = combined
                best_quality = quality
                best_provider = provider
            if quality.coverage_pct >= request.min_acceptable_coverage_pct and quality.invalid_ohlc_rows == 0:
                break
        except Exception as exc:
            attempts.append({
                "provider": provider,
                "started_utc": attempt_started,
                "finished_utc": utc_now_iso(),
                "ok": False,
                "rows": 0,
                "coverage_pct": 0.0,
                "error": f"{type(exc).__name__}: {exc}",
            })

    if best_quality is None or best_frame.empty:
        return HistoricalDatasetResult(
            symbol=symbol,
            timeframe=request.timeframe,
            ok=False,
            dataset_path=str(path),
            manifest_path=str(mpath),
            attempts=attempts,
            error="No provider returned usable historical OHLCV data.",
        )

    saved_path = save_history(best_frame, symbol, request.timeframe, request.data_dir)
    result = HistoricalDatasetResult(
        symbol=symbol,
        timeframe=request.timeframe,
        ok=best_quality.readiness_status in {"REPLAY_READY", "REPLAY_READY_WITH_WARNINGS", "PARTIAL_HISTORY"},
        provider=best_provider,
        dataset_path=str(saved_path),
        manifest_path=str(mpath),
        rows=len(best_frame),
        fetched_rows=len(best_frame),
        used_cache=False,
        attempts=attempts,
        quality=best_quality,
        error="" if best_quality.actual_candles else "Historical data is empty after validation.",
    )
    _write_manifest(result, request, mpath)
    _write_quality(best_quality)
    return result


def _write_manifest(result: HistoricalDatasetResult, request: HistoricalDataRequest, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": VERSION,
        "generated_utc": utc_now_iso(),
        "request": asdict(request),
        "result": asdict(result),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _write_quality(quality: Optional[DatasetQuality]) -> None:
    if quality is None:
        return
    path = quality_report_path(quality.symbol, quality.timeframe)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(quality), ensure_ascii=False, indent=2), encoding="utf-8")


def build_historical_data(
    request: HistoricalDataRequest,
    *,
    exchange_factory: Optional[Callable[[str], Any]] = None,
) -> HistoricalDataBuildReport:
    run_id = make_run_id()
    started = utc_now_iso()
    results: List[HistoricalDatasetResult] = []
    for symbol in request.symbols:
        print("=" * 108)
        print(f"📚 Historical Data Build: {symbol} | {request.timeframe}")
        print("=" * 108)
        result = build_symbol_history(request, symbol, exchange_factory=exchange_factory)
        results.append(result)
        if result.ok and result.quality:
            print(
                f"✅ {symbol}: rows={result.rows} provider={result.provider} "
                f"coverage={result.quality.coverage_pct:.2f}% status={result.quality.readiness_status}"
            )
        else:
            print(f"❌ {symbol}: {result.error or 'historical data build failed'}")

    completed = sum(1 for item in results if item.ok)
    failed = len(results) - completed
    ready = sum(
        1 for item in results
        if item.quality and item.quality.readiness_status in {"REPLAY_READY", "REPLAY_READY_WITH_WARNINGS"}
    )
    partial = sum(1 for item in results if item.quality and item.quality.readiness_status == "PARTIAL_HISTORY")
    blockers: List[str] = []
    if failed:
        blockers.append(f"{failed} dataset ساخته نشد.")
    if ready < len(results):
        blockers.append(f"فقط {ready}/{len(results)} dataset به وضعیت Replay Ready رسید.")
    warnings = [
        "Historical OHLCV به‌تنهایی خبرها و داده‌های مشتقه تاریخی را بازسازی نمی‌کند.",
        "Market Replay باید با حالت replay-safe اجرا شود تا Historical Edge و Learning Override آینده وارد گذشته نشوند.",
    ]
    report = HistoricalDataBuildReport(
        run_id=run_id,
        version=VERSION,
        started_utc=started,
        finished_utc=utc_now_iso(),
        requested_symbols=len(request.symbols),
        completed_symbols=completed,
        failed_symbols=failed,
        total_rows=sum(item.rows for item in results),
        ready_datasets=ready,
        partial_datasets=partial,
        results=results,
        blockers=blockers,
        warnings=warnings,
    )
    report_dir = Path(DEFAULT_REPORT_DIR)
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{run_id}.json"
    report_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return report


def scan_historical_data(
    *,
    symbols: Sequence[str],
    timeframe: str,
    years: float = 3.0,
    data_dir: Path | str = DEFAULT_DATA_DIR,
    start_utc: str = "",
    end_utc: str = "",
) -> HistoricalDataBuildReport:
    request = HistoricalDataRequest(
        symbols=list(symbols),
        timeframe=timeframe,
        years=years,
        start_utc=start_utc,
        end_utc=end_utc,
        data_dir=str(data_dir),
    )
    start, end = resolve_range(request)
    results: List[HistoricalDatasetResult] = []
    for symbol in symbols:
        path = dataset_path(symbol, timeframe, data_dir)
        if not path.exists():
            results.append(HistoricalDatasetResult(
                symbol=symbol,
                timeframe=timeframe,
                ok=False,
                dataset_path=str(path),
                error="Dataset file does not exist.",
            ))
            continue
        try:
            frame = load_history(symbol, timeframe, data_dir)
            provider = str(frame["provider"].dropna().iloc[-1]) if len(frame) and "provider" in frame else "unknown"
            quality = evaluate_quality(
                frame,
                symbol=symbol,
                timeframe=timeframe,
                provider=provider,
                requested_start=floor_datetime_to_timeframe(start, timeframe),
                requested_end=floor_datetime_to_timeframe(end, timeframe),
            )
            results.append(HistoricalDatasetResult(
                symbol=symbol,
                timeframe=timeframe,
                ok=quality.readiness_status in {"REPLAY_READY", "REPLAY_READY_WITH_WARNINGS", "PARTIAL_HISTORY"},
                provider=provider,
                dataset_path=str(path),
                manifest_path=str(manifest_path(symbol, timeframe, data_dir)),
                rows=len(frame),
                used_cache=True,
                quality=quality,
            ))
        except Exception as exc:
            results.append(HistoricalDatasetResult(
                symbol=symbol,
                timeframe=timeframe,
                ok=False,
                dataset_path=str(path),
                error=f"{type(exc).__name__}: {exc}",
            ))

    completed = sum(1 for item in results if item.ok)
    ready = sum(1 for item in results if item.quality and item.quality.readiness_status.startswith("REPLAY_READY"))
    partial = sum(1 for item in results if item.quality and item.quality.readiness_status == "PARTIAL_HISTORY")
    failed = len(results) - completed
    blockers = []
    if failed:
        blockers.append(f"{failed} historical dataset missing or invalid.")
    if ready < len(results):
        blockers.append(f"Replay-ready coverage کامل نیست: {ready}/{len(results)}")
    return HistoricalDataBuildReport(
        run_id="historical_data_status",
        version=VERSION,
        started_utc=utc_now_iso(),
        finished_utc=utc_now_iso(),
        requested_symbols=len(results),
        completed_symbols=completed,
        failed_symbols=failed,
        total_rows=sum(item.rows for item in results),
        ready_datasets=ready,
        partial_datasets=partial,
        results=results,
        blockers=blockers,
        warnings=["Status scan فقط فایل‌های محلی را بررسی می‌کند و هیچ fetch اینترنتی انجام نمی‌دهد."],
    )


def format_historical_data_console(report: HistoricalDataBuildReport, compact: bool = False) -> str:
    lines = [
        "=" * 110,
        f"📚 Freakto Historical Data Store {VERSION}",
        "=" * 110,
        f"Run ID                 : {report.run_id}",
        f"Datasets Ready/Total   : {report.ready_datasets} / {report.requested_symbols}",
        f"Completed / Failed     : {report.completed_symbols} / {report.failed_symbols}",
        f"Total Rows             : {report.total_rows}",
        f"Partial Datasets       : {report.partial_datasets}",
    ]
    if report.results:
        lines.extend(["", "Datasets:"])
        for result in report.results:
            quality = result.quality
            if quality:
                lines.append(
                    f"- {result.symbol} {result.timeframe} | {result.provider or '-'} | "
                    f"rows={result.rows} coverage={quality.coverage_pct:.2f}% gaps={quality.gap_count} | "
                    f"{quality.readiness_status}"
                )
                if not compact and quality.warnings:
                    for warning in quality.warnings[:4]:
                        lines.append(f"  ⚠️ {warning}")
            else:
                lines.append(f"- {result.symbol} {result.timeframe} | FAILED | {result.error}")
    if report.blockers:
        lines.extend(["", "Blockers:"])
        lines.extend(f"⛔ {item}" for item in report.blockers)
    if report.warnings:
        lines.extend(["", "Warnings:"])
        lines.extend(f"⚠️ {item}" for item in report.warnings)
    lines.append("=" * 110)
    return "\n".join(lines)
