"""
engine.learning_config

Freakto Learning Config & Auto-Tuning Advisor - v3.3.0

این ماژول خروجی Self-Learning Engine را به یک فایل تنظیمات قابل بررسی تبدیل می‌کند.
نکته مهم: این نسخه هنوز هیچ وزن اجرایی را در Decision Engine خودکار تغییر نمی‌دهد.
هدف، ساخت یک لایه امن بین «یادگیری» و «اعمال تغییر» است.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
import json

from .self_learning import (
    build_self_learning_report,
    save_self_learning_report,
    save_recommendations_json,
)


LOGS_DIR = Path("logs")
LEARNING_DIR = LOGS_DIR / "learning"
CONFIG_DIR = Path("config")

RECOMMENDATIONS_FILE = LEARNING_DIR / "self_learning_recommendations.json"
ADVISORY_CONFIG_FILE = LEARNING_DIR / "learning_config_advisory.json"
ADVISORY_REPORT_FILE = LEARNING_DIR / "learning_config_report.md"
STAGED_OVERRIDES_FILE = CONFIG_DIR / "learning_overrides.json"


@dataclass
class TuningAction:
    key: str
    current_value: Any
    proposed_value: Any
    confidence: str
    apply_mode: str
    reason: str
    source_signal: str = ""


@dataclass
class LearningConfigPlan:
    version: str
    created_at_utc: str
    mode: str
    auto_apply: bool
    sample_size: int
    complete_evaluations: int
    data_readiness: str
    summary: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    actions: List[TuningAction] = field(default_factory=list)
    raw_recommendations: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["actions"] = [asdict(action) for action in self.actions]
        return data


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json(path: Path, payload: Dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _data_readiness(complete: int) -> str:
    if complete < 10:
        return "INSUFFICIENT"
    if complete < 30:
        return "OBSERVE_ONLY"
    if complete < 100:
        return "CONSERVATIVE_READY"
    return "READY"


def _step_for_samples(complete: int) -> float:
    """محافظه‌کارانه‌ترین اندازه تغییر پیشنهادی بر اساس تعداد نمونه."""
    if complete < 30:
        return 0.0
    if complete < 100:
        return 0.05
    return 0.10


def _gate_step_for_samples(complete: int) -> int:
    if complete < 30:
        return 0
    if complete < 100:
        return 2
    return 4


def _extract_warning_actions(recommendations: Dict[str, Any]) -> List[Dict[str, Any]]:
    actions = recommendations.get("suggested_actions", [])
    if not isinstance(actions, list):
        return []
    return [item for item in actions if isinstance(item, dict)]


def _add_default_actions(plan: LearningConfigPlan) -> None:
    """همیشه یک baseline قابل خواندن بساز، حتی اگر هیچ هشدار خاصی نباشد."""
    plan.actions.append(
        TuningAction(
            key="learning.auto_apply",
            current_value=False,
            proposed_value=False,
            confidence="HIGH",
            apply_mode="LOCKED",
            reason="اعمال خودکار وزن‌ها تا قبل از رسیدن به نمونه‌های کافی غیرفعال می‌ماند.",
            source_signal="Safety Policy",
        )
    )

    plan.actions.append(
        TuningAction(
            key="learning.min_complete_evaluations_for_auto_tuning",
            current_value=30,
            proposed_value=30,
            confidence="HIGH",
            apply_mode="REFERENCE",
            reason="تا قبل از حداقل 30 ارزیابی کامل، فقط پیشنهاد تولید می‌شود و وزن اجرایی تغییر نمی‌کند.",
            source_signal="Data Readiness",
        )
    )


def _build_actions_from_recommendations(plan: LearningConfigPlan) -> None:
    complete = plan.complete_evaluations
    sample_step = _step_for_samples(complete)
    gate_step = _gate_step_for_samples(complete)
    warning_actions = _extract_warning_actions(plan.raw_recommendations)

    for item in warning_actions:
        name = str(item.get("name", ""))
        status = str(item.get("status", ""))
        evidence = str(item.get("evidence", ""))
        recommendation = str(item.get("recommendation", ""))
        source = f"{name} | {status}"

        if "Component Weight: Volume" in name and status == "QUESTIONABLE":
            if sample_step == 0:
                proposed = 1.00
                mode = "OBSERVE_ONLY"
                confidence = "LOW"
                reason = "Volume در داده فعلی مشکوک است، اما نمونه COMPLETE هنوز برای کاهش وزن کافی نیست."
            else:
                proposed = round(1.00 - sample_step, 2)
                mode = "STAGED"
                confidence = "MEDIUM" if complete >= 30 else "LOW"
                reason = f"Volume طبق Self-Learning اثر ضعیف/معکوس داشته است؛ کاهش آزمایشی {int(sample_step*100)}٪ پیشنهاد می‌شود."

            plan.actions.append(
                TuningAction(
                    key="component_multipliers.volume",
                    current_value=1.00,
                    proposed_value=proposed,
                    confidence=confidence,
                    apply_mode=mode,
                    reason=f"{reason} Evidence: {evidence}",
                    source_signal=source,
                )
            )

        elif "Component Weight: Structure" in name and status == "QUESTIONABLE":
            if sample_step == 0:
                proposed = 1.00
                mode = "OBSERVE_ONLY"
                confidence = "LOW"
                reason = "Structure در داده فعلی مشکوک است، اما نمونه COMPLETE هنوز برای کاهش وزن کافی نیست."
            else:
                proposed = round(1.00 - sample_step, 2)
                mode = "STAGED"
                confidence = "MEDIUM" if complete >= 30 else "LOW"
                reason = f"Structure طبق Self-Learning اثر ضعیف/معکوس داشته است؛ کاهش آزمایشی {int(sample_step*100)}٪ پیشنهاد می‌شود."

            plan.actions.append(
                TuningAction(
                    key="component_multipliers.structure",
                    current_value=1.00,
                    proposed_value=proposed,
                    confidence=confidence,
                    apply_mode=mode,
                    reason=f"{reason} Evidence: {evidence}",
                    source_signal=source,
                )
            )

        elif "Score Bucket" in name and status == "OVERVALUED":
            plan.actions.append(
                TuningAction(
                    key="quality_gate.min_score_delta",
                    current_value=0,
                    proposed_value=gate_step,
                    confidence="MEDIUM" if gate_step else "LOW",
                    apply_mode="STAGED" if gate_step else "OBSERVE_ONLY",
                    reason=f"بازه امتیازی بالا بازده کافی نداده است؛ افزایش محافظه‌کارانه Quality Gate پیشنهاد می‌شود. Evidence: {evidence}",
                    source_signal=source,
                )
            )

        elif "Actionability" in name and status == "TOO_LOOSE":
            plan.actions.append(
                TuningAction(
                    key="quality_gate.actionability_strictness_delta",
                    current_value=0,
                    proposed_value=gate_step,
                    confidence="MEDIUM" if gate_step else "LOW",
                    apply_mode="STAGED" if gate_step else "OBSERVE_ONLY",
                    reason=f"سطح Actionability بیش از حد آسان بوده است؛ سخت‌گیری بیشتر پیشنهاد می‌شود. Evidence: {evidence}",
                    source_signal=source,
                )
            )

        else:
            plan.actions.append(
                TuningAction(
                    key="learning.review_required",
                    current_value=None,
                    proposed_value=None,
                    confidence="LOW",
                    apply_mode="MANUAL_REVIEW",
                    reason=f"سیگنال یادگیری نیاز به بررسی دستی دارد. {recommendation} Evidence: {evidence}",
                    source_signal=source,
                )
            )


def build_learning_config_plan(refresh: bool = False) -> LearningConfigPlan:
    if refresh or not RECOMMENDATIONS_FILE.exists():
        report = build_self_learning_report()
        save_self_learning_report(report)
        save_recommendations_json(report)

    recommendations = _read_json(RECOMMENDATIONS_FILE)
    complete = int(recommendations.get("complete_evaluations", 0) or 0)
    sample_size = int(recommendations.get("sample_size", 0) or 0)
    readiness = _data_readiness(complete)

    plan = LearningConfigPlan(
        version="3.3.0",
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        mode="advisory_config",
        auto_apply=False,
        sample_size=sample_size,
        complete_evaluations=complete,
        data_readiness=readiness,
        raw_recommendations=recommendations,
    )

    plan.summary.append(f"Recommendation source version: {recommendations.get('version', 'unknown')}")
    plan.summary.append(f"Sample size: {sample_size} | Complete evaluations: {complete}")
    plan.summary.append(f"Data readiness: {readiness}")

    if complete < 30:
        plan.warnings.append("نمونه‌های COMPLETE کمتر از 30 است؛ هیچ تغییر اجرایی پیشنهاد نمی‌شود، فقط مانیتورینگ.")
    elif complete < 100:
        plan.warnings.append("نمونه‌ها برای تغییرات کوچک کافی هستند، اما Auto-Apply همچنان خاموش می‌ماند.")

    if not _extract_warning_actions(recommendations):
        plan.summary.append("هیچ هشدار یادگیری جدی پیدا نشد؛ تنظیمات فعلی فعلاً حفظ می‌شوند.")

    _add_default_actions(plan)
    _build_actions_from_recommendations(plan)

    return plan


def plan_to_markdown(plan: LearningConfigPlan) -> str:
    lines: List[str] = []
    lines.append("# Freakto Learning Config Advisory v3.3")
    lines.append("")
    lines.append(f"Created UTC: {plan.created_at_utc}")
    lines.append("")
    lines.append("## Summary")
    for line in plan.summary:
        lines.append(f"- {line}")

    if plan.warnings:
        lines.append("")
        lines.append("## Warnings")
        for warning in plan.warnings:
            lines.append(f"- ⚠️ {warning}")

    lines.append("")
    lines.append("## Proposed Actions")
    if not plan.actions:
        lines.append("- No actions generated.")
    else:
        for action in plan.actions:
            lines.append(f"### {action.key}")
            lines.append(f"- Current: `{action.current_value}`")
            lines.append(f"- Proposed: `{action.proposed_value}`")
            lines.append(f"- Confidence: `{action.confidence}`")
            lines.append(f"- Mode: `{action.apply_mode}`")
            lines.append(f"- Source: {action.source_signal}")
            lines.append(f"- Reason: {action.reason}")
            lines.append("")

    lines.append("## Safety")
    lines.append("- Auto-Apply is OFF in v3.2.")
    lines.append("- This file is advisory/staging only. Decision Engine will not read these overrides yet.")
    lines.append("- Future versions may support opt-in application after enough COMPLETE evaluations are collected.")
    return "\n".join(lines).strip() + "\n"


def format_learning_config_console(plan: LearningConfigPlan) -> str:
    lines: List[str] = []
    lines.append("=" * 110)
    lines.append("🧩 Freakto Learning Config Advisor v3.3")
    lines.append("=" * 110)
    lines.append(f"Created UTC : {plan.created_at_utc}")
    lines.append(f"Mode        : {plan.mode}")
    lines.append(f"Auto Apply  : {plan.auto_apply}")
    lines.append(f"Readiness   : {plan.data_readiness}")
    lines.append(f"Samples     : {plan.sample_size} | Complete: {plan.complete_evaluations}")
    lines.append("")

    if plan.warnings:
        lines.append("Warnings:")
        for warning in plan.warnings:
            lines.append(f"⚠️ {warning}")
        lines.append("")

    lines.append("Proposed Actions:")
    for action in plan.actions:
        lines.append("-" * 110)
        lines.append(f"Key       : {action.key}")
        lines.append(f"Current   : {action.current_value}")
        lines.append(f"Proposed  : {action.proposed_value}")
        lines.append(f"Confidence: {action.confidence}")
        lines.append(f"Mode      : {action.apply_mode}")
        lines.append(f"Reason    : {action.reason}")

    lines.append("=" * 110)
    return "\n".join(lines)


def format_learning_config_telegram(plan: LearningConfigPlan) -> str:
    lines = []
    lines.append("🧩 *Freakto Learning Config v3.3*")
    lines.append(f"Readiness: `{plan.data_readiness}`")
    lines.append(f"Complete evaluations: `{plan.complete_evaluations}`")
    lines.append("Auto-Apply: `OFF`")

    staged = [a for a in plan.actions if a.apply_mode in {"STAGED", "OBSERVE_ONLY", "MANUAL_REVIEW"}]
    if staged:
        lines.append("")
        lines.append("*Top Proposed Actions:*")
        for action in staged[:5]:
            lines.append(f"• `{action.key}` → `{action.proposed_value}` ({action.apply_mode})")

    if plan.warnings:
        lines.append("")
        lines.append("*Warnings:*")
        for warning in plan.warnings[:3]:
            lines.append(f"⚠️ {warning}")

    return "\n".join(lines)


def save_learning_config_plan(plan: LearningConfigPlan) -> Path:
    return _write_json(ADVISORY_CONFIG_FILE, plan.to_dict())


def save_learning_config_report(plan: LearningConfigPlan) -> Path:
    LEARNING_DIR.mkdir(parents=True, exist_ok=True)
    ADVISORY_REPORT_FILE.write_text(plan_to_markdown(plan), encoding="utf-8")
    return ADVISORY_REPORT_FILE


def stage_learning_overrides(plan: LearningConfigPlan) -> Path:
    """یک فایل تنظیمات staging می‌سازد. موتور اصلی هنوز این فایل را اجرا نمی‌کند."""
    staged_actions = [
        asdict(action)
        for action in plan.actions
        if action.apply_mode in {"STAGED", "OBSERVE_ONLY", "MANUAL_REVIEW", "LOCKED", "REFERENCE"}
    ]

    payload = {
        "version": plan.version,
        "created_at_utc": plan.created_at_utc,
        "enabled": False,
        "auto_apply": False,
        "data_readiness": plan.data_readiness,
        "complete_evaluations": plan.complete_evaluations,
        "note": "Staged only by default. Decision Engine v3.3 can read this file, but applies it only if enabled=true, auto_apply=true, readiness is safe, and complete_evaluations is sufficient.",
        "safe_loader_version": "3.3.0",
        "min_complete_evaluations": 30,
        "actions": staged_actions,
    }

    return _write_json(STAGED_OVERRIDES_FILE, payload)
