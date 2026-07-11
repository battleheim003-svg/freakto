"""
Freakto Calibration Mapper v1.0

Converts raw decision scores into empirical probabilities.
The score is not treated as probability anymore.
"""

from dataclasses import dataclass
from pathlib import Path
import pandas as pd

DEFAULT_DATASET = Path("logs/calibration_dataset/calibration_training.csv")


@dataclass
class CalibrationEstimate:
    score: float
    probability: float
    samples: int
    verdict: str


def _bucket(score: float) -> str:
    low = int(float(score) // 10 * 10)
    return f"score_{low}_{low+9}"


def build_mapping(dataset_path: Path = DEFAULT_DATASET) -> pd.DataFrame:
    if not dataset_path.exists():
        return pd.DataFrame()

    df = pd.read_csv(dataset_path)
    if "evaluated_return" not in df.columns or "score" not in df.columns:
        return pd.DataFrame()

    df["win"] = pd.to_numeric(df["evaluated_return"], errors="coerce") > 0
    df["score_bucket"] = df["score"].map(_bucket)

    mapping = (
        df.groupby("score_bucket")
        .agg(
            samples=("win", "size"),
            historical_probability=("win", "mean"),
            avg_return=("evaluated_return", "mean"),
        )
        .reset_index()
    )

    mapping["historical_probability"] = (
        mapping["historical_probability"] * 100
    ).round(2)

    return mapping


def estimate_probability(score: float, mapping: pd.DataFrame) -> CalibrationEstimate:
    bucket = _bucket(score)

    if mapping.empty or bucket not in set(mapping["score_bucket"]):
        return CalibrationEstimate(score, 50.0, 0, "NO_DATA")

    row = mapping[mapping["score_bucket"] == bucket].iloc[0]
    prob = float(row["historical_probability"])
    samples = int(row["samples"])

    verdict = "VALID" if samples >= 100 else "LOW_SAMPLE"

    return CalibrationEstimate(score, prob, samples, verdict)
