from __future__ import annotations

from airdrop.models import ScoredAirdrop


def fmt_money(value: float | None) -> str:
    if value is None:
        return "نامشخص"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:.2f}"


def format_console(scored: ScoredAirdrop) -> str:
    c = scored.candidate
    lines = [
        "=" * 70,
        f"🪂 {c.name} | {scored.level} | Score: {scored.final_score}/100",
        f"Source: {c.source}",
        f"Category: {c.category} | Task: {c.task_type} | Token: {c.token_status}",
        f"TVL: {fmt_money(c.tvl_usd)} | Cost: {fmt_money(c.estimated_cost_usd)} | Time: {c.estimated_minutes or 'نامشخص'} min",
        f"Official: {c.official_url or '---'}",
        f"Source URL: {c.source_url or '---'}",
        "",
        "Score Components:",
    ]
    for comp in scored.components:
        lines.append(f"  - {comp.name}: {comp.score}/{comp.max_score}")
    if scored.positive_reasons:
        lines.append("\nWhy it matters:")
        for reason in scored.positive_reasons[:5]:
            lines.append(f"  ✓ {reason}")
    if scored.warnings:
        lines.append("\nWarnings:")
        for warning in scored.warnings[:5]:
            lines.append(f"  ⚠ {warning}")
    lines.append(f"\nSuggested Action: {scored.action}")
    return "\n".join(lines)


def format_telegram(scored_items: list[ScoredAirdrop]) -> str:
    if not scored_items:
        return "🪂 *Freakto Airdrop Radar*\n\nفرصت قابل گزارش پیدا نشد."

    lines = ["🪂 *Freakto Airdrop Radar*", ""]
    for idx, scored in enumerate(scored_items, start=1):
        c = scored.candidate
        chains = ", ".join(c.chains[:4]) if c.chains else "نامشخص"
        reasons = scored.positive_reasons[:3]
        warnings = scored.warnings[:3]
        lines.extend(
            [
                f"*{idx}. {c.name}*",
                f"Level: {scored.level}",
                f"Score: `{scored.final_score}/100`",
                f"Category: `{_safe(c.category)}` | Task: `{_safe(c.task_type)}`",
                f"Chains: `{_safe(chains)}`",
                f"TVL: `{fmt_money(c.tvl_usd)}` | Cost: `{fmt_money(c.estimated_cost_usd)}` | Time: `{c.estimated_minutes or 'نامشخص'} min`",
            ]
        )
        if c.official_url:
            lines.append(f"Official: {c.official_url}")
        if c.source_url:
            lines.append(f"Source: {c.source_url}")
        if reasons:
            lines.append("Why:")
            lines.extend([f"✓ {r}" for r in reasons])
        if warnings:
            lines.append("Warnings:")
            lines.extend([f"⚠ {w}" for w in warnings])
        lines.append(f"Action: {_safe(scored.action)}")
        lines.append("")
    lines.append("⚠️ این پیام توصیه مالی نیست. از wallet تازه استفاده کن و هیچ private key یا seed phrase وارد نکن.")
    return "\n".join(lines)


def _safe(value: str) -> str:
    return str(value or "").replace("`", "'")
