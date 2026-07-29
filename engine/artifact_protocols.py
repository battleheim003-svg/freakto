"""Versioned artifact routing and frozen Global UTC split contracts.

Registry entries are definitions only: importing this module never creates
directories or selects the v3 candidate implicitly.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence, Tuple

import pandas as pd

from engine.model_contract import (
    DECISION_MODEL_VERSION,
    EXECUTION_MODEL_VERSION,
    FEATURE_SET_VERSION,
    SCORE_CALIBRATION_VERSION,
)


DEFAULT_ARTIFACT_SELECTOR = "v2-canonical"
GLOBAL_UTC_SELECTOR = "v3-global-utc-candidate"
GLOBAL_UTC_PROTOCOL = "global-utc-pooled-60-20-20-purge6-v1"
GLOBAL_UTC_PROFILE_ID = "full-btc-eth-sol-4h-cutoff-20260709-v1"
GLOBAL_UTC_SCHEMA_VERSION = "3.0.0"
GLOBAL_SPLIT_ASSIGNMENT_VERSION = "utc-boundary-assignment-v1"
GLOBAL_BOUNDARIES_STATUS = "GLOBAL_UTC_BOUNDARIES_FROZEN_BEFORE_HOLDOUT"
GLOBAL_TRAIN_END_UTC = "2023-01-20T12:00:00Z"
GLOBAL_VALIDATION_START_UTC = "2023-01-20T16:00:00Z"
GLOBAL_TEST_START_UTC = "2024-10-13T16:00:00Z"


@dataclass(frozen=True)
class ArtifactProtocolRoute:
    selector: str
    replay_root: Path
    event_root: Path
    cost_root: Path
    split_protocol: str
    split_profile: str
    canonical: bool


@dataclass(frozen=True)
class GlobalUtcSplitProfile:
    protocol_id: str = GLOBAL_UTC_PROTOCOL
    profile_id: str = GLOBAL_UTC_PROFILE_ID
    schema_version: str = GLOBAL_UTC_SCHEMA_VERSION
    frozen_status: str = GLOBAL_BOUNDARIES_STATUS
    window: str = "FULL"
    symbols: Tuple[str, ...] = ("BTC/USDT", "ETH/USDT", "SOL/USDT")
    timeframe: str = "4h"
    research_cutoff_utc: str = "2026-07-09T12:00:00Z"
    train_end_utc: str = GLOBAL_TRAIN_END_UTC
    validation_start_utc: str = GLOBAL_VALIDATION_START_UTC
    test_start_utc: str = GLOBAL_TEST_START_UTC
    raw_split_labels: Tuple[str, ...] = ("TRAIN_60", "VALIDATION_20", "TEST_20")
    purge_owner: str = "EVENT_PIPELINE"
    purge_applied: bool = False
    purge_timestamps: int = 6
    purge_unit: str = "unique UTC timestamps"
    split_assignment_version: str = GLOBAL_SPLIT_ASSIGNMENT_VERSION

    def validate(self) -> None:
        if self.protocol_id != GLOBAL_UTC_PROTOCOL:
            raise ValueError(f"GLOBAL_UTC_PROFILE_VIOLATION: unknown protocol {self.protocol_id}")
        if self.profile_id != GLOBAL_UTC_PROFILE_ID:
            raise ValueError(f"GLOBAL_UTC_PROFILE_VIOLATION: unknown profile {self.profile_id}")
        if self.schema_version != GLOBAL_UTC_SCHEMA_VERSION:
            raise ValueError("GLOBAL_UTC_PROFILE_VIOLATION: schema version mismatch")
        if self.frozen_status != GLOBAL_BOUNDARIES_STATUS:
            raise ValueError("GLOBAL_UTC_PROFILE_VIOLATION: boundaries are not frozen")
        if (
            self.train_end_utc,
            self.validation_start_utc,
            self.test_start_utc,
        ) != (
            GLOBAL_TRAIN_END_UTC,
            GLOBAL_VALIDATION_START_UTC,
            GLOBAL_TEST_START_UTC,
        ):
            raise ValueError("GLOBAL_UTC_PROFILE_VIOLATION: frozen boundary mutation")
        boundaries = [
            _strict_utc(self.train_end_utc, "train_end_utc"),
            _strict_utc(self.validation_start_utc, "validation_start_utc"),
            _strict_utc(self.test_start_utc, "test_start_utc"),
        ]
        if not boundaries[0] < boundaries[1] < boundaries[2]:
            raise ValueError("GLOBAL_UTC_PROFILE_VIOLATION: invalid boundary chronology")
        if self.purge_applied:
            raise ValueError("GLOBAL_UTC_PROFILE_VIOLATION: Stage 1 profile cannot own purge")
        if self.purge_owner != "EVENT_PIPELINE":
            raise ValueError("GLOBAL_UTC_PROFILE_VIOLATION: purge owner mismatch")
        if self.purge_timestamps != 6 or self.purge_unit != "unique UTC timestamps":
            raise ValueError("GLOBAL_UTC_PROFILE_VIOLATION: purge contract mismatch")


GLOBAL_UTC_PROFILE = GlobalUtcSplitProfile()

ARTIFACT_PROTOCOL_ROUTES: Dict[str, ArtifactProtocolRoute] = {
    DEFAULT_ARTIFACT_SELECTOR: ArtifactProtocolRoute(
        selector=DEFAULT_ARTIFACT_SELECTOR,
        replay_root=Path("logs") / "multi_cycle_archive_v2",
        event_root=Path("logs") / "event_opportunity_v2",
        cost_root=Path("logs") / "cost_gate_diagnostics",
        split_protocol="chronological-60-20-20-v1",
        split_profile="legacy-per-symbol-v2",
        canonical=True,
    ),
    GLOBAL_UTC_SELECTOR: ArtifactProtocolRoute(
        selector=GLOBAL_UTC_SELECTOR,
        replay_root=Path("logs") / "multi_cycle_archive_v3_global_utc",
        event_root=Path("logs") / "event_opportunity_v3_global_utc",
        cost_root=Path("logs") / "cost_gate_diagnostics_v3_global_utc",
        split_protocol=GLOBAL_UTC_PROTOCOL,
        split_profile=GLOBAL_UTC_PROFILE_ID,
        canonical=False,
    ),
}


def _strict_utc(value: Any, field: str = "timestamp") -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError(f"GLOBAL_UTC_PROFILE_VIOLATION: naive {field} is forbidden")
    return timestamp.tz_convert("UTC")


def resolve_artifact_route(selector: str = DEFAULT_ARTIFACT_SELECTOR) -> ArtifactProtocolRoute:
    normalized = str(selector or DEFAULT_ARTIFACT_SELECTOR).strip()
    route = ARTIFACT_PROTOCOL_ROUTES.get(normalized)
    if route is None:
        raise ValueError(f"ARTIFACT_SELECTOR_VIOLATION: unknown selector {normalized}")
    return route


def validate_global_utc_request(
    *,
    protocol_id: str,
    profile_id: str,
    window: str,
    symbols: Sequence[str],
    timeframe: str,
    cutoff_utc: str,
) -> GlobalUtcSplitProfile:
    profile = GLOBAL_UTC_PROFILE
    profile.validate()
    mismatches: Dict[str, Any] = {}
    if protocol_id != profile.protocol_id:
        mismatches["protocol_id"] = protocol_id
    if profile_id != profile.profile_id:
        mismatches["profile_id"] = profile_id
    if str(window).upper() != profile.window:
        mismatches["window"] = window
    if tuple(sorted(map(str, symbols))) != tuple(sorted(profile.symbols)):
        mismatches["symbols"] = list(symbols)
    if str(timeframe) != profile.timeframe:
        mismatches["timeframe"] = timeframe
    cutoff = _strict_utc(cutoff_utc, "cutoff_utc")
    if cutoff != _strict_utc(profile.research_cutoff_utc, "research_cutoff_utc"):
        mismatches["cutoff_utc"] = cutoff.isoformat()
    if mismatches:
        raise ValueError(f"GLOBAL_UTC_PROFILE_VIOLATION: request mismatch {mismatches}")
    return profile


def assign_global_utc_split(
    timestamp: Any,
    profile: GlobalUtcSplitProfile = GLOBAL_UTC_PROFILE,
) -> str:
    profile.validate()
    current = _strict_utc(timestamp)
    train_end = _strict_utc(profile.train_end_utc, "train_end_utc")
    validation_start = _strict_utc(profile.validation_start_utc, "validation_start_utc")
    test_start = _strict_utc(profile.test_start_utc, "test_start_utc")
    if current <= train_end:
        return "TRAIN_60"
    if current < validation_start:
        raise ValueError("GLOBAL_UTC_PROFILE_VIOLATION: timestamp falls in an undefined boundary gap")
    if current < test_start:
        return "VALIDATION_20"
    return "TEST_20"


def global_utc_fingerprint(
    *,
    source_fingerprints: Mapping[str, str],
    profile: GlobalUtcSplitProfile = GLOBAL_UTC_PROFILE,
    feature_version: str = FEATURE_SET_VERSION,
    decision_model_version: str = DECISION_MODEL_VERSION,
    calibration_version: str = SCORE_CALIBRATION_VERSION,
    execution_model_version: str = EXECUTION_MODEL_VERSION,
) -> str:
    profile.validate()
    if set(map(str, source_fingerprints)) != set(profile.symbols):
        raise ValueError(
            "GLOBAL_UTC_PROFILE_VIOLATION: source fingerprints must cover the exact symbol universe"
        )
    payload = {
        **asdict(profile),
        "symbols": sorted(profile.symbols),
        "source_fingerprints": sorted(
            (str(symbol), str(value)) for symbol, value in source_fingerprints.items()
        ),
        "feature_version": feature_version,
        "decision_model_version": decision_model_version,
        "calibration_version": calibration_version,
        "execution_model_version": execution_model_version,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_global_replay_manifest(
    *,
    source_fingerprints: Mapping[str, str],
    counts_by_split: Mapping[str, int],
    counts_by_symbol_and_split: Mapping[str, Mapping[str, int]],
    first_last_timestamp_by_split: Mapping[str, Mapping[str, str]],
    cross_asset_timestamp_label_conflicts: int,
    profile: GlobalUtcSplitProfile = GLOBAL_UTC_PROFILE,
) -> Dict[str, Any]:
    output_fingerprint = global_utc_fingerprint(
        source_fingerprints=source_fingerprints,
        profile=profile,
    )
    return {
        "schema_version": profile.schema_version,
        "split_protocol": profile.protocol_id,
        "split_profile": profile.profile_id,
        "boundaries_frozen_before_holdout": True,
        "train_end_utc": profile.train_end_utc,
        "validation_start_utc": profile.validation_start_utc,
        "test_start_utc": profile.test_start_utc,
        "window": profile.window,
        "symbols": list(profile.symbols),
        "timeframe": profile.timeframe,
        "cutoff": profile.research_cutoff_utc,
        "purge_owner": profile.purge_owner,
        "purge_applied": profile.purge_applied,
        "purge_timestamps": profile.purge_timestamps,
        "purge_unit": profile.purge_unit,
        "canonical": False,
        "source_fingerprints": dict(sorted(source_fingerprints.items())),
        "output_fingerprint": output_fingerprint,
        "counts_by_split": dict(counts_by_split),
        "counts_by_symbol_and_split": {
            key: dict(value) for key, value in counts_by_symbol_and_split.items()
        },
        "first_last_timestamp_by_split": {
            key: dict(value) for key, value in first_last_timestamp_by_split.items()
        },
        "cross_asset_timestamp_label_conflicts": int(
            cross_asset_timestamp_label_conflicts
        ),
    }


def validate_global_replay_manifest(
    manifest: Mapping[str, Any],
    rows: pd.DataFrame,
    *,
    profile: GlobalUtcSplitProfile = GLOBAL_UTC_PROFILE,
) -> None:
    profile.validate()
    required = {
        "split_protocol",
        "split_profile",
        "boundaries_frozen_before_holdout",
        "train_end_utc",
        "validation_start_utc",
        "test_start_utc",
        "window",
        "symbols",
        "timeframe",
        "cutoff",
        "purge_owner",
        "purge_applied",
        "purge_timestamps",
        "purge_unit",
        "canonical",
        "source_fingerprints",
        "output_fingerprint",
        "counts_by_split",
        "counts_by_symbol_and_split",
        "first_last_timestamp_by_split",
        "cross_asset_timestamp_label_conflicts",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise ValueError(f"GLOBAL_UTC_MANIFEST_VIOLATION: missing fields {missing}")
    expected = {
        "split_protocol": profile.protocol_id,
        "split_profile": profile.profile_id,
        "boundaries_frozen_before_holdout": True,
        "train_end_utc": profile.train_end_utc,
        "validation_start_utc": profile.validation_start_utc,
        "test_start_utc": profile.test_start_utc,
        "window": profile.window,
        "symbols": list(profile.symbols),
        "timeframe": profile.timeframe,
        "cutoff": profile.research_cutoff_utc,
        "purge_owner": profile.purge_owner,
        "purge_applied": False,
        "purge_timestamps": profile.purge_timestamps,
        "purge_unit": profile.purge_unit,
        "canonical": False,
        "cross_asset_timestamp_label_conflicts": 0,
    }
    mismatches = {
        key: manifest.get(key)
        for key, value in expected.items()
        if manifest.get(key) != value
    }
    if mismatches:
        raise ValueError(f"GLOBAL_UTC_MANIFEST_VIOLATION: contract mismatch {mismatches}")
    fingerprint = global_utc_fingerprint(
        source_fingerprints=manifest["source_fingerprints"],
        profile=profile,
    )
    if manifest["output_fingerprint"] != fingerprint:
        raise ValueError("GLOBAL_UTC_MANIFEST_VIOLATION: fingerprint mismatch")
    if rows is None or not {"replay_split", "symbol", "candle_timestamp"}.issubset(rows.columns):
        raise ValueError("GLOBAL_UTC_MANIFEST_VIOLATION: replay rows lack reconciliation columns")
    split_counts = rows.groupby("replay_split").size().astype(int).to_dict()
    symbol_counts = {
        str(symbol): group.groupby("replay_split").size().astype(int).to_dict()
        for symbol, group in rows.groupby("symbol")
    }
    if manifest["counts_by_split"] != split_counts:
        raise ValueError("GLOBAL_UTC_MANIFEST_VIOLATION: split counts do not reconcile")
    if manifest["counts_by_symbol_and_split"] != symbol_counts:
        raise ValueError("GLOBAL_UTC_MANIFEST_VIOLATION: symbol/split counts do not reconcile")
    timestamp_rows = rows.assign(
        __manifest_timestamp=pd.to_datetime(
            rows["candle_timestamp"], utc=True, errors="raise"
        )
    )
    first_last = {
        str(label): {
            "first": group["__manifest_timestamp"].min().isoformat(),
            "last": group["__manifest_timestamp"].max().isoformat(),
        }
        for label, group in timestamp_rows.groupby("replay_split")
    }
    if manifest["first_last_timestamp_by_split"] != first_last:
        raise ValueError("GLOBAL_UTC_MANIFEST_VIOLATION: timestamp ranges do not reconcile")
    labels_per_timestamp = rows.groupby("candle_timestamp")["replay_split"].nunique()
    if int(labels_per_timestamp.gt(1).sum()) != 0:
        raise ValueError("GLOBAL_UTC_MANIFEST_VIOLATION: cross-asset timestamp label conflict")


def validate_v3_upstream_purge_metadata(frame: pd.DataFrame) -> None:
    required = {
        "split_protocol",
        "split_profile",
        "purge_owner",
        "purge_applied",
        "purge_timestamps",
        "purge_unit",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(
            f"UPSTREAM_SPLIT_PROVENANCE_VIOLATION: missing v3 purge metadata {missing}"
        )
    expected = {
        "split_protocol": GLOBAL_UTC_PROTOCOL,
        "split_profile": GLOBAL_UTC_PROFILE_ID,
        "purge_owner": "EVENT_PIPELINE",
        "purge_timestamps": 6,
        "purge_unit": "unique UTC timestamps",
    }
    for column, value in expected.items():
        observed = set(frame[column].dropna().tolist())
        if observed != {value}:
            raise ValueError(
                f"UPSTREAM_SPLIT_PROVENANCE_VIOLATION: {column} mismatch {observed}"
            )
    applied = frame["purge_applied"]
    if applied.isna().any() or applied.astype(bool).any():
        raise ValueError(
            "UPSTREAM_SPLIT_PROVENANCE_VIOLATION: upstream purge already applied"
        )


def validate_v3_upstream_purge_manifest(manifest: Mapping[str, Any]) -> None:
    if not isinstance(manifest, Mapping):
        raise ValueError(
            "UPSTREAM_SPLIT_PROVENANCE_VIOLATION: v3 upstream manifest is missing"
        )
    expected = {
        "split_protocol": GLOBAL_UTC_PROTOCOL,
        "split_profile": GLOBAL_UTC_PROFILE_ID,
        "purge_owner": "EVENT_PIPELINE",
        "purge_applied": False,
        "purge_timestamps": 6,
        "purge_unit": "unique UTC timestamps",
        "canonical": False,
    }
    missing = sorted(set(expected) - set(manifest))
    if missing:
        raise ValueError(
            f"UPSTREAM_SPLIT_PROVENANCE_VIOLATION: missing v3 manifest metadata {missing}"
        )
    mismatches = {
        key: manifest.get(key)
        for key, value in expected.items()
        if manifest.get(key) != value
    }
    if mismatches:
        raise ValueError(
            f"UPSTREAM_SPLIT_PROVENANCE_VIOLATION: v3 manifest metadata mismatch {mismatches}"
        )
