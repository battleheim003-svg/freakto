from typing import List, Tuple
import pandas as pd

from .common import ScoreComponent, safe_float
from .trend import score_trend
from .momentum import score_momentum
from .volume import score_volume
from .structure import score_structure
from .risk import score_risk, risk_label
from .regime import detect_market_regime
from .adaptive import score_adaptive_adjustment
from .historical_edge import score_historical_edge
from .learning_overrides import apply_learning_overrides
from .score import OpportunityV2, confidence_label, _zones


class DecisionEngine:
    def __init__(self, min_side_score: int = 50):
        self.min_side_score = min_side_score

    def analyze(self, df: pd.DataFrame, symbol: str, timeframe: str) -> OpportunityV2:
        required = [
            "close",
            "sma_10",
            "sma_30",
            "ema_10",
            "rsi_14",
            "macd_diff",
            "atr_pct",
        ]

        clean = df.dropna(subset=required)

        if len(clean) < 35:
            return OpportunityV2(
                symbol=symbol,
                timeframe=timeframe,
                side="NEUTRAL",
                score=0,
                confidence_label="Low",
                risk_label="Unknown",
                entry_zone="نامشخص",
                stop_zone="نامشخص",
                warnings=["داده کافی برای تحلیل وجود ندارد."],
            )

        row = clean.iloc[-1]
        prev_row = clean.iloc[-2]
        recent_df = clean.tail(80)

        latest_timestamp = self._get_latest_timestamp(clean)
        regime = detect_market_regime(recent_df)

        long_score, long_components = self._analyze_side(
            prev_row=prev_row,
            row=row,
            recent_df=recent_df,
            side="LONG",
            regime=regime,
            symbol=symbol,
            timeframe=timeframe,
            latest_timestamp=latest_timestamp,
        )

        short_score, short_components = self._analyze_side(
            prev_row=prev_row,
            row=row,
            recent_df=recent_df,
            side="SHORT",
            regime=regime,
            symbol=symbol,
            timeframe=timeframe,
            latest_timestamp=latest_timestamp,
        )

        side, score, components = self._select_side(
            long_score=long_score,
            long_components=long_components,
            short_score=short_score,
            short_components=short_components,
        )

        reasons, warnings = self._collect_explanations(components)

        if side == "NEUTRAL":
            reasons = ["هیچ سمت بازار به اندازه کافی هم‌راستا نیست."]
            warnings.append(
                "در این وضعیت بهتر است فقط بازار مانیتور شود، نه اینکه فرصت فرض شود."
            )

        entry_zone, stop_zone, targets = _zones(row, side)

        risk_component = next(
            (component for component in components if component.name == "Risk Penalty"),
            ScoreComponent("Risk Penalty", 0, 25),
        )

        return OpportunityV2(
            symbol=symbol,
            timeframe=timeframe,
            side=side,
            score=score,
            confidence_label=confidence_label(score),
            risk_label=risk_label(risk_component),
            entry_zone=entry_zone,
            stop_zone=stop_zone,
            targets=targets,
            reasons=reasons,
            warnings=warnings,
            components=components,
            raw={
                "close": safe_float(row.get("close")),
                "timestamp": str(latest_timestamp),
                "long_score": long_score,
                "short_score": short_score,
                "regime_label": regime.label,
                "regime_confidence": regime.confidence,
                "regime_adjustment": regime.adjustment,
                "regime_reasons": regime.reasons,
                "regime_warnings": regime.warnings,
                "engine": "DecisionEngine",
            },
        )

    def _get_latest_timestamp(self, df: pd.DataFrame):
        if "timestamp" in df.columns:
            return df.iloc[-1]["timestamp"]

        return df.index[-1]

    def _regime_component(self, side: str, regime) -> ScoreComponent:
        points = 0
        reasons = []
        warnings = []

        if regime.label == "TRENDING_BULL":
            if side == "LONG":
                points = 5
                reasons.append("Market Regime صعودی است و Bias لانگ را تأیید می‌کند.")
            elif side == "SHORT":
                points = -8
                warnings.append("Market Regime صعودی است و با Bias شورت تضاد دارد.")

        elif regime.label == "TRENDING_BEAR":
            if side == "SHORT":
                points = 5
                reasons.append("Market Regime نزولی است و Bias شورت را تأیید می‌کند.")
            elif side == "LONG":
                points = -8
                warnings.append("Market Regime نزولی است و با Bias لانگ تضاد دارد.")

        elif regime.label == "SIDEWAYS":
            points = -5
            warnings.append("Market Regime رنج/خنثی است؛ کیفیت سیگنال‌های جهت‌دار کمتر می‌شود.")

        elif regime.label == "VOLATILE":
            points = -4
            warnings.append("Market Regime پرنوسان است؛ ریسک شکست فیک و نوسان شدید بیشتر است.")

        elif regime.label == "QUIET":
            points = -2
            warnings.append("Market Regime کم‌نوسان است؛ حرکت ممکن است هنوز انرژی کافی نداشته باشد.")

        else:
            warnings.append("Market Regime با اطمینان کافی تشخیص داده نشد.")

        return ScoreComponent(
            name="Regime Adjustment",
            points=points,
            max_points=10,
            reasons=reasons,
            warnings=warnings,
        )

    def _analyze_side(
        self,
        prev_row,
        row,
        recent_df,
        side: str,
        regime,
        symbol: str,
        timeframe: str,
        latest_timestamp,
    ) -> Tuple[int, List[ScoreComponent]]:
        components = [
            score_trend(row, side),
            score_momentum(prev_row, row, side),
            score_volume(row, recent_df, side),
            score_structure(row, recent_df, side),
            self._regime_component(side, regime),
            score_risk(row, side),
        ]

        components, learning_state, learning_component = apply_learning_overrides(components)

        # Learning Override در v3.3 فقط وقتی فایل staging وجود داشته باشد در Breakdown دیده می‌شود.
        # اگر فعال نباشد، امتیاز آن صفر است و فقط دلیل/هشدار ایمنی گزارش می‌شود.
        if learning_state.exists:
            components.append(learning_component)

        adaptive_adjustment = score_adaptive_adjustment(
            components=components,
            regime=regime,
            side=side,
        )

        components.append(adaptive_adjustment)

        base_score = max(0, min(100, int(sum(component.points for component in components))))

        historical_edge = score_historical_edge(
            symbol=symbol,
            timeframe=timeframe,
            side=side,
            components=components,
            base_score=base_score,
            current_timestamp=str(latest_timestamp),
        )

        components.append(historical_edge)

        total = sum(component.points for component in components)
        final_score = max(0, min(100, int(total)))

        return final_score, components

    def _select_side(
        self,
        long_score: int,
        long_components: List[ScoreComponent],
        short_score: int,
        short_components: List[ScoreComponent],
    ):
        if long_score >= short_score and long_score >= self.min_side_score:
            return "LONG", long_score, long_components

        if short_score > long_score and short_score >= self.min_side_score:
            return "SHORT", short_score, short_components

        if long_score >= short_score:
            return "NEUTRAL", long_score, long_components

        return "NEUTRAL", short_score, short_components

    def _collect_explanations(self, components: List[ScoreComponent]):
        reasons = []
        warnings = []

        for component in components:
            reasons.extend(component.reasons)
            warnings.extend(component.warnings)

        return reasons, warnings