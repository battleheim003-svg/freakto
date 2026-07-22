"""Economic interpretation of raw decision scores.

The artifact is fitted on TRAIN and assessed on VALIDATION. TEST outcomes are
never used to fit probabilities or expectancy. A failed artifact remains useful
for reporting, but is explicitly unusable for capital allocation.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from engine.model_contract import CURRENT_MODEL_CONTRACT


VERSION = "economic-calibration-v1"
DEFAULT_REPLAY_FILE = Path("logs") / "market_replay" / "market_replay_evaluations.csv"
DEFAULT_ARTIFACT = Path("logs") / "models" / "economic_score_calibration.json"
SCORE_BANDS: Tuple[Tuple[int, int], ...] = tuple((low, low + 9) for low in range(0, 100, 10))


@dataclass
class EconomicBand:
    label: str
    score_min: int
    score_max: int
    samples: int
    wins: int
    historical_win_probability: float
    probability_ci_low: float
    probability_ci_high: float
    average_net_return_pct: float
    average_r: float
    median_r: float
    profit_factor_r: float
    sufficient_samples: bool


@dataclass
class EconomicCalibrationArtifact:
    version: str
    generated_utc: str
    source_replay_run_id: str
    feature_set_version: str
    model_version: str
    calibration_version: str
    status: str
    usable_for_allocation: bool
    train_samples: int
    validation_samples: int
    global_train_win_probability: float
    validation_score_return_correlation: float
    validation_high_minus_low_r: float
    bands: List[EconomicBand] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class EconomicEstimate:
    score: float
    band: str
    historical_win_probability: float
    probability_ci_low: float
    probability_ci_high: float
    expected_r: float
    average_net_return_pct: float
    samples: int
    calibration_status: str
    usable_for_allocation: bool


def _number(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        parsed = float(value)
        return parsed if math.isfinite(parsed) else default
    except (TypeError, ValueError):
        return default


def _parse_stop(value: Any) -> Optional[float]:
    text = str(value or "").replace("`", "").replace(",", "").strip()
    if not text:
        return None
    values = []
    for part in text.split(" - "):
        parsed = _number(part)
        if parsed is not None:
            values.append(parsed)
    return sum(values) / len(values) if values else None


def _wilson(wins: int, samples: int, z: float = 1.96) -> Tuple[float, float]:
    if samples <= 0:
        return 0.0, 1.0
    p = wins / samples
    denominator = 1.0 + z * z / samples
    centre = (p + z * z / (2 * samples)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * samples)) / samples) / denominator
    return max(0.0, centre - margin), min(1.0, centre + margin)


def _prepare(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    if "run_id" in work.columns and not work.empty:
        contract = CURRENT_MODEL_CONTRACT.as_dict()
        compatible = pd.Series(True, index=work.index)
        for column, expected in contract.items():
            if column in work.columns:
                compatible &= work[column].astype(str).eq(expected)
        compatible_frame = work[compatible]
        if not compatible_frame.empty:
            latest = str(compatible_frame["run_id"].dropna().iloc[-1])
            work = compatible_frame[compatible_frame["run_id"].astype(str) == latest].copy()
    side = work.get("side", pd.Series("", index=work.index)).astype(str)
    status = work.get("evaluation_status", pd.Series("", index=work.index)).astype(str)
    work = work[side.isin(["LONG", "SHORT"]) & status.eq("COMPLETE")].copy()
    work["_score"] = pd.to_numeric(work.get("score"), errors="coerce")
    work["_net"] = pd.to_numeric(work.get("net_return_pct"), errors="coerce")
    if work["_net"].isna().all():
        work["_net"] = pd.to_numeric(work.get("net_signed_return_after_6c_pct"), errors="coerce")
    entries = pd.to_numeric(work.get("entry_price"), errors="coerce")
    stops = work.get("stop_zone", pd.Series("", index=work.index)).map(_parse_stop)
    risk_pct = (entries - stops).abs() / entries.abs().clip(lower=1e-12) * 100.0
    work["_r"] = (work["_net"] / risk_pct.where(risk_pct > 0)).clip(-10.0, 10.0)
    work = work.dropna(subset=["_score", "_net", "_r"])
    return work


def _band_for(score: float) -> Tuple[int, int]:
    value = max(0, min(100, int(float(score))))
    low = min(90, (value // 10) * 10)
    return low, low + 9


def _profit_factor(values: pd.Series) -> float:
    wins = values[values > 0].sum()
    losses = abs(values[values < 0].sum())
    return float(wins / losses) if losses > 0 else (999.0 if wins > 0 else 0.0)


def _build_bands(train: pd.DataFrame, min_band_samples: int) -> List[EconomicBand]:
    global_wins = int((train["_net"] > 0).sum())
    global_samples = len(train)
    prior_strength = 40.0
    prior_probability = global_wins / global_samples if global_samples else 0.5
    bands: List[EconomicBand] = []
    for low, high in SCORE_BANDS:
        part = train[(train["_score"] >= low) & (train["_score"] <= high)]
        samples = int(len(part))
        wins = int((part["_net"] > 0).sum())
        shrunk = (wins + prior_probability * prior_strength) / (samples + prior_strength) if samples else prior_probability
        ci_low, ci_high = _wilson(wins, samples)
        r_values = part["_r"].dropna()
        bands.append(EconomicBand(
            label=f"{low}_{high}", score_min=low, score_max=high,
            samples=samples, wins=wins,
            historical_win_probability=round(shrunk, 4),
            probability_ci_low=round(ci_low, 4), probability_ci_high=round(ci_high, 4),
            average_net_return_pct=round(float(part["_net"].mean()), 6) if samples else 0.0,
            average_r=round(float(r_values.mean()), 6) if len(r_values) else 0.0,
            median_r=round(float(r_values.median()), 6) if len(r_values) else 0.0,
            profit_factor_r=round(_profit_factor(r_values), 4),
            sufficient_samples=samples >= min_band_samples,
        ))
    return bands


def build_economic_calibration(
    path: str | Path = DEFAULT_REPLAY_FILE,
    *,
    min_train_samples: int = 500,
    min_validation_samples: int = 150,
    min_band_samples: int = 100,
) -> EconomicCalibrationArtifact:
    input_path = Path(path)
    if not input_path.exists():
        return EconomicCalibrationArtifact(
            VERSION, datetime.now(timezone.utc).isoformat(), "", CURRENT_MODEL_CONTRACT.feature_set_version,
            CURRENT_MODEL_CONTRACT.model_version, CURRENT_MODEL_CONTRACT.calibration_version,
            "BLOCKED_NO_REPLAY", False, 0, 0, 0.0, 0.0, 0.0,
            blockers=[f"Replay file not found: {input_path}"],
        )
    raw = pd.read_csv(input_path, encoding="utf-8-sig", low_memory=False)
    work = _prepare(raw)
    source_run = str(work.get("run_id", pd.Series([""])).iloc[-1]) if len(work) else ""
    split = work.get("replay_split", pd.Series("", index=work.index)).astype(str)
    train = work[split.eq("TRAIN_60")].copy()
    validation = work[split.eq("VALIDATION_20")].copy()
    blockers: List[str] = []
    if len(train) < min_train_samples:
        blockers.append(f"TRAIN samples {len(train)} < {min_train_samples}.")
    if len(validation) < min_validation_samples:
        blockers.append(f"VALIDATION samples {len(validation)} < {min_validation_samples}.")
    bands = _build_bands(train, min_band_samples) if len(train) else []
    corr = validation["_score"].corr(validation["_r"], method="spearman") if len(validation) >= 3 else 0.0
    corr = 0.0 if pd.isna(corr) else float(corr)
    q25 = float(train["_score"].quantile(0.25)) if len(train) else 0.0
    q75 = float(train["_score"].quantile(0.75)) if len(train) else 0.0
    low_r = validation[validation["_score"] <= q25]["_r"].mean() if len(validation) else 0.0
    high_r = validation[validation["_score"] >= q75]["_r"].mean() if len(validation) else 0.0
    spread = float(high_r - low_r) if not (pd.isna(low_r) or pd.isna(high_r)) else 0.0
    enough_bands = sum(1 for band in bands if band.sufficient_samples) >= 3
    usable = not blockers and enough_bands and corr >= 0.10 and spread > 0 and float(validation["_r"].mean()) > 0
    if not enough_bands:
        blockers.append("Fewer than three score bands have sufficient TRAIN samples.")
    if corr < 0.10:
        blockers.append(f"VALIDATION score-to-R correlation is not positive enough: {corr:.4f}.")
    if spread <= 0:
        blockers.append(f"High-score VALIDATION expectancy does not beat low-score expectancy: {spread:.4f}R.")
    if len(validation) and float(validation["_r"].mean()) <= 0:
        blockers.append("VALIDATION average expectancy R is not positive.")
    global_probability = float((train["_net"] > 0).mean()) if len(train) else 0.0
    return EconomicCalibrationArtifact(
        version=VERSION,
        generated_utc=datetime.now(timezone.utc).isoformat(),
        source_replay_run_id=source_run,
        feature_set_version=CURRENT_MODEL_CONTRACT.feature_set_version,
        model_version=CURRENT_MODEL_CONTRACT.model_version,
        calibration_version=CURRENT_MODEL_CONTRACT.calibration_version,
        status="ECONOMIC_CALIBRATION_VALIDATED" if usable else "ECONOMIC_CALIBRATION_RESEARCH_ONLY",
        usable_for_allocation=usable,
        train_samples=int(len(train)), validation_samples=int(len(validation)),
        global_train_win_probability=round(global_probability, 4),
        validation_score_return_correlation=round(corr, 6),
        validation_high_minus_low_r=round(spread, 6),
        bands=bands,
        blockers=blockers,
        warnings=["Probabilities and R are historical estimates, not guarantees.", "R values are winsorized to [-10, 10] for calibration stability."],
    )


def save_economic_calibration(artifact: EconomicCalibrationArtifact, path: str | Path = DEFAULT_ARTIFACT) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(output.name + ".tmp")
    temp.write_text(json.dumps(asdict(artifact), ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(output)
    return output


def load_economic_calibration(path: str | Path = DEFAULT_ARTIFACT) -> Optional[EconomicCalibrationArtifact]:
    artifact_path = Path(path)
    if not artifact_path.exists():
        return None
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    payload["bands"] = [EconomicBand(**item) for item in payload.get("bands", [])]
    return EconomicCalibrationArtifact(**payload)


def estimate_score_economics(score: float, artifact: Optional[EconomicCalibrationArtifact] = None) -> EconomicEstimate:
    artifact = artifact or load_economic_calibration()
    if artifact is None:
        return EconomicEstimate(float(score), "UNKNOWN", 0.0, 0.0, 1.0, 0.0, 0.0, 0, "MISSING", False)
    low, high = _band_for(score)
    band = next((item for item in artifact.bands if item.score_min == low), None)
    if band is None:
        return EconomicEstimate(float(score), f"{low}_{high}", artifact.global_train_win_probability, 0.0, 1.0, 0.0, 0.0, 0, artifact.status, False)
    return EconomicEstimate(
        score=float(score), band=band.label,
        historical_win_probability=band.historical_win_probability,
        probability_ci_low=band.probability_ci_low, probability_ci_high=band.probability_ci_high,
        expected_r=band.average_r, average_net_return_pct=band.average_net_return_pct,
        samples=band.samples, calibration_status=artifact.status,
        usable_for_allocation=bool(artifact.usable_for_allocation and band.sufficient_samples),
    )
