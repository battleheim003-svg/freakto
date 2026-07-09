"""
monitor.py - نقطه شروع Freakto

نسخه Multi-Timeframe:
- تحلیل تایم‌فریم اصلی پروژه
- تحلیل تایم‌فریم‌های کمکی 1h و 1d
- محاسبه Multi-Timeframe Consensus
- اضافه کردن MTF Consensus به Score Breakdown تایم‌فریم اصلی
- حفظ قابلیت‌های قبلی: --once، تلگرام، Decision Log، History DB، Similarity
"""

import argparse
import time
from typing import Dict, List, Optional, Tuple

import schedule

from config import (
    SYMBOL,
    TIMEFRAME,
    CHECK_INTERVAL_MINUTES,
    OPPORTUNITY_ENGINE_ENABLED,
    OPPORTUNITY_MIN_SCORE,
    SEND_NEUTRAL_REPORTS,
)

from alert_rules import ALL_RULES_DESCRIPTION, evaluate_all_rules
from data_fetcher import fetch_ohlcv
from decision_logger import log_decision
from features import add_features
from history_db import init_history_db, save_snapshot
from opportunity_engine import analyze_opportunity, format_opportunity_message
from telegram_notifier import send_telegram_message
from engine.common import ScoreComponent
from engine.score import confidence_label
from engine.similarity import find_similar_snapshots, format_similarity_for_console
from engine.trade_quality import build_trade_intelligence_card
from engine.intelligence import build_intelligence_report, format_intelligence_console
from engine.causal_intelligence import attach_causal_context
from engine.multi_timeframe import (
    TimeframeSignal,
    calculate_consensus,
    consensus_adjustment,
    console_report as print_consensus_report,
    telegram_lines as format_consensus_telegram_lines,
)


PRIMARY_TIMEFRAME = TIMEFRAME
MULTI_TIMEFRAMES = ["1h", PRIMARY_TIMEFRAME, "1d"]
FETCH_LIMITS = {
    "1h": 260,
    "4h": 220,
    "1d": 220,
}

_last_checked_timestamp = None


def _unique_timeframes(timeframes: List[str]) -> List[str]:
    result = []
    for timeframe in timeframes:
        if timeframe not in result:
            result.append(timeframe)
    return result


def _dedupe_text(items: List[str]) -> List[str]:
    seen = set()
    result = []

    for item in items:
        key = str(item).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)

    return result


def _send_alert_report(latest_timestamp, price, alerts):
    lines = [
        "📡 *Freakto Market Monitor*",
        f"Symbol: {SYMBOL} | TF: {PRIMARY_TIMEFRAME}",
        f"Price: `{price:.2f}`",
        f"Candle: `{latest_timestamp}`",
        "",
    ]

    for alert in alerts:
        lines.append(f"🔸 *{alert['name']}*")
        lines.append(f"   {alert['detail']}")

    lines.append("")
    lines.append("این بخش فقط رخدادهای قابل‌توجه بازار را گزارش می‌کند، نه توصیه خرید/فروش.")

    sent = send_telegram_message("\n".join(lines))
    if sent:
        print("✅ پیام هشدار ارسال شد")
    else:
        print("⚠️ پیام هشدار ارسال نشد")


def _print_decision_report(opportunity):
    status_icon = {
        "HIGH_ACTIONABILITY": "🟢",
        "ACTIONABLE": "🟢",
        "WATCHLIST": "🟡",
        "NOT_ACTIONABLE": "⚪",
        "MONITOR_ONLY": "🔵",
    }.get(opportunity.actionability_label, "⚪")

    print("\n" + "=" * 70)
    print("📊 Freakto Decision Engine")
    print("=" * 70)
    print(f"Bias          : {opportunity.side}")
    print(f"Score         : {opportunity.score}/100 ({opportunity.confidence_label})")
    print(f"Confidence    : {opportunity.confidence.value}% ({opportunity.confidence.label})")
    print(f"Risk          : {opportunity.risk_label}")
    print(f"Actionability : {status_icon} {opportunity.actionability_label}")

    if opportunity.raw.get("regime_label"):
        print(
            f"Regime        : {opportunity.raw.get('regime_label')} "
            f"({opportunity.raw.get('regime_confidence')}%)"
        )

    if opportunity.raw.get("mtf_consensus") is not None:
        print(
            f"MTF Consensus : {opportunity.raw.get('mtf_consensus')}% "
            f"({opportunity.raw.get('mtf_direction')})"
        )

    if opportunity.is_actionable:
        print(f"Entry Zone    : {opportunity.entry_zone}")
        print(f"Stop Zone     : {opportunity.stop_zone}")
        if opportunity.targets:
            print("Targets:")
            for index, target in enumerate(opportunity.targets, start=1):
                print(f"  T{index}: {target}")
    else:
        print("Entry Zone    : ---")
        print("Stop Zone     : ---")

    print("\nScore Breakdown:")
    if opportunity.components:
        for component in opportunity.components:
            sign = "+" if component.points > 0 else ""
            print(f"  - {component.name}: {sign}{component.points}/{component.max_points}")
    else:
        print("  - بدون جزئیات امتیازدهی")

    positive_reasons = []
    risk_warnings = []

    for component in opportunity.components:
        positive_reasons.extend(component.reasons)
        risk_warnings.extend(component.warnings)

    positive_reasons = _dedupe_text(positive_reasons)
    risk_warnings = _dedupe_text(risk_warnings)

    if positive_reasons:
        print("\nTop Signals:")
        for reason in positive_reasons[:5]:
            print(f"  ✓ {reason}")

    if risk_warnings:
        print("\nWarnings:")
        for warning in risk_warnings[:5]:
            print(f"  ⚠ {warning}")

    intelligence_report = build_intelligence_report(opportunity)
    print(format_intelligence_console(intelligence_report))

    trade_card = build_trade_intelligence_card(opportunity)
    if trade_card.is_directional:
        print("\nTrade Intelligence:")
        print(f"  Quality       : {trade_card.quality.grade} ({trade_card.quality.score}/100) - {trade_card.quality.label}")
        if trade_card.rr.is_valid:
            print(f"  Entry/Stop    : {trade_card.rr.entry:.6g} / {trade_card.rr.stop:.6g}")
            print(f"  Stop Distance : {trade_card.rr.stop_distance_pct:.2f}%")
            if trade_card.rr.targets:
                rr_text = ", ".join([f"{target.label}={target.rr:.2f}" for target in trade_card.rr.targets if target.rr is not None])
                print(f"  R:R           : {rr_text}")
        if trade_card.position.is_valid:
            print(f"  Position      : ${trade_card.position.position_notional:,.2f} | Risk ${trade_card.position.risk_amount:,.2f}")
        print(f"  Kelly Risk    : {trade_card.kelly.recommended_risk_pct:.2f}%")
        if trade_card.drawdown.is_valid:
            print(f"  Hist Drawdown : Expected {trade_card.drawdown.expected_drawdown_pct:.2f}% | Worst {trade_card.drawdown.worst_drawdown_pct:.2f}%")

    print("=" * 70)


def _should_send_opportunity(opportunity) -> bool:
    if opportunity.is_actionable:
        return True

    if opportunity.side == "NEUTRAL" and SEND_NEUTRAL_REPORTS:
        return True

    if SEND_NEUTRAL_REPORTS and opportunity.score >= OPPORTUNITY_MIN_SCORE:
        return True

    return False


def _extract_provider(df):
    try:
        return df.attrs.get("provider")
    except Exception:
        return None


def _get_latest_timestamp(df):
    if "timestamp" in df.columns:
        return df.iloc[-1]["timestamp"]
    return df.index[-1]


def _prepare_market_dataframe(symbol=SYMBOL, timeframe=PRIMARY_TIMEFRAME, limit=None):
    limit = limit or FETCH_LIMITS.get(timeframe, 220)

    raw = fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)

    if raw is None or raw.empty:
        print(f"❌ داده‌ای برای {symbol} | {timeframe} دریافت نشد.")
        return None

    provider = _extract_provider(raw)
    df = add_features(raw)

    if provider:
        df.attrs["provider"] = provider

    required_columns = [
        "rsi_14",
        "bb_high",
        "bb_low",
        "macd_diff",
        "sma_10",
        "sma_30",
        "ema_10",
        "atr_pct",
    ]

    df = df.dropna(subset=required_columns)

    if len(df) < 35:
        print(f"❌ داده‌ی کافی برای محاسبه‌ی اندیکاتورها وجود ندارد: {symbol} | {timeframe}")
        return None

    return df


def _build_timeframe_signal(opportunity, timeframe: str) -> TimeframeSignal:
    return TimeframeSignal(
        timeframe=timeframe,
        side=opportunity.side,
        score=int(opportunity.score),
        confidence=int(opportunity.confidence.value),
    )


def _analyze_timeframe(symbol: str, timeframe: str):
    df = _prepare_market_dataframe(
        symbol=symbol,
        timeframe=timeframe,
        limit=FETCH_LIMITS.get(timeframe, 220),
    )

    if df is None:
        return None, None, None, None

    opportunity = analyze_opportunity(
        df,
        symbol=symbol,
        timeframe=timeframe,
    )

    latest_timestamp = _get_latest_timestamp(df)
    price = float(df.iloc[-1]["close"])
    provider = _extract_provider(df)

    return df, opportunity, latest_timestamp, price, provider


def _apply_consensus_to_primary(opportunity, consensus_result):
    adjustment = consensus_adjustment(consensus_result, primary_side=opportunity.side)
    reasons = []
    warnings = []

    if not consensus_result.signals:
        warnings.append("Multi-Timeframe Consensus محاسبه نشد.")
    elif consensus_result.direction == opportunity.side and adjustment > 0:
        reasons.append(
            f"Multi-Timeframe هم‌راستا با Bias اصلی است: {consensus_result.consensus}%"
        )
    elif consensus_result.direction == "NEUTRAL":
        if adjustment < 0:
            warnings.append(
                f"Multi-Timeframe خنثی/ناهم‌راستا است؛ تایم‌فریم‌های بالاتر هنوز Bias {opportunity.side} را تأیید نمی‌کنند: {consensus_result.consensus}%"
            )
        else:
            warnings.append("اجماع تایم‌فریم‌ها خنثی/نامشخص است و تأیید جهت‌دار نمی‌دهد.")
    elif consensus_result.direction != opportunity.side:
        warnings.append(
            f"Multi-Timeframe با Bias اصلی تضاد دارد: {consensus_result.direction} با اجماع {consensus_result.consensus}%"
        )
    elif consensus_result.consensus < 60:
        warnings.append("اجماع تایم‌فریم‌ها ضعیف است؛ کیفیت تصمیم کاهش پیدا می‌کند.")

    component = ScoreComponent(
        name="MTF Consensus",
        points=adjustment,
        max_points=8,
        reasons=reasons,
        warnings=warnings,
    )

    opportunity.components.append(component)
    opportunity.score = max(0, min(100, int(opportunity.score + adjustment)))
    opportunity.confidence_label = confidence_label(opportunity.score)
    opportunity.raw["mtf_consensus"] = consensus_result.consensus
    opportunity.raw["mtf_direction"] = consensus_result.direction
    opportunity.raw["mtf_adjustment"] = adjustment
    opportunity.raw["mtf_quality"] = consensus_result.alignment_quality
    opportunity.raw["mtf_bull_weight"] = consensus_result.bull_weight
    opportunity.raw["mtf_bear_weight"] = consensus_result.bear_weight
    opportunity.raw["mtf_neutral_weight"] = consensus_result.neutral_weight
    opportunity.raw["mtf_signals"] = [
        {
            "timeframe": signal.timeframe,
            "side": signal.side,
            "score": signal.score,
            "confidence": signal.confidence,
            "weight": signal.weight,
        }
        for signal in consensus_result.signals
    ]

    opportunity.reasons = _dedupe_text(opportunity.reasons)
    opportunity.warnings = _dedupe_text(opportunity.warnings)

    return opportunity


def _format_telegram_message(opportunity, consensus_result=None):
    message = format_opportunity_message(opportunity)

    if consensus_result is not None:
        message += "\n\n" + "\n".join(format_consensus_telegram_lines(consensus_result))

    return message


def _analyze_multi_timeframe():
    timeframes = _unique_timeframes(MULTI_TIMEFRAMES)
    results: Dict[str, Tuple] = {}
    signals = []

    print("\n" + "=" * 70)
    print("🕓 شروع تحلیل Multi-Timeframe")
    print("=" * 70)

    for timeframe in timeframes:
        print(f"\n--- تحلیل تایم‌فریم {timeframe} ---")
        result = _analyze_timeframe(SYMBOL, timeframe)
        df, opportunity, latest_timestamp, price, provider = result

        if opportunity is None:
            print(f"⚠️ تحلیل {timeframe} انجام نشد.")
            continue

        results[timeframe] = result
        signals.append(_build_timeframe_signal(opportunity, timeframe))
        print(
            f"✅ {timeframe}: {opportunity.side} | "
            f"Score {opportunity.score} | Confidence {opportunity.confidence.value}%"
        )

    consensus_result = calculate_consensus(signals)
    print_consensus_report(consensus_result)

    primary_result = results.get(PRIMARY_TIMEFRAME)

    if primary_result is None:
        print(f"❌ تایم‌فریم اصلی {PRIMARY_TIMEFRAME} تحلیل نشد.")
        return None, None

    primary_df, primary_opportunity, latest_timestamp, price, provider = primary_result
    primary_opportunity = _apply_consensus_to_primary(primary_opportunity, consensus_result)

    return (
        primary_df,
        primary_opportunity,
        latest_timestamp,
        price,
        provider,
        consensus_result,
    ), results


def check_market():
    global _last_checked_timestamp

    if not OPPORTUNITY_ENGINE_ENABLED:
        df = _prepare_market_dataframe()
        if df is None:
            return

        latest_timestamp = _get_latest_timestamp(df)
        row = df.iloc[-1]
        prev_row = df.iloc[-2]
        price = float(row["close"])
        atr_rolling_median = df["atr_pct"].tail(30).median()

        alerts = evaluate_all_rules(
            prev_row,
            row,
            atr_rolling_median=atr_rolling_median,
        )

        print(f"[{latest_timestamp}] قیمت: {price:.2f} | هشدارها: {len(alerts)}")

        if alerts:
            _send_alert_report(latest_timestamp, price, alerts)

        _last_checked_timestamp = latest_timestamp
        return

    analysis_result, all_results = _analyze_multi_timeframe()

    if analysis_result is None:
        return

    df, opportunity, latest_timestamp, price, provider, consensus_result = analysis_result

    if str(latest_timestamp) == str(_last_checked_timestamp):
        print(f"[{latest_timestamp}] کندل تکراری، رد شد.")
        return

    row = df.iloc[-1]
    prev_row = df.iloc[-2]
    atr_rolling_median = df["atr_pct"].tail(30).median()

    alerts = evaluate_all_rules(
        prev_row,
        row,
        atr_rolling_median=atr_rolling_median,
    )

    print(f"[{latest_timestamp}] قیمت: {price:.2f} | هشدارها: {len(alerts)}")

    if alerts:
        _send_alert_report(latest_timestamp, price, alerts)

    _print_decision_report(opportunity)

    try:
        causal_context = attach_causal_context(
            opportunity,
            df,
            symbol=SYMBOL,
            timeframe=PRIMARY_TIMEFRAME,
            collect_live=False,
        )
        print("\n" + "=" * 70)
        print("🧠 Causal/Event Intelligence Context v6.4")
        print("=" * 70)
        print(f"Primary Cause : {causal_context.primary_cause}")
        print(f"Catalyst      : {causal_context.catalyst_score}/100 | Risk: {causal_context.event_risk}")
        print(f"Conflict      : {causal_context.technical_event_conflict} | Verdict: {causal_context.causal_verdict}")
        print("=" * 70)
    except Exception as error:
        print(f"⚠️ Causal context attach skipped: {type(error).__name__}: {error}")

    similarity = find_similar_snapshots(opportunity)
    format_similarity_for_console(similarity)

    log_decision(
        opportunity=opportunity,
        latest_timestamp=latest_timestamp,
        price=price,
        provider=provider,
    )

    save_snapshot(
        opportunity=opportunity,
        latest_timestamp=latest_timestamp,
        price=price,
        provider=provider,
    )

    if _should_send_opportunity(opportunity):
        sent = send_telegram_message(_format_telegram_message(opportunity, consensus_result))
        if sent:
            print("✅ پیام تصمیم/فرصت ارسال شد")
        else:
            print("⚠️ پیام تصمیم/فرصت ارسال نشد")
    else:
        print("ℹ️ پیام ارسال نشد؛ وضعیت هنوز قابل اقدام یا قابل گزارش نیست.")

    _last_checked_timestamp = latest_timestamp


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one market check and exit.",
    )
    args = parser.parse_args()

    init_history_db()

    print("Freakto شروع شد: Market Monitor + Decision Engine v4 + Intelligence Layer")
    print(ALL_RULES_DESCRIPTION)
    print(f"Opportunity Engine: {'ON' if OPPORTUNITY_ENGINE_ENABLED else 'OFF'}")
    print(f"Opportunity Min Score: {OPPORTUNITY_MIN_SCORE}")
    print(f"Send Neutral Reports: {SEND_NEUTRAL_REPORTS}")
    print(f"Primary Timeframe: {PRIMARY_TIMEFRAME}")
    print(f"Multi-Timeframes: {', '.join(_unique_timeframes(MULTI_TIMEFRAMES))}")

    check_market()

    if args.once:
        print("✅ اجرای یک‌باره انجام شد.")
        return

    schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(check_market)

    while True:
        schedule.run_pending()
        time.sleep(15)


if __name__ == "__main__":
    main()
