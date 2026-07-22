"""
engine.learning_overrides

Freakto Safe Learning Override Loader - v3.3.0

این ماژول فایل config/learning_overrides.json را می‌خواند، اما فقط در شرایط امن
اجازه اثرگذاری روی ScoreComponentها را می‌دهد.

قانون ایمنی:
- اگر فایل وجود نداشته باشد: هیچ اثری ندارد.
- اگر enabled یا auto_apply خاموش باشد: فقط گزارش می‌دهد، اعمال نمی‌کند.
- اگر تعداد evaluation کامل کافی نباشد: اعمال نمی‌کند.
- فقط کلیدهای allowlist شده اجازه اثرگذاری دارند.
- تغییر هر مولتی‌پلایر به بازه محافظه‌کارانه محدود می‌شود.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple
import json

from .common import ScoreComponent


OVERRIDES_FILE = Path("config") / "learning_overrides.json"
MIN_COMPLETE_EVALUATIONS = 30
MIN_MULTIPLIER = 0.80
MAX_MULTIPLIER = 1.20

# فقط این کامپوننت‌ها در v3.3 قابل تنظیم هستند.
COMPONENT_KEY_MAP = {
    "component_multipliers.trend": "Trend",
    "component_multipliers.momentum": "Momentum",
    "component_multipliers.volume": "Volume",
    "component_multipliers.structure": "Structure",
    "component_multipliers.regime": "Regime Adjustment",
    "component_multipliers.adaptive": "Adaptive Adjustment",
    "component_multipliers.historical_edge": "Historical Edge",
}


@dataclass
class LearningOverrideState:
    exists: bool = False
    enabled: bool = False
    auto_apply: bool = False
    data_readiness: str = "UNKNOWN"
    complete_evaluations: int = 0
    status: str = "NO_FILE"
    applied: bool = False
    summary: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    multipliers: Dict[str, float] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        return {
            "_read_error": f"{type(error).__name__}: {error}",
        }


def _safe_float(value: Any, default: float = 1.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _clamp_multiplier(value: float) -> float:
    return max(MIN_MULTIPLIER, min(MAX_MULTIPLIER, value))


def load_learning_override_state(path: Path = OVERRIDES_FILE) -> LearningOverrideState:
    payload = _read_json(path)

    if not payload:
        return LearningOverrideState(
            exists=False,
            status="NO_FILE",
            summary=["فایل learning_overrides.json پیدا نشد؛ موتور با وزن‌های پیش‌فرض اجرا می‌شود."],
        )

    if "_read_error" in payload:
        return LearningOverrideState(
            exists=True,
            status="INVALID_FILE",
            warnings=[f"خواندن learning_overrides.json ناموفق بود: {payload['_read_error']}"],
            raw=payload,
        )

    state = LearningOverrideState(
        exists=True,
        enabled=bool(payload.get("enabled", False)),
        auto_apply=bool(payload.get("auto_apply", False)),
        data_readiness=str(payload.get("data_readiness", "UNKNOWN")),
        complete_evaluations=int(payload.get("complete_evaluations", 0) or 0),
        raw=payload,
    )

    if not state.enabled:
        state.status = "DISABLED"
        state.summary.append("Learning overrides موجود است اما enabled=false است؛ هیچ تغییری اعمال نمی‌شود.")
        return state

    if not state.auto_apply:
        state.status = "AUTO_APPLY_OFF"
        state.summary.append("Learning overrides فعال است اما auto_apply=false است؛ فقط مانیتورینگ انجام می‌شود.")
        return state

    if state.complete_evaluations < MIN_COMPLETE_EVALUATIONS:
        state.status = "BLOCKED_INSUFFICIENT_DATA"
        state.warnings.append(
            f"تعداد COMPLETE evaluation کافی نیست: {state.complete_evaluations}/{MIN_COMPLETE_EVALUATIONS}."
        )
        return state

    if state.data_readiness not in {"CONSERVATIVE_READY", "READY"}:
        state.status = "BLOCKED_READINESS"
        state.warnings.append(f"data_readiness هنوز آماده نیست: {state.data_readiness}")
        return state

    actions = payload.get("actions", [])
    if not isinstance(actions, list):
        state.status = "NO_ACTIONS"
        state.warnings.append("ساختار actions در learning_overrides.json معتبر نیست.")
        return state

    for action in actions:
        if not isinstance(action, dict):
            continue

        key = str(action.get("key", ""))
        if key not in COMPONENT_KEY_MAP:
            continue

        mode = str(action.get("apply_mode", ""))
        confidence = str(action.get("confidence", ""))

        # فقط پیشنهادهای staged با اعتماد قابل قبول اجازه اعمال دارند.
        if mode != "STAGED" or confidence not in {"MEDIUM", "HIGH"}:
            continue

        proposed = _clamp_multiplier(_safe_float(action.get("proposed_value"), 1.0))
        component_name = COMPONENT_KEY_MAP[key]
        state.multipliers[component_name] = proposed

    if not state.multipliers:
        state.status = "NO_APPLICABLE_MULTIPLIERS"
        state.summary.append("هیچ مولتی‌پلایر قابل اعمالی در فایل override پیدا نشد.")
        return state

    state.status = "READY_TO_APPLY"
    state.summary.append(
        "Learning overrides شرایط ایمنی را پاس کرده و مولتی‌پلایرهای مجاز اعمال می‌شوند."
    )
    return state


def _adjust_component(component: ScoreComponent, multiplier: float) -> ScoreComponent:
    original = int(component.points)
    adjusted = int(round(original * multiplier))

    # امتیاز را به بازه معقول کامپوننت محدود کن.
    if component.points >= 0:
        adjusted = max(0, min(component.max_points, adjusted))
    else:
        adjusted = max(-component.max_points, min(0, adjusted))

    reasons = list(component.reasons)
    warnings = list(component.warnings)
    metrics = dict(component.metrics)
    metrics["learning_multiplier"] = multiplier
    metrics["learning_original_points"] = original
    metrics["learning_adjusted_points"] = adjusted

    if adjusted != original:
        reasons.append(
            f"Learning Override: {component.name} با ضریب {multiplier:.2f} از {original} به {adjusted} تنظیم شد."
        )

    return ScoreComponent(
        name=component.name,
        points=adjusted,
        max_points=component.max_points,
        direction=component.direction,
        reasons=reasons,
        warnings=warnings,
        metrics=metrics,
    )


def build_learning_override_component(state: LearningOverrideState) -> ScoreComponent:
    reasons: List[str] = []
    warnings: List[str] = []

    if state.status in {"NO_FILE"}:
        return ScoreComponent(
            name="Learning Override",
            points=0,
            max_points=10,
            reasons=[],
            warnings=[],
            metrics={"status": state.status},
        )

    reasons.extend(state.summary)
    warnings.extend(state.warnings)

    if state.applied:
        reasons.append(
            "Learning Override فعال شد: "
            + ", ".join(f"{name}×{value:.2f}" for name, value in state.multipliers.items())
        )
    elif state.status not in {"NO_FILE"}:
        warnings.append(f"Learning Override اعمال نشد. Status={state.status}")

    return ScoreComponent(
        name="Learning Override",
        points=0,
        max_points=10,
        reasons=reasons,
        warnings=warnings,
        metrics={
            "status": state.status,
            "enabled": state.enabled,
            "auto_apply": state.auto_apply,
            "data_readiness": state.data_readiness,
            "complete_evaluations": state.complete_evaluations,
            "applied": state.applied,
            "multipliers": dict(state.multipliers),
        },
    )


def apply_learning_overrides(
    components: List[ScoreComponent],
    path: Path = OVERRIDES_FILE,
) -> Tuple[List[ScoreComponent], LearningOverrideState, ScoreComponent]:
    state = load_learning_override_state(path)

    if state.status != "READY_TO_APPLY":
        return components, state, build_learning_override_component(state)

    adjusted_components: List[ScoreComponent] = []
    changed = False

    for component in components:
        multiplier = state.multipliers.get(component.name)
        if multiplier is None:
            adjusted_components.append(component)
            continue

        adjusted = _adjust_component(component, multiplier)
        if adjusted.points != component.points:
            changed = True
        adjusted_components.append(adjusted)

    state.applied = changed
    if not changed:
        state.status = "READY_BUT_NO_SCORE_CHANGE"
        state.summary.append("مولتی‌پلایرها خوانده شدند اما امتیاز کامپوننت‌ها تغییری نکرد.")

    return adjusted_components, state, build_learning_override_component(state)


def format_learning_override_status_console(state: LearningOverrideState) -> str:
    lines: List[str] = []
    lines.append("=" * 110)
    lines.append("🧪 Freakto Learning Override Status v3.3")
    lines.append("=" * 110)
    lines.append(f"File exists          : {state.exists}")
    lines.append(f"Enabled             : {state.enabled}")
    lines.append(f"Auto Apply          : {state.auto_apply}")
    lines.append(f"Data Readiness      : {state.data_readiness}")
    lines.append(f"Complete Evaluations: {state.complete_evaluations}")
    lines.append(f"Status              : {state.status}")
    lines.append(f"Applied             : {state.applied}")

    if state.multipliers:
        lines.append("")
        lines.append("Multipliers:")
        for name, multiplier in state.multipliers.items():
            lines.append(f"- {name}: {multiplier:.2f}")

    if state.summary:
        lines.append("")
        lines.append("Summary:")
        for item in state.summary:
            lines.append(f"- {item}")

    if state.warnings:
        lines.append("")
        lines.append("Warnings:")
        for item in state.warnings:
            lines.append(f"⚠️ {item}")

    lines.append("=" * 110)
    return "\n".join(lines)
