"""
monitor.py - نقطه شروع Freakto
"""

import time
import argparse
import schedule

from config import (
    SYMBOL,
    TIMEFRAME,
    CHECK_INTERVAL_MINUTES,
    OPPORTUNITY_ENGINE_ENABLED,
    OPPORTUNITY_MIN_SCORE,
    SEND_NEUTRAL_REPORTS,
)

from data_fetcher import fetch_ohlcv
from features import add_features
from telegram_notifier import send_telegram_message
from alert_rules import evaluate_all_rules, ALL_RULES_DESCRIPTION
from opportunity_engine import analyze_opportunity, format_opportunity_message
from decision_logger import log_decision
from history_db import save_snapshot, init_history_db
from engine.similarity import find_similar_snapshots, format_similarity_for_console


_last_checked_timestamp = None


def _send_alert_report(latest_timestamp, price, alerts):
    lines = [
        "📡 *Freakto Market Monitor*",
        f"Symbol: {SYMBOL} | TF: {TIMEFRAME}",
        f"Price: `{price:.2f}`",
        f"Candle: `{latest_timestamp}`",
        "",
    ]

    for alert in alerts:
        lines.append(f"🔸 *{alert['name']}*")
        lines.append(f"   {alert['detail']}")

    lines.append("")
    lines.append("این بخش فقط رخدادهای قابل‌توجه بازار را گزارش می‌کند، نه توصیه خرید/فروش.")
    send_telegram_message("\n".join(lines))


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
    calibrated_probability = opportunity.raw.get("calibrated_probability")
    if calibrated_probability is None:
        print(f"Calibration   : {opportunity.raw.get('calibration_status', 'UNAVAILABLE')}")
    else:
        print(
            f"Calibration   : {calibrated_probability:.1%} "
            f"({opportunity.raw.get('calibration_sample_count', 0)} samples)"
        )
    print(f"Edge Gate     : {'PASS' if opportunity.raw.get('edge_gate_passed') else 'FAIL'}")
    print(f"Risk          : {opportunity.risk_label}")
    print(f"Actionability : {status_icon} {opportunity.actionability_label}")

    if opportunity.raw.get("regime_label"):
        print(
            f"Regime        : {opportunity.raw.get('regime_label')} "
            f"({opportunity.raw.get('regime_confidence')}%)"
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

    if positive_reasons:
        print("\nTop Signals:")
        for reason in positive_reasons[:4]:
            print(f"  ✓ {reason}")

    if risk_warnings:
        print("\nWarnings:")
        for warning in risk_warnings[:4]:
            print(f"  ⚠ {warning}")

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


def _prepare_market_dataframe():
    raw = fetch_ohlcv(limit=220)

    if raw is None or raw.empty:
        print("❌ داده‌ای دریافت نشد.")
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
        print("❌ داده‌ی کافی برای محاسبه‌ی اندیکاتورها وجود ندارد.")
        return None

    return df


def check_market():
    global _last_checked_timestamp

    df = _prepare_market_dataframe()
    if df is None:
        return

    latest_timestamp = _get_latest_timestamp(df)

    if str(latest_timestamp) == str(_last_checked_timestamp):
        print(f"[{latest_timestamp}] کندل تکراری، رد شد.")
        return

    row = df.iloc[-1]
    prev_row = df.iloc[-2]

    price = row["close"]
    atr_rolling_median = df["atr_pct"].tail(30).median()

    alerts = evaluate_all_rules(
        prev_row,
        row,
        atr_rolling_median=atr_rolling_median,
    )

    print(f"[{latest_timestamp}] قیمت: {price:.2f} | هشدارها: {len(alerts)}")

    if alerts:
        _send_alert_report(latest_timestamp, price, alerts)

    if OPPORTUNITY_ENGINE_ENABLED:
        opportunity = analyze_opportunity(
            df,
            symbol=SYMBOL,
            timeframe=TIMEFRAME,
        )

        _print_decision_report(opportunity)

        similarity = find_similar_snapshots(opportunity)
        format_similarity_for_console(similarity)

        provider = _extract_provider(df)

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
            send_telegram_message(format_opportunity_message(opportunity))
            print("✅ پیام تصمیم/فرصت ارسال شد")
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

    print("Freakto شروع شد: Market Monitor + Decision Engine v2")
    print(ALL_RULES_DESCRIPTION)
    print(f"Opportunity Engine: {'ON' if OPPORTUNITY_ENGINE_ENABLED else 'OFF'}")
    print(f"Opportunity Min Score: {OPPORTUNITY_MIN_SCORE}")
    print(f"Send Neutral Reports: {SEND_NEUTRAL_REPORTS}")

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