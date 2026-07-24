"""Atomic persistence of validated adapter output in the legacy replay layout."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from freakto.market_data import OHLCV_COLUMNS, inspect_ohlcv
from freakto.markets.config import MarketConfig


@dataclass(frozen=True)
class DatasetManifest:
    schema_version: str
    asset_class: str
    symbol: str
    timeframe: str
    provider: str
    source_symbol: str
    price_basis: str
    volume_semantics: str
    session_calendar: str
    rows: int
    first_timestamp_utc: str
    last_timestamp_utc: str
    data_sha256: str
    created_utc: str
    research_only: bool = True


def _symbol_slug(symbol: str) -> str:
    return str(symbol).replace("/", "_").replace(":", "_").replace(" ", "").upper()


def _data_bytes(frame: pd.DataFrame) -> bytes:
    serialised = frame.loc[:, [*OHLCV_COLUMNS, "provider"]].copy()
    serialised["timestamp"] = pd.to_datetime(
        serialised["timestamp"], utc=True
    ).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return serialised.to_csv(index=False, lineterminator="\n").encode("utf-8")


def persist_replay_dataset(
    frame: pd.DataFrame,
    *,
    symbol: str,
    timeframe: str,
    config: MarketConfig,
    data_dir: str | Path = Path("data") / "market_replay",
    now: datetime | None = None,
) -> tuple[Path, Path, DatasetManifest]:
    """Persist a new dataset only; existing replay data is never overwritten."""
    config.assert_safe()
    canonical_symbol = str(symbol).strip().upper()
    if canonical_symbol not in config.symbols:
        raise ValueError(f"Symbol {canonical_symbol} is not allowed by {config.asset_class}.")
    report = inspect_ohlcv(frame, timeframe, now=now, require_closed=True)
    if not report.ok:
        codes = ", ".join(issue.code for issue in report.issues if issue.severity == "ERROR")
        raise ValueError(f"Dataset contract failed: {codes}")

    root = Path(data_dir) / str(timeframe)
    dataset_path = root / f"{_symbol_slug(canonical_symbol)}.csv.gz"
    manifest_path = root / f"{_symbol_slug(canonical_symbol)}.adapter.json"
    if dataset_path.exists() or manifest_path.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing replay dataset or manifest for {canonical_symbol}."
        )

    provider_values = frame.get("provider", pd.Series(dtype=str)).dropna().astype(str).unique()
    if len(provider_values) != 1 or provider_values[0] != config.provider:
        raise ValueError("Dataset must contain exactly the configured provider.")

    raw = _data_bytes(frame)
    manifest = DatasetManifest(
        schema_version=config.schema_version,
        asset_class=config.asset_class,
        symbol=canonical_symbol,
        timeframe=str(timeframe),
        provider=config.provider,
        source_symbol=canonical_symbol,
        price_basis=config.price_basis,
        volume_semantics=config.volume_semantics,
        session_calendar=config.session_calendar,
        rows=len(frame),
        first_timestamp_utc=report.first_timestamp_utc or "",
        last_timestamp_utc=report.last_timestamp_utc or "",
        data_sha256=hashlib.sha256(raw).hexdigest(),
        created_utc=(now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(),
    )

    root.mkdir(parents=True, exist_ok=True)
    dataset_fd, dataset_temp_name = tempfile.mkstemp(
        prefix=f".{dataset_path.stem}.", suffix=".tmp.gz", dir=root
    )
    manifest_fd, manifest_temp_name = tempfile.mkstemp(
        prefix=f".{manifest_path.stem}.", suffix=".tmp", dir=root
    )
    os.close(dataset_fd)
    os.close(manifest_fd)
    dataset_temp = Path(dataset_temp_name)
    manifest_temp = Path(manifest_temp_name)
    try:
        serialised = frame.loc[:, [*OHLCV_COLUMNS, "provider"]].copy()
        serialised["timestamp"] = pd.to_datetime(
            serialised["timestamp"], utc=True
        ).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        serialised.to_csv(
            dataset_temp,
            index=False,
            compression="gzip",
            encoding="utf-8",
            lineterminator="\n",
        )
        manifest_temp.write_text(
            json.dumps(asdict(manifest), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        dataset_temp.replace(dataset_path)
        manifest_temp.replace(manifest_path)
    finally:
        dataset_temp.unlink(missing_ok=True)
        manifest_temp.unlink(missing_ok=True)
    return dataset_path, manifest_path, manifest
