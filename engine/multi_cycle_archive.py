"""Multi-cycle historical archive builder for Freakto research.

This module creates immutable, provider-explicit development archives without
modifying the canonical ``data/market_replay`` cache or the Fresh OOS freeze.
Every archive is capped at the frozen development cutoff and receives hashes,
coverage metadata and listing-boundary diagnostics.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import pandas as pd

from engine.historical_data_store import (
    DEFAULT_EXCHANGE_ORDER,
    HistoricalDataRequest,
    build_historical_data,
    dataset_path,
    load_history,
    parse_utc,
    symbol_slug,
    timeframe_to_milliseconds,
)

VERSION = "2.1.0"
DEFAULT_ARCHIVE_ROOT = Path("data") / "multi_cycle_archive_v2"
DEFAULT_OUTPUT_DIR = Path("logs") / "multi_cycle_archive_v2"
DEFAULT_FRESH_FREEZE_DIR = Path("logs") / "fresh_oos_v2" / "development_freeze"
DEFAULT_FULL_HISTORY_START_UTC = "2017-01-01T00:00:00+00:00"
WINDOW_ORDER = ("3Y", "5Y", "FULL")


@dataclass(frozen=True)
class ArchiveWindow:
    name: str
    start_utc: str
    end_utc: str
    years: Optional[float]


@dataclass
class MultiCycleArchiveConfig:
    symbols: List[str] = field(default_factory=lambda: ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
    timeframe: str = "4h"
    archive_root: str = str(DEFAULT_ARCHIVE_ROOT)
    output_dir: str = str(DEFAULT_OUTPUT_DIR)
    source_data_dir: str = str(Path("data") / "market_replay")
    fresh_freeze_dir: str = str(DEFAULT_FRESH_FREEZE_DIR)
    development_cutoff_utc: str = ""
    full_history_start_utc: str = DEFAULT_FULL_HISTORY_START_UTC
    windows: List[str] = field(default_factory=lambda: list(WINDOW_ORDER))
    exchange: str = "auto"
    exchange_order: List[str] = field(default_factory=lambda: list(DEFAULT_EXCHANGE_ORDER))
    batch_limit: int = 1000
    max_retries: int = 3
    retry_backoff_seconds: float = 1.5
    force_refresh: bool = False
    build_archives: bool = False
    run_replays: bool = False
    replay_step: int = 1
    fixed_score_threshold: float = 70.0
    strict_provider_consistency: bool = True
    listing_boundary_tolerance_days: int = 30
    full_history_discovery: bool = True
    listing_probe_days: int = 90
    max_listing_probes: int = 80


@dataclass
class ArchiveDatasetManifest:
    version: str
    dataset_version_id: str
    window: str
    symbol: str
    timeframe: str
    provider: str
    requested_start_utc: str
    requested_end_utc: str
    actual_start_utc: str
    actual_end_utc: str
    rows: int
    coverage_pct: float
    gap_count: int
    listing_boundary_detected: bool
    provider_consistent: bool
    source_file: str
    archive_file: str
    sha256: str
    generated_utc: str
    listing_probe_count: int = 0
    listing_boundary_source: str = "REQUEST_START_OR_PROVIDER_RESPONSE"
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class MultiCycleArchiveReport:
    status: str
    mode: str
    version: str
    development_cutoff_utc: str
    archive_root: str
    windows: List[Dict[str, Any]]
    datasets: List[Dict[str, Any]]
    replay_runs: List[Dict[str, Any]]
    build_issues: List[Dict[str, Any]]
    blockers: List[str]
    warnings: List[str]
    promotion_applied: bool = False
    paper_live_enabled: bool = False


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _utc_timestamp(value: Any) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts


def _iso(value: Any) -> str:
    return _utc_timestamp(value).isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_id(parts: Iterable[Any], length: int = 20) -> str:
    raw = "|".join(str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:length]


def _manifest_candidates(freeze_dir: Path) -> List[Path]:
    return [
        freeze_dir / "development_freeze_manifest.json",
        freeze_dir / "development_manifest.json",
        freeze_dir / "manifest.json",
    ]


def resolve_development_cutoff(config: MultiCycleArchiveConfig) -> str:
    """Resolve the immutable development cutoff, preferring an explicit value."""
    if config.development_cutoff_utc:
        return _iso(config.development_cutoff_utc)
    freeze_dir = Path(config.fresh_freeze_dir)
    for path in _manifest_candidates(freeze_dir):
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for key in ("development_cutoff_utc", "cutoff_utc", "max_timestamp_utc"):
            if payload.get(key):
                return _iso(payload[key])
    # Search nested JSON manifests as a compatibility fallback.
    if freeze_dir.exists():
        for path in sorted(freeze_dir.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            for key in ("development_cutoff_utc", "cutoff_utc", "max_timestamp_utc"):
                if payload.get(key):
                    return _iso(payload[key])
    raise FileNotFoundError(
        "Development cutoff is unavailable. Pass --cutoff or keep the Fresh OOS development freeze manifest."
    )


def resolve_archive_windows(config: MultiCycleArchiveConfig, cutoff_utc: str) -> List[ArchiveWindow]:
    cutoff = _utc_timestamp(cutoff_utc)
    requested = []
    for name in config.windows:
        key = str(name).strip().upper()
        if key and key not in requested:
            requested.append(key)
    unknown = sorted(set(requested) - set(WINDOW_ORDER))
    if unknown:
        raise ValueError(f"Unsupported archive windows: {unknown}")
    windows: List[ArchiveWindow] = []
    for key in WINDOW_ORDER:
        if key not in requested:
            continue
        if key == "3Y":
            start = cutoff - pd.Timedelta(days=round(3 * 365.25))
            years: Optional[float] = 3.0
        elif key == "5Y":
            start = cutoff - pd.Timedelta(days=round(5 * 365.25))
            years = 5.0
        else:
            start = _utc_timestamp(config.full_history_start_utc)
            years = None
        if start >= cutoff:
            raise ValueError(f"Archive start for {key} must be before the development cutoff")
        windows.append(ArchiveWindow(key, start.isoformat(), cutoff.isoformat(), years))
    return windows


def archive_window_dir(config: MultiCycleArchiveConfig, window: str) -> Path:
    return Path(config.archive_root) / str(window).upper()


def validate_archive_separation(config: MultiCycleArchiveConfig) -> None:
    source = Path(config.source_data_dir).resolve()
    archive = Path(config.archive_root).resolve()
    if source == archive or source in archive.parents or archive in source.parents:
        raise ValueError("archive_root and source_data_dir must be separate to protect Fresh OOS and canonical cache")
    freeze = Path(config.fresh_freeze_dir).resolve()
    if archive == freeze or archive in freeze.parents or freeze in archive.parents:
        raise ValueError("archive_root must be separate from the Fresh OOS development freeze")


def _provider_values(frame: pd.DataFrame) -> List[str]:
    if "provider" not in frame.columns:
        return []
    values = frame["provider"].dropna().astype(str).str.strip()
    return sorted(value for value in values.unique().tolist() if value)


def _filtered_to_cutoff(frame: pd.DataFrame, cutoff_utc: str) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame(columns=list(frame.columns) if isinstance(frame, pd.DataFrame) else [])
    work = frame.copy()
    work["timestamp"] = pd.to_datetime(work["timestamp"], utc=True, errors="coerce")
    cutoff = _utc_timestamp(cutoff_utc)
    work = work.dropna(subset=["timestamp"])
    work = work[work["timestamp"] <= cutoff]
    return work.sort_values("timestamp").drop_duplicates("timestamp", keep="last").reset_index(drop=True)


def _write_archive_snapshot(
    frame: pd.DataFrame,
    *,
    config: MultiCycleArchiveConfig,
    window: ArchiveWindow,
    symbol: str,
) -> Path:
    root = archive_window_dir(config, window.name)
    path = dataset_path(symbol, config.timeframe, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    serialised = frame.copy()
    serialised["timestamp"] = pd.to_datetime(serialised["timestamp"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    serialised.to_csv(path, index=False, compression="gzip", encoding="utf-8")
    return path


def build_dataset_manifest(
    frame: pd.DataFrame,
    *,
    config: MultiCycleArchiveConfig,
    window: ArchiveWindow,
    symbol: str,
    provider_hint: str = "",
    coverage_pct: float = 0.0,
    gap_count: int = 0,
    source_file: str = "",
) -> ArchiveDatasetManifest:
    if frame is None or frame.empty:
        raise ValueError(f"Cannot manifest empty archive: {window.name} {symbol} {config.timeframe}")
    work = _filtered_to_cutoff(frame, window.end_utc)
    if work.empty:
        raise ValueError(f"Archive contains no rows at or before cutoff: {window.name} {symbol}")
    providers = _provider_values(work)
    provider = providers[0] if len(providers) == 1 else str(provider_hint or "unknown")
    provider_consistent = len(providers) <= 1
    actual_start = _utc_timestamp(work["timestamp"].iloc[0])
    actual_end = _utc_timestamp(work["timestamp"].iloc[-1])
    requested_start = _utc_timestamp(window.start_utc)
    requested_end = _utc_timestamp(window.end_utc)
    blockers: List[str] = []
    warnings: List[str] = []
    if actual_end > requested_end:
        blockers.append("Archive contains rows after the frozen development cutoff.")
    if config.strict_provider_consistency and not provider_consistent:
        blockers.append(f"Provider mixing detected: {providers}")
    listing_boundary = actual_start > requested_start + pd.Timedelta(days=max(0, config.listing_boundary_tolerance_days))
    if listing_boundary:
        warnings.append(
            f"Actual history starts at {actual_start.isoformat()}, after requested start; this is treated as a listing/provider boundary."
        )
    archive_file = _write_archive_snapshot(work, config=config, window=window, symbol=symbol)
    digest = _sha256_file(archive_file)
    dataset_version_id = _stable_id(
        [VERSION, window.name, symbol, config.timeframe, provider, actual_start.isoformat(), actual_end.isoformat(), len(work), digest]
    )
    manifest = ArchiveDatasetManifest(
        version=VERSION,
        dataset_version_id=dataset_version_id,
        window=window.name,
        symbol=symbol,
        timeframe=config.timeframe,
        provider=provider,
        requested_start_utc=requested_start.isoformat(),
        requested_end_utc=requested_end.isoformat(),
        actual_start_utc=actual_start.isoformat(),
        actual_end_utc=actual_end.isoformat(),
        rows=int(len(work)),
        coverage_pct=float(coverage_pct),
        gap_count=int(gap_count),
        listing_boundary_detected=bool(listing_boundary),
        provider_consistent=bool(provider_consistent),
        source_file=str(source_file),
        archive_file=str(archive_file),
        sha256=digest,
        generated_utc=utc_now_iso(),
        blockers=blockers,
        warnings=warnings,
    )
    manifest_path = archive_file.with_suffix(archive_file.suffix + ".archive_manifest.json")
    manifest_path.write_text(json.dumps(asdict(manifest), ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def verify_archive_manifest(manifest: Mapping[str, Any]) -> List[str]:
    blockers: List[str] = []
    path = Path(str(manifest.get("archive_file", "")))
    if not path.exists():
        return [f"Archive file is missing: {path}"]
    expected = str(manifest.get("sha256", ""))
    actual = _sha256_file(path)
    if not expected or actual != expected:
        blockers.append(f"Archive hash mismatch: {path}")
    try:
        frame = pd.read_csv(path, compression="gzip")
        timestamps = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
        cutoff = _utc_timestamp(manifest.get("requested_end_utc"))
        if timestamps.notna().any() and timestamps.max() > cutoff:
            blockers.append(f"Archive contains post-cutoff rows: {path}")
        providers = sorted(frame.get("provider", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
        if len(providers) > 1:
            blockers.append(f"Archive mixes providers {providers}: {path}")
    except Exception as exc:
        blockers.append(f"Archive verification failed for {path}: {type(exc).__name__}: {exc}")
    return blockers


def _quality_fields(result: Any) -> Tuple[float, int]:
    quality = getattr(result, "quality", None)
    return (
        float(getattr(quality, "coverage_pct", 0.0) or 0.0),
        int(getattr(quality, "gap_count", 0) or 0),
    )


def _build_window(
    config: MultiCycleArchiveConfig,
    window: ArchiveWindow,
    *,
    exchange_factory: Optional[Callable[[str], Any]] = None,
) -> Tuple[List[ArchiveDatasetManifest], List[Dict[str, Any]]]:
    staging_root = Path(config.archive_root) / "_staging" / window.name
    request = HistoricalDataRequest(
        symbols=list(config.symbols),
        timeframe=config.timeframe,
        start_utc=window.start_utc,
        end_utc=window.end_utc,
        exchange=config.exchange,
        exchange_order=list(config.exchange_order),
        batch_limit=config.batch_limit,
        max_retries=config.max_retries,
        retry_backoff_seconds=config.retry_backoff_seconds,
        min_acceptable_coverage_pct=90.0,
        data_dir=str(staging_root),
        update_existing=True,
        force_refresh=config.force_refresh,
        discover_listing_boundary=bool(config.full_history_discovery and window.name == "FULL"),
        listing_probe_days=max(1, int(config.listing_probe_days)),
        max_listing_probes=max(1, int(config.max_listing_probes)),
    )
    report = build_historical_data(request, exchange_factory=exchange_factory)
    manifests: List[ArchiveDatasetManifest] = []
    issues: List[Dict[str, Any]] = []
    for result in report.results:
        if not result.ok or not result.dataset_path:
            issues.append({
                "window": window.name,
                "symbol": result.symbol,
                "timeframe": config.timeframe,
                "status": "NO_USABLE_PROVIDER_HISTORY",
                "error": result.error or "Historical archive build failed.",
                "attempts": result.attempts,
                "listing_probe_count": int(getattr(result, "listing_probe_count", 0) or 0),
            })
            continue
        frame = load_history(result.symbol, config.timeframe, staging_root)
        frame = _filtered_to_cutoff(frame, window.end_utc)
        coverage, gaps = _quality_fields(result)
        manifest = build_dataset_manifest(
            frame,
            config=config,
            window=window,
            symbol=result.symbol,
            provider_hint=result.provider,
            coverage_pct=coverage,
            gap_count=gaps,
            source_file=result.dataset_path,
        )
        manifest.listing_probe_count = int(getattr(result, "listing_probe_count", 0) or 0)
        if bool(getattr(result, "listing_boundary_discovered", False)):
            manifest.listing_boundary_source = "DISCOVERED_BY_EMPTY_RANGE_PROBING"
            manifest.warnings.append(
                f"Listing boundary discovered after {manifest.listing_probe_count} provider probes."
            )
        elif manifest.listing_boundary_detected:
            manifest.listing_boundary_source = "PROVIDER_FIRST_AVAILABLE_CANDLE"
        if manifest.listing_probe_count or manifest.listing_boundary_detected:
            manifest_path = Path(manifest.archive_file).with_suffix(
                Path(manifest.archive_file).suffix + ".archive_manifest.json"
            )
            manifest_path.write_text(
                json.dumps(asdict(manifest), ensure_ascii=False, indent=2), encoding="utf-8"
            )
        manifests.append(manifest)
    return manifests, issues

def _load_existing_manifests(config: MultiCycleArchiveConfig, windows: Sequence[ArchiveWindow]) -> List[ArchiveDatasetManifest]:
    manifests: List[ArchiveDatasetManifest] = []
    for window in windows:
        root = archive_window_dir(config, window.name) / config.timeframe
        for path in sorted(root.glob("*.archive_manifest.json")):
            try:
                manifests.append(ArchiveDatasetManifest(**json.loads(path.read_text(encoding="utf-8"))))
            except Exception:
                continue
    return manifests


def _replay_window(
    config: MultiCycleArchiveConfig,
    window: ArchiveWindow,
    *,
    symbols: Optional[Sequence[str]] = None,
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    try:
        from engine.market_replay import MarketReplayConfig, run_market_replay  # type: ignore
    except Exception as exc:
        raise RuntimeError(f"Market Replay is unavailable: {exc}") from exc
    replay_config = MarketReplayConfig(
        symbols=list(symbols or config.symbols),
        timeframe=config.timeframe,
        start_utc=window.start_utc,
        end_utc=window.end_utc,
        data_dir=str(archive_window_dir(config, window.name)),
        step=max(1, int(config.replay_step)),
        include_neutral=True,
        strict_leakage_audit=True,
        source=f"MULTI_CYCLE_{window.name}",
    )
    run, summary, rows = run_market_replay(replay_config, save=False)
    payload = {
        "window": window.name,
        "run_id": getattr(run, "run_id", ""),
        "ok": bool(getattr(run, "ok", False)),
        "status": getattr(summary, "status", ""),
        "rows": int(len(rows)) if isinstance(rows, pd.DataFrame) else 0,
        "directional_rows": int(rows.get("side", pd.Series(dtype=str)).astype(str).isin(["LONG", "SHORT"]).sum())
        if isinstance(rows, pd.DataFrame)
        else 0,
        "leakage_audit_status": getattr(summary, "leakage_audit_status", ""),
    }
    return payload, rows if isinstance(rows, pd.DataFrame) else pd.DataFrame()


def _write_replay_rows(config: MultiCycleArchiveConfig, window: str, rows: pd.DataFrame) -> str:
    path = Path(config.output_dir) / "replays" / f"{window.lower()}_replay.csv.gz"
    if rows is None or rows.empty:
        if path.exists():
            path.unlink()
        return ""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows.to_csv(path, index=False, compression="gzip", encoding="utf-8")
    return str(path)


def run_multi_cycle_archive(
    config: MultiCycleArchiveConfig,
    *,
    exchange_factory: Optional[Callable[[str], Any]] = None,
) -> MultiCycleArchiveReport:
    validate_archive_separation(config)
    cutoff = resolve_development_cutoff(config)
    windows = resolve_archive_windows(config, cutoff)
    manifests: List[ArchiveDatasetManifest] = []
    build_issues: List[Dict[str, Any]] = []
    blockers: List[str] = []
    warnings: List[str] = []

    if config.build_archives:
        for window in windows:
            window_manifests, window_issues = _build_window(
                config, window, exchange_factory=exchange_factory
            )
            manifests.extend(window_manifests)
            build_issues.extend(window_issues)
    else:
        manifests = _load_existing_manifests(config, windows)

    expected = {(window.name, symbol) for window in windows for symbol in config.symbols}
    observed = {(item.window, item.symbol) for item in manifests}
    missing = sorted(expected - observed)
    if missing:
        warnings.append(f"Missing archive datasets: {missing}")
    for issue in build_issues:
        warnings.append(
            f"{issue.get('window')} {issue.get('symbol')}: {issue.get('error')}"
        )

    verified_keys = set()
    for manifest in manifests:
        blockers.extend(manifest.blockers)
        warnings.extend(manifest.warnings)
        verification = verify_archive_manifest(asdict(manifest))
        blockers.extend(verification)
        if not manifest.blockers and not verification:
            verified_keys.add((manifest.window, manifest.symbol))

    replay_runs: List[Dict[str, Any]] = []
    if config.run_replays and not blockers:
        for window in windows:
            available_symbols = [
                symbol for symbol in config.symbols
                if (window.name, symbol) in verified_keys
            ]
            if not available_symbols:
                _write_replay_rows(config, window.name, pd.DataFrame())
                replay_runs.append({
                    "window": window.name,
                    "run_id": "",
                    "ok": False,
                    "status": "SKIPPED_NO_ARCHIVE_DATA",
                    "rows": 0,
                    "directional_rows": 0,
                    "symbols_requested": list(config.symbols),
                    "symbols_replayed": [],
                    "missing_symbols": list(config.symbols),
                    "leakage_audit_status": "NOT_RUN_NO_DATA",
                    "output_csv": "",
                })
                warnings.append(f"Replay skipped for {window.name}: no verified archive datasets.")
                continue
            try:
                payload, rows = _replay_window(config, window, symbols=available_symbols)
            except Exception as exc:
                _write_replay_rows(config, window.name, pd.DataFrame())
                blockers.append(
                    f"Replay failed for {window.name}: {type(exc).__name__}: {exc}"
                )
                replay_runs.append({
                    "window": window.name,
                    "run_id": "",
                    "ok": False,
                    "status": "FAILED_REPLAY_EXCEPTION",
                    "rows": 0,
                    "directional_rows": 0,
                    "symbols_requested": list(config.symbols),
                    "symbols_replayed": available_symbols,
                    "missing_symbols": [s for s in config.symbols if s not in available_symbols],
                    "leakage_audit_status": "FAILED_REPLAY_EXCEPTION",
                    "output_csv": "",
                })
                continue
            payload["symbols_requested"] = list(config.symbols)
            payload["symbols_replayed"] = available_symbols
            payload["missing_symbols"] = [s for s in config.symbols if s not in available_symbols]
            payload["output_csv"] = _write_replay_rows(config, window.name, rows)
            replay_runs.append(payload)
            if payload.get("leakage_audit_status") not in {"PASSED_NO_LOOKAHEAD", "PASSED"}:
                blockers.append(
                    f"Leakage audit did not pass for {window.name}: {payload.get('leakage_audit_status')}"
                )

    missing_full = [item for item in missing if item[0] == "FULL"]
    if blockers:
        status = "FAIL_CLOSED"
    elif (
        missing_full
        and manifests
        and any(window.name == "FULL" for window in windows)
    ):
        status = "PARTIAL_FULL_HISTORY"
    elif missing:
        status = "PARTIAL_ARCHIVE"
    elif config.run_replays:
        status = "COMPLETE_RESEARCH_ONLY"
    elif manifests:
        status = "ARCHIVE_READY"
    else:
        status = "READY_TO_BUILD"

    report = MultiCycleArchiveReport(
        status=status,
        mode="MULTI_CYCLE_DEVELOPMENT_ARCHIVE_ONLY",
        version=VERSION,
        development_cutoff_utc=cutoff,
        archive_root=str(Path(config.archive_root)),
        windows=[asdict(window) for window in windows],
        datasets=[asdict(item) for item in manifests],
        replay_runs=replay_runs,
        build_issues=build_issues,
        blockers=sorted(set(blockers)),
        warnings=sorted(set(warnings)),
        promotion_applied=False,
        paper_live_enabled=False,
    )
    output = Path(config.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "multi_cycle_archive_report.json").write_text(
        json.dumps(asdict(report), ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    dataset_rows = [asdict(item) for item in manifests]
    pd.DataFrame(dataset_rows).to_csv(output / "archive_dataset_manifest.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(build_issues).to_csv(output / "archive_build_issues.csv", index=False, encoding="utf-8-sig")
    return report

