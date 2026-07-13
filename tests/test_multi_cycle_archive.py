from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd
import pytest

from engine.multi_cycle_archive import (
    ArchiveWindow,
    MultiCycleArchiveConfig,
    build_dataset_manifest,
    resolve_archive_windows,
    resolve_development_cutoff,
    run_multi_cycle_archive,
    validate_archive_separation,
    verify_archive_manifest,
)


def market_frame(start="2020-01-01", periods=30, provider="kucoin"):
    timestamps = pd.date_range(start, periods=periods, freq="4h", tz="UTC")
    close = pd.Series(range(100, 100 + periods), dtype=float)
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": close,
            "high": close + 2,
            "low": close - 2,
            "close": close + 1,
            "volume": 1000.0,
            "provider": provider,
        }
    )


def config_for(tmp_path: Path, **kwargs):
    defaults = dict(
        archive_root=str(tmp_path / "archive"),
        output_dir=str(tmp_path / "logs"),
        source_data_dir=str(tmp_path / "source"),
        fresh_freeze_dir=str(tmp_path / "freeze"),
        development_cutoff_utc="2025-01-01T00:00:00Z",
        symbols=["BTC/USDT"],
        windows=["3Y", "5Y", "FULL"],
    )
    defaults.update(kwargs)
    return MultiCycleArchiveConfig(**defaults)


def test_explicit_cutoff_wins(tmp_path):
    config = config_for(tmp_path, development_cutoff_utc="2026-07-09T12:00:00Z")
    assert resolve_development_cutoff(config) == "2026-07-09T12:00:00+00:00"


def test_cutoff_loaded_from_fresh_freeze_manifest(tmp_path):
    freeze = tmp_path / "freeze"
    freeze.mkdir()
    (freeze / "development_manifest.json").write_text(
        json.dumps({"development_cutoff_utc": "2026-07-09T12:00:00Z"}), encoding="utf-8"
    )
    config = config_for(tmp_path, development_cutoff_utc="")
    assert resolve_development_cutoff(config).startswith("2026-07-09T12:00:00")


def test_resolve_windows_uses_same_frozen_end(tmp_path):
    config = config_for(tmp_path)
    windows = resolve_archive_windows(config, "2025-01-01T00:00:00Z")
    assert [window.name for window in windows] == ["3Y", "5Y", "FULL"]
    assert len({window.end_utc for window in windows}) == 1
    assert pd.Timestamp(windows[1].start_utc) < pd.Timestamp(windows[0].start_utc)
    assert pd.Timestamp(windows[2].start_utc) < pd.Timestamp(windows[1].start_utc)


def test_archive_must_be_separate_from_source_and_freeze(tmp_path):
    config = config_for(tmp_path, archive_root=str(tmp_path / "source" / "archive"))
    with pytest.raises(ValueError):
        validate_archive_separation(config)
    config = config_for(tmp_path, archive_root=str(tmp_path / "freeze" / "archive"))
    with pytest.raises(ValueError):
        validate_archive_separation(config)


def test_manifest_filters_post_cutoff_and_hash_verifies(tmp_path):
    config = config_for(tmp_path, development_cutoff_utc="2020-01-03T00:00:00Z")
    window = ArchiveWindow("FULL", "2017-01-01T00:00:00+00:00", "2020-01-03T00:00:00+00:00", None)
    frame = market_frame(periods=20)
    manifest = build_dataset_manifest(frame, config=config, window=window, symbol="BTC/USDT")
    saved = pd.read_csv(manifest.archive_file, compression="gzip")
    assert pd.to_datetime(saved["timestamp"], utc=True).max() <= pd.Timestamp(window.end_utc)
    assert verify_archive_manifest(asdict(manifest)) == []
    assert len(manifest.sha256) == 64


def test_provider_mixing_is_fail_closed(tmp_path):
    config = config_for(tmp_path, development_cutoff_utc="2020-01-10T00:00:00Z")
    window = ArchiveWindow("FULL", "2017-01-01T00:00:00+00:00", "2020-01-10T00:00:00+00:00", None)
    frame = market_frame(periods=10)
    frame.loc[frame.index[-1], "provider"] = "okx"
    manifest = build_dataset_manifest(frame, config=config, window=window, symbol="BTC/USDT")
    assert not manifest.provider_consistent
    assert any("Provider mixing" in blocker for blocker in manifest.blockers)


def test_listing_boundary_is_recorded_not_silently_filled(tmp_path):
    config = config_for(tmp_path, development_cutoff_utc="2021-01-01T00:00:00Z", listing_boundary_tolerance_days=30)
    window = ArchiveWindow("FULL", "2017-01-01T00:00:00+00:00", "2021-01-01T00:00:00+00:00", None)
    manifest = build_dataset_manifest(
        market_frame(start="2020-01-01", periods=20),
        config=config,
        window=window,
        symbol="SOL/USDT",
    )
    assert manifest.listing_boundary_detected
    assert manifest.warnings


def test_tampered_archive_fails_hash_verification(tmp_path):
    config = config_for(tmp_path, development_cutoff_utc="2020-01-10T00:00:00Z")
    window = ArchiveWindow("3Y", "2017-01-01T00:00:00+00:00", "2020-01-10T00:00:00+00:00", 3.0)
    manifest = build_dataset_manifest(market_frame(periods=10), config=config, window=window, symbol="BTC/USDT")
    path = Path(manifest.archive_file)
    path.write_bytes(path.read_bytes() + b"tamper")
    assert any("hash mismatch" in blocker.lower() for blocker in verify_archive_manifest(asdict(manifest)))


def test_empty_existing_archive_reports_ready_to_build(tmp_path):
    config = config_for(tmp_path, build_archives=False, run_replays=False)
    report = run_multi_cycle_archive(config)
    assert report.status == "PARTIAL_ARCHIVE"
    assert report.promotion_applied is False
    assert report.paper_live_enabled is False


def test_missing_full_symbol_returns_partial_full_history_and_replays_available_only(tmp_path, monkeypatch):
    import engine.multi_cycle_archive as module

    config = config_for(
        tmp_path,
        symbols=["BTC/USDT", "SOL/USDT"],
        windows=["FULL"],
        build_archives=True,
        run_replays=True,
    )
    window = ArchiveWindow("FULL", "2017-01-01T00:00:00+00:00", "2025-01-01T00:00:00+00:00", None)
    manifest = build_dataset_manifest(
        market_frame(start="2020-01-01", periods=50),
        config=config,
        window=window,
        symbol="BTC/USDT",
    )

    monkeypatch.setattr(module, "resolve_archive_windows", lambda *_: [window])
    monkeypatch.setattr(
        module,
        "_build_window",
        lambda *_args, **_kwargs: (
            [manifest],
            [{
                "window": "FULL",
                "symbol": "SOL/USDT",
                "timeframe": "4h",
                "status": "NO_USABLE_PROVIDER_HISTORY",
                "error": "no data",
                "attempts": [],
                "listing_probe_count": 4,
            }],
        ),
    )
    observed = {}

    def fake_replay(_config, _window, *, symbols=None):
        observed["symbols"] = list(symbols or [])
        rows = pd.DataFrame({
            "side": ["LONG"],
            "score": [80],
            "candle_timestamp": [pd.Timestamp("2024-01-01", tz="UTC")],
        })
        return ({
            "window": "FULL",
            "run_id": "test",
            "ok": True,
            "status": "COMPLETE",
            "rows": 1,
            "directional_rows": 1,
            "leakage_audit_status": "PASSED_NO_LOOKAHEAD",
        }, rows)

    monkeypatch.setattr(module, "_replay_window", fake_replay)
    report = run_multi_cycle_archive(config)

    assert report.status == "PARTIAL_FULL_HISTORY"
    assert report.blockers == []
    assert observed["symbols"] == ["BTC/USDT"]
    assert report.replay_runs[0]["missing_symbols"] == ["SOL/USDT"]
    assert report.build_issues[0]["symbol"] == "SOL/USDT"


def test_empty_replay_removes_stale_output(tmp_path):
    import engine.multi_cycle_archive as module

    config = config_for(tmp_path)
    stale = Path(config.output_dir) / "replays" / "full_replay.csv.gz"
    stale.parent.mkdir(parents=True)
    stale.write_bytes(b"old")

    output = module._write_replay_rows(config, "FULL", pd.DataFrame())

    assert output == ""
    assert not stale.exists()
