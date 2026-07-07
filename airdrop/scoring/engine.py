from __future__ import annotations

from datetime import datetime, timezone

from airdrop.models import AirdropCandidate, ScoredAirdrop, ScoreComponent
from airdrop.security.checks import run_security_checks


def score_candidate(candidate: AirdropCandidate) -> ScoredAirdrop:
    components = [
        _credibility(candidate),
        _reward_potential(candidate),
        _traction(candidate),
        _effort_roi(candidate),
        _security(candidate),
        _timing(candidate),
    ]

    raw_score = sum(c.score for c in components)
    final_score = max(0, min(100, raw_score))
    level, action = _level_and_action(final_score, components)

    positive: list[str] = []
    warnings: list[str] = []
    security_flags: list[str] = []
    for component in components:
        positive.extend(component.reasons)
        warnings.extend(component.warnings)
        if component.name == "Security":
            security_flags.extend(component.warnings)

    return ScoredAirdrop(
        candidate=candidate,
        final_score=final_score,
        level=level,
        action=action,
        components=components,
        positive_reasons=positive[:8],
        warnings=warnings[:10],
        security_flags=security_flags,
    )


def _credibility(c: AirdropCandidate) -> ScoreComponent:
    score = 0
    reasons: list[str] = []
    warnings: list[str] = []

    trusted_sources = {"defillama_protocols", "configured_watchlist"}
    if c.source in trusted_sources:
        score += 5
        reasons.append(f"از منبع قابل‌پیگیری دریافت شده: {c.source}")

    if c.official_url:
        score += 5
        reasons.append("لینک رسمی پروژه موجود است.")
    else:
        warnings.append("لینک رسمی ندارد؛ اقدام مستقیم نکن.")

    if c.docs_url:
        score += 3
        reasons.append("مستندات رسمی/فنی دارد.")

    if c.twitter_url or c.discord_url:
        score += 3
        reasons.append("کانال اجتماعی رسمی برای پیگیری دارد.")

    if c.funding or c.investors:
        score += 8
        reasons.append("اطلاعات funding/investor برای اعتبارسنجی وجود دارد.")

    if c.priority_hint > 0:
        score += min(6, c.priority_hint)
        reasons.append("در watchlist دستی اولویت مثبت گرفته است.")
    elif c.priority_hint < 0:
        score += max(-8, c.priority_hint)
        warnings.append("در watchlist دستی هشدار/اولویت منفی دارد.")

    return ScoreComponent("Credibility", max(0, min(30, score)), 30, reasons, warnings)


def _reward_potential(c: AirdropCandidate) -> ScoreComponent:
    score = 0
    reasons: list[str] = []
    warnings: list[str] = []

    if c.token_status in {"no-token-confirmed", "tokenless-likely"}:
        score += 8
        reasons.append("پروژه توکن مشخص ندارد یا tokenless-likely است.")
    elif c.token_status == "has-token-or-unknown":
        score += 2
        warnings.append("پروژه احتمالاً توکن دارد یا وضعیت توکن نامشخص است.")
    else:
        score += 4
        warnings.append("وضعیت توکن قطعی نیست.")

    if c.funding or c.investors:
        score += 4
        reasons.append("وجود funding/investor می‌تواند پتانسیل پاداش را بهتر کند.")

    if c.task_type in {"testnet", "protocol interaction", "bridge", "staking", "points", "quest"}:
        score += 4
        reasons.append(f"نوع فعالیت قابل ردیابی است: {c.task_type}")

    if any(tag in c.tags for tag in ["points", "incentive", "season", "testnet", "tokenless"]):
        score += 4
        reasons.append("برچسب‌های مرتبط با ایردراپ/امتیاز دارد.")

    return ScoreComponent("Reward Potential", max(0, min(20, score)), 20, reasons, warnings)


def _traction(c: AirdropCandidate) -> ScoreComponent:
    score = 0
    reasons: list[str] = []
    warnings: list[str] = []

    if c.tvl_usd is not None:
        if c.tvl_usd >= 100_000_000:
            score += 10
            reasons.append("TVL بالای 100M دلار دارد.")
        elif c.tvl_usd >= 10_000_000:
            score += 7
            reasons.append("TVL بالای 10M دلار دارد.")
        elif c.tvl_usd >= 1_000_000:
            score += 4
            reasons.append("TVL بالای 1M دلار دارد.")
        else:
            score += 1
            warnings.append("TVL پایین است.")
    else:
        warnings.append("داده TVL ندارد.")

    if c.volume_usd and c.volume_usd >= 1_000_000:
        score += 3
        reasons.append("حجم/استفاده قابل توجه گزارش شده است.")
    if c.fees_24h_usd and c.fees_24h_usd >= 10_000:
        score += 2
        reasons.append("Fee روزانه قابل توجه دارد.")
    if len(c.chains) >= 2:
        score += 2
        reasons.append("روی چند chain فعال است.")

    return ScoreComponent("On-chain Traction", max(0, min(15, score)), 15, reasons, warnings)


def _effort_roi(c: AirdropCandidate) -> ScoreComponent:
    score = 9
    reasons: list[str] = []
    warnings: list[str] = []

    if c.estimated_minutes is not None:
        if c.estimated_minutes <= 20:
            score += 3
            reasons.append("زمان انجام پایین است.")
        elif c.estimated_minutes <= 60:
            score += 1
            reasons.append("زمان انجام متوسط است.")
        else:
            score -= 4
            warnings.append("زمان انجام زیاد است؛ فقط اگر امتیاز کلی بالا بود انجام شود.")

    if c.estimated_cost_usd is not None:
        if c.estimated_cost_usd <= 5:
            score += 3
            reasons.append("هزینه تخمینی پایین است.")
        elif c.estimated_cost_usd <= 25:
            score += 1
            reasons.append("هزینه تخمینی متوسط است.")
        else:
            score -= 5
            warnings.append("هزینه تخمینی بالا است؛ با wallet اصلی انجام نده.")

    if c.task_type in {"node", "validator", "ambassador"}:
        score -= 3
        warnings.append("نوع فعالیت زمان‌بر/عملیاتی است.")

    return ScoreComponent("Effort / Cost ROI", max(0, min(15, score)), 15, reasons, warnings)


def _security(c: AirdropCandidate) -> ScoreComponent:
    score, warnings, flags = run_security_checks(c)
    reasons = []
    if score >= 15:
        reasons.append("بررسی اولیه دامنه/امنیت مشکل جدی نشان نداد.")
    if flags:
        warnings.extend(flags)
        score = min(score, 8)
    return ScoreComponent("Security", max(0, min(20, score)), 20, reasons, warnings)


def _timing(c: AirdropCandidate) -> ScoreComponent:
    score = 2
    reasons: list[str] = []
    warnings: list[str] = []
    if c.deadline:
        try:
            deadline = datetime.fromisoformat(c.deadline.replace("Z", "+00:00"))
            days = (deadline - datetime.now(timezone.utc)).days
            if days < 0:
                score = 0
                warnings.append("deadline گذشته است.")
            elif days <= 7:
                score = 5
                reasons.append("deadline نزدیک است؛ اولویت زمانی دارد.")
            elif days <= 45:
                score = 4
                reasons.append("deadline مشخص و قابل برنامه‌ریزی دارد.")
            else:
                score = 3
                reasons.append("deadline مشخص است اما فوری نیست.")
        except ValueError:
            score = 3
            warnings.append("deadline قابل parse نبود؛ دستی بررسی شود.")
    else:
        warnings.append("زمان snapshot/deadline مشخص نیست.")
    return ScoreComponent("Timing", max(0, min(5, score)), 5, reasons, warnings)


def _level_and_action(final_score: int, components: list[ScoreComponent]) -> tuple[str, str]:
    security = next((c.score for c in components if c.name == "Security"), 0)
    if security <= 5:
        return "🔴 AVOID", "Avoid: security risk is too high or official link is missing."
    if final_score >= 85:
        return "🟢 ELITE", "Actionable: do low-risk tasks with a fresh wallet after final manual URL check."
    if final_score >= 70:
        return "🟢 ACTIONABLE", "Actionable: worth doing after final manual review."
    if final_score >= 55:
        return "🟡 WATCHLIST", "Watchlist: monitor and do only very low-cost tasks."
    if final_score >= 40:
        return "🔵 MONITOR ONLY", "Monitor only: wait for stronger evidence."
    return "🔴 AVOID", "Avoid: weak reward/risk profile."
