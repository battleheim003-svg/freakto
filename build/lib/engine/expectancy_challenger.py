"""Expectancy-aware challenger model for Freakto research and shadow evaluation.

The challenger is deliberately separate from :class:`DecisionEngine`.  It is
trained only on chronological replay data and produces *shadow* decisions.  It
never changes score weights, Paper settings, Live settings, or order execution.

Model design
------------
* LONG and SHORT are fitted independently.
* Win probability, average winning payoff, and average losing payoff are
  estimated separately.
* Momentum is capped by default because attribution found that large momentum
  values did not generalize.
* Structure is not added to the linear feature score; it can be used as a hard
  gate by a challenger variant.
* Volume remains a confirmation gate.
* Risk penalty, already known at decision time, is translated to an explicit
  expected-value haircut.
* Any missing model, unsupported side, unknown regime, or failed gate is
  fail-closed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, Iterable, Optional, Sequence

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

VERSION = "v10.7.0"

LEAKAGE_TOKENS = (
    "return",
    "win",
    "loss",
    "outcome",
    "future",
    "target_hit",
    "stop_hit",
    "mfe",
    "mae",
    "exit_price",
    "direction_correct",
)

BASE_NUMERIC_FEATURES = (
    "trend_score",
    "volume_score",
    "regime_score",
    "risk_penalty",
    "adaptive_adjustment",
    "external_context_score",
    "historical_edge_score",
)


@dataclass(frozen=True)
class ChallengerConfig:
    minimum_side_train_rows: int = 300
    minimum_class_rows: int = 60
    minimum_payoff_rows: int = 45
    probability_clip_low: float = 0.02
    probability_clip_high: float = 0.98
    logistic_c: float = 0.25
    ridge_alpha: float = 20.0
    payoff_model_weight: float = 0.35
    momentum_cap: float = 20.0
    minimum_volume_score: float = 5.0
    minimum_structure_score: float = 6.0
    risk_cost_pct_per_point: float = 0.015
    additional_execution_cost_pct: float = 0.05
    block_unknown_regime: bool = True
    random_state: int = 42

    def validate(self) -> None:
        if self.minimum_side_train_rows <= 0:
            raise ValueError("minimum_side_train_rows must be positive.")
        if self.minimum_class_rows <= 0 or self.minimum_payoff_rows <= 0:
            raise ValueError("minimum outcome constraints must be positive.")
        if not 0 < self.probability_clip_low < self.probability_clip_high < 1:
            raise ValueError("probability clip bounds must be inside (0, 1).")
        if not 0 <= self.payoff_model_weight <= 1:
            raise ValueError("payoff_model_weight must be in [0, 1].")
        if self.momentum_cap <= 0:
            raise ValueError("momentum_cap must be positive.")
        if self.risk_cost_pct_per_point < 0 or self.additional_execution_cost_pct < 0:
            raise ValueError("cost parameters cannot be negative.")


@dataclass(frozen=True)
class ChallengerVariant:
    name: str
    include_momentum: bool = True
    structure_gate: bool = False
    allowed_sides: tuple[str, ...] = ("LONG", "SHORT")
    description: str = ""

    def validate(self) -> None:
        allowed = {str(side).upper() for side in self.allowed_sides}
        if not allowed or not allowed.issubset({"LONG", "SHORT"}):
            raise ValueError("allowed_sides must contain LONG and/or SHORT only.")


DEFAULT_VARIANTS: tuple[ChallengerVariant, ...] = (
    ChallengerVariant(
        name="EXPECTANCY_BASE",
        include_momentum=True,
        structure_gate=False,
        description="Side-specific expected value with capped momentum and volume confirmation.",
    ),
    ChallengerVariant(
        name="EXPECTANCY_NO_MOMENTUM",
        include_momentum=False,
        structure_gate=False,
        description="Expected-value model without Momentum.",
    ),
    ChallengerVariant(
        name="EXPECTANCY_STRUCTURE_GATE",
        include_momentum=True,
        structure_gate=True,
        description="Expected-value model with Structure used only as a hard gate.",
    ),
    ChallengerVariant(
        name="EXPECTANCY_LONG_ONLY",
        include_momentum=True,
        structure_gate=True,
        allowed_sides=("LONG",),
        description="LONG-only challenger; SHORT is fail-closed.",
    ),
    ChallengerVariant(
        name="EXPECTANCY_SHORT_DISABLED",
        include_momentum=True,
        structure_gate=True,
        allowed_sides=("LONG",),
        description="Explicit SHORT-disabled alias used for safety/reporting.",
    ),
)


@dataclass
class SideModel:
    side: str
    status: str
    sample_count: int
    win_count: int
    loss_count: int
    probability_model: Optional[Pipeline] = None
    win_payoff_model: Optional[Pipeline] = None
    loss_payoff_model: Optional[Pipeline] = None
    average_win_pct: float = 0.0
    average_loss_pct: float = 0.0
    win_floor_pct: float = 0.0
    win_ceiling_pct: float = 0.0
    loss_floor_pct: float = 0.0
    loss_ceiling_pct: float = 0.0
    reason: str = ""

    @property
    def available(self) -> bool:
        return (
            self.status == "READY"
            and self.probability_model is not None
            and self.win_payoff_model is not None
            and self.loss_payoff_model is not None
        )

    def metadata(self) -> dict:
        data = asdict(self)
        for key in ("probability_model", "win_payoff_model", "loss_payoff_model"):
            data.pop(key, None)
        data["available"] = self.available
        return data


@dataclass
class ChallengerFitSummary:
    version: str
    variant: str
    status: str
    train_rows: int
    feature_columns: list[str]
    side_models: dict[str, dict] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def validate_feature_columns(features: Iterable[str]) -> None:
    for feature in features:
        lowered = str(feature).strip().lower()
        if any(token in lowered for token in LEAKAGE_TOKENS):
            raise ValueError(f"Outcome/leakage column cannot be used as a model feature: {feature}")


def expected_value_pct(
    probability_win: float,
    average_win_pct: float,
    average_loss_pct: float,
    *,
    execution_cost_pct: float = 0.0,
    risk_cost_pct: float = 0.0,
) -> float:
    """Return the expected net percentage value for one decision.

    ``average_loss_pct`` is supplied as a positive magnitude.
    """

    probability = min(1.0, max(0.0, float(probability_win)))
    win = max(0.0, float(average_win_pct))
    loss = max(0.0, float(average_loss_pct))
    costs = max(0.0, float(execution_cost_pct)) + max(0.0, float(risk_cost_pct))
    return probability * win - (1.0 - probability) * loss - costs


def _normalise_regime(value: object) -> str:
    text = str(value or "").strip().upper().replace("-", "_").replace(" ", "_")
    if text in {"TRENDING_BULL", "BULL", "BULLISH", "UPTREND", "TREND_UP"}:
        return "BULL"
    if text in {"TRENDING_BEAR", "BEAR", "BEARISH", "DOWNTREND", "TREND_DOWN"}:
        return "BEAR"
    if text in {"SIDEWAYS", "RANGE", "RANGING", "NEUTRAL", "CHOP", "CHOPPY"}:
        return "SIDEWAYS"
    if text in {"VOLATILE", "HIGH_VOL", "HIGH_VOLATILITY", "EXPANDING_VOLATILITY"}:
        return "VOLATILE"
    if text in {"QUIET", "LOW_VOL", "LOW_VOLATILITY", "COMPRESSED_VOLATILITY"}:
        return "QUIET"
    return "UNKNOWN"


def _numeric(frame: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce").fillna(default).astype(float)


def build_feature_frame(
    frame: pd.DataFrame,
    variant: ChallengerVariant,
    config: ChallengerConfig,
) -> pd.DataFrame:
    """Build decision-time-only features for one challenger variant."""

    variant.validate()
    numeric_features = list(BASE_NUMERIC_FEATURES)
    validate_feature_columns(numeric_features)
    output = pd.DataFrame(index=frame.index)
    for feature in numeric_features:
        output[feature] = _numeric(frame, feature)
    if variant.include_momentum:
        output["momentum_capped"] = _numeric(frame, "momentum_score").clip(
            lower=-config.momentum_cap,
            upper=config.momentum_cap,
        )
    regime_source = (
        frame["_regime_group"]
        if "_regime_group" in frame.columns
        else frame.get("regime_label", pd.Series("UNKNOWN", index=frame.index))
    )
    output["regime_group"] = regime_source.map(_normalise_regime).astype(str)
    return output


def _pipeline_for_columns(
    feature_columns: Sequence[str],
    config: ChallengerConfig,
    *,
    classification: bool,
) -> Pipeline:
    numeric = [column for column in feature_columns if column != "regime_group"]
    categorical = ["regime_group"]
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), numeric),
            (
                "regime",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                categorical,
            ),
        ],
        remainder="drop",
        sparse_threshold=0.0,
    )
    estimator = (
        LogisticRegression(
            C=config.logistic_c,
            class_weight="balanced",
            max_iter=2000,
            random_state=config.random_state,
            solver="lbfgs",
        )
        if classification
        else Ridge(alpha=config.ridge_alpha)
    )
    return Pipeline([("preprocess", preprocessor), ("model", estimator)])


class ExpectancyChallenger:
    """Side-specific research challenger that emits fail-closed shadow scores."""

    def __init__(
        self,
        variant: ChallengerVariant,
        config: ChallengerConfig = ChallengerConfig(),
    ) -> None:
        config.validate()
        variant.validate()
        self.variant = variant
        self.config = config
        self.side_models: Dict[str, SideModel] = {}
        self.feature_columns: list[str] = []
        self.fit_summary: Optional[ChallengerFitSummary] = None

    def fit(self, train: pd.DataFrame) -> ChallengerFitSummary:
        required = {"side", "evaluated_return"}
        missing = sorted(required.difference(train.columns))
        if missing:
            raise ValueError(f"Missing challenger training columns: {', '.join(missing)}")
        if train.empty:
            raise ValueError("Training frame is empty.")

        features = build_feature_frame(train, self.variant, self.config)
        self.feature_columns = features.columns.tolist()
        validate_feature_columns(self.feature_columns)
        blockers: list[str] = []
        self.side_models = {}

        side_series = train["side"].astype(str).str.upper()
        returns = pd.to_numeric(train["evaluated_return"], errors="coerce")
        for side in ("LONG", "SHORT"):
            if side not in {value.upper() for value in self.variant.allowed_sides}:
                model = SideModel(
                    side=side,
                    status="DISABLED",
                    sample_count=int(side_series.eq(side).sum()),
                    win_count=0,
                    loss_count=0,
                    reason="Side disabled by challenger variant.",
                )
                self.side_models[side] = model
                continue

            mask = side_series.eq(side) & returns.notna()
            side_features = features.loc[mask]
            side_returns = returns.loc[mask]
            wins = side_returns > 0
            losses = side_returns < 0
            sample_count = int(len(side_returns))
            win_count = int(wins.sum())
            loss_count = int(losses.sum())

            if sample_count < self.config.minimum_side_train_rows:
                reason = (
                    f"{side} has {sample_count} training rows; "
                    f"{self.config.minimum_side_train_rows} required."
                )
                self.side_models[side] = SideModel(
                    side, "INSUFFICIENT_DATA", sample_count, win_count, loss_count, reason=reason
                )
                blockers.append(reason)
                continue
            if min(win_count, loss_count) < self.config.minimum_class_rows:
                reason = (
                    f"{side} class support is insufficient: wins={win_count}, losses={loss_count}."
                )
                self.side_models[side] = SideModel(
                    side, "INSUFFICIENT_CLASSES", sample_count, win_count, loss_count, reason=reason
                )
                blockers.append(reason)
                continue
            if win_count < self.config.minimum_payoff_rows or loss_count < self.config.minimum_payoff_rows:
                reason = f"{side} payoff-model support is insufficient."
                self.side_models[side] = SideModel(
                    side, "INSUFFICIENT_PAYOFFS", sample_count, win_count, loss_count, reason=reason
                )
                blockers.append(reason)
                continue

            probability_model = _pipeline_for_columns(
                self.feature_columns, self.config, classification=True
            )
            win_model = _pipeline_for_columns(
                self.feature_columns, self.config, classification=False
            )
            loss_model = _pipeline_for_columns(
                self.feature_columns, self.config, classification=False
            )
            probability_model.fit(side_features, wins.astype(int))
            win_model.fit(side_features.loc[wins], side_returns.loc[wins].astype(float))
            loss_model.fit(side_features.loc[losses], side_returns.loc[losses].abs().astype(float))

            win_values = side_returns.loc[wins].astype(float)
            loss_values = side_returns.loc[losses].abs().astype(float)
            model = SideModel(
                side=side,
                status="READY",
                sample_count=sample_count,
                win_count=win_count,
                loss_count=loss_count,
                probability_model=probability_model,
                win_payoff_model=win_model,
                loss_payoff_model=loss_model,
                average_win_pct=float(win_values.mean()),
                average_loss_pct=float(loss_values.mean()),
                win_floor_pct=float(win_values.quantile(0.05)),
                win_ceiling_pct=float(win_values.quantile(0.95)),
                loss_floor_pct=float(loss_values.quantile(0.05)),
                loss_ceiling_pct=float(loss_values.quantile(0.95)),
            )
            self.side_models[side] = model

        ready = [model for model in self.side_models.values() if model.available]
        status = "READY" if ready else "FAIL_CLOSED"
        summary = ChallengerFitSummary(
            version=VERSION,
            variant=self.variant.name,
            status=status,
            train_rows=int(len(train)),
            feature_columns=list(self.feature_columns),
            side_models={side: model.metadata() for side, model in self.side_models.items()},
            blockers=blockers,
        )
        self.fit_summary = summary
        return summary

    def _predict_side(
        self,
        features: pd.DataFrame,
        model: SideModel,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        probability = model.probability_model.predict_proba(features)[:, 1]
        probability = np.clip(
            probability,
            self.config.probability_clip_low,
            self.config.probability_clip_high,
        )
        win_model = np.asarray(model.win_payoff_model.predict(features), dtype=float)
        loss_model = np.asarray(model.loss_payoff_model.predict(features), dtype=float)
        blend = self.config.payoff_model_weight
        win = blend * win_model + (1.0 - blend) * model.average_win_pct
        loss = blend * loss_model + (1.0 - blend) * model.average_loss_pct
        win = np.clip(win, max(0.0, model.win_floor_pct), max(model.win_floor_pct, model.win_ceiling_pct))
        loss = np.clip(
            loss,
            max(0.0, model.loss_floor_pct),
            max(model.loss_floor_pct, model.loss_ceiling_pct),
        )
        return probability, win, loss

    def predict(self, frame: pd.DataFrame) -> pd.DataFrame:
        if self.fit_summary is None:
            raise RuntimeError("Challenger must be fitted before prediction.")
        output = pd.DataFrame(index=frame.index)
        output["challenger_variant"] = self.variant.name
        output["shadow_only"] = True
        output["paper_live_enabled"] = False
        output["side"] = frame["side"].astype(str).str.upper()
        output["predicted_probability_win"] = np.nan
        output["predicted_average_win_pct"] = np.nan
        output["predicted_average_loss_pct"] = np.nan
        output["risk_cost_pct"] = 0.0
        output["execution_cost_pct"] = float(self.config.additional_execution_cost_pct)
        output["predicted_expected_value_pct"] = np.nan
        output["model_available"] = False
        output["base_gate_passed"] = False
        output["shadow_blockers"] = [[] for _ in range(len(output))]

        features = build_feature_frame(frame, self.variant, self.config)
        risk_penalty = _numeric(frame, "risk_penalty")
        output["risk_cost_pct"] = risk_penalty.clip(upper=0).abs() * self.config.risk_cost_pct_per_point
        volume = _numeric(frame, "volume_score")
        structure = _numeric(frame, "structure_score")
        regime_source = (
            frame["_regime_group"]
            if "_regime_group" in frame.columns
            else frame.get("regime_label", pd.Series("UNKNOWN", index=frame.index))
        )
        regime = regime_source.map(_normalise_regime)

        allowed_sides = {value.upper() for value in self.variant.allowed_sides}
        for side in ("LONG", "SHORT"):
            side_mask = output["side"].eq(side)
            if not side_mask.any():
                continue
            model = self.side_models.get(side)
            if model is None or not model.available:
                for index in output.index[side_mask]:
                    blockers = ["SIDE_MODEL_UNAVAILABLE"]
                    if side not in allowed_sides:
                        blockers = ["SIDE_DISABLED"]
                    output.at[index, "shadow_blockers"] = blockers
                continue

            side_features = features.loc[side_mask, self.feature_columns]
            probability, win, loss = self._predict_side(side_features, model)
            indices = side_features.index
            output.loc[indices, "predicted_probability_win"] = probability
            output.loc[indices, "predicted_average_win_pct"] = win
            output.loc[indices, "predicted_average_loss_pct"] = loss
            output.loc[indices, "model_available"] = True
            risk_cost = output.loc[indices, "risk_cost_pct"].to_numpy(dtype=float)
            expected = (
                probability * win
                - (1.0 - probability) * loss
                - float(self.config.additional_execution_cost_pct)
                - risk_cost
            )
            output.loc[indices, "predicted_expected_value_pct"] = expected

        for index in output.index:
            blockers: list[str] = []
            side = output.at[index, "side"]
            if side not in allowed_sides:
                blockers.append("SIDE_DISABLED")
            if not bool(output.at[index, "model_available"]):
                blockers.append("SIDE_MODEL_UNAVAILABLE")
            if float(volume.loc[index]) < self.config.minimum_volume_score:
                blockers.append("VOLUME_CONFIRMATION_FAILED")
            if self.variant.structure_gate and float(structure.loc[index]) < self.config.minimum_structure_score:
                blockers.append("STRUCTURE_GATE_FAILED")
            if self.config.block_unknown_regime and regime.loc[index] == "UNKNOWN":
                blockers.append("UNKNOWN_REGIME")
            # Stable de-duplication keeps reports deterministic.
            blockers = list(dict.fromkeys(blockers))
            output.at[index, "shadow_blockers"] = blockers
            output.at[index, "base_gate_passed"] = len(blockers) == 0

        return output

    def metadata(self) -> dict:
        return {
            "version": VERSION,
            "variant": asdict(self.variant),
            "config": asdict(self.config),
            "fit_summary": self.fit_summary.to_dict() if self.fit_summary else None,
            "shadow_only": True,
            "paper_live_enabled": False,
        }
