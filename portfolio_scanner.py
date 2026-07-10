"""
portfolio_scanner.py

Portfolio Scanner برای Freakto - v4.6.1

اجرا:
    python portfolio_scanner.py
    python portfolio_scanner.py --send
    python portfolio_scanner.py --paper
    python portfolio_scanner.py --symbols BTC/USDT,ETH/USDT,SOL/USDT

این اسکریپت چند نماد را با همان Decision Engine فعلی تحلیل می‌کند،
Multi-Timeframe Consensus می‌سازد، سپس نمادها را رتبه‌بندی می‌کند.
"""

import argparse
import csv
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from config import (
    PORTFOLIO_SYMBOLS,
    PORTFOLIO_TOP_N,
    PORTFOLIO_SEND_TELEGRAM,
    TIMEFRAME,
)
from data_fetcher import fetch_ohlcv
from features import add_features
from opportunity_engine import analyze_opportunity
from telegram_notifier import send_telegram_message
from engine.common import ScoreComponent
from engine.score import confidence_label
from engine.multi_timeframe import (
    TimeframeSignal,
    calculate_consensus,
    consensus_adjustment,
    console_report as print_consensus_report,
)
from engine.portfolio import (
    PortfolioScanResult,
    build_portfolio_item,
    format_portfolio_console,
    format_portfolio_telegram,
)
from engine.market_breadth import calculate_market_breadth
from engine.daily_report import (
    build_daily_report,
    format_daily_report_console,
    format_daily_report_telegram,
    save_daily_report,
)
from engine.market_enrichment import add_live_enrichment_features
from engine.paper_trading import (
    record_paper_trades_from_portfolio,
    format_paper_record_result,
)
from engine.signal_store import init_signal_db, save_portfolio_item_signal


PRIMARY_TIMEFRAME = TIMEFRAME
MULTI_TIMEFRAMES = ["1h", PRIMARY_TIMEFRAME, "1d"]
FETCH_LIMITS = {
    "1h": 260,
    "4h": 220,
    "1d": 220,
}
LOGS_DIR = Path("logs")
PORTFOLIO_LOG_FILE = LOGS_DIR / "portfolio_scans.csv"


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


def _parse_symbols(value: Optional[str]) -> List[str]:
    if not value:
        return list(PORTFOLIO_SYMBOLS)

    symbols = []
    for raw in value.split(","):
        symbol = raw.strip().upper()
        if symbol:
            symbols.append(symbol)

    return symbols or list(PORTFOLIO_SYMBOLS)


def _extract_provider(df):
    try:
        return df.attrs.get("provider")
    except Exception:
        return None


def _get_latest_timestamp(df):
    if "timestamp" in df.columns:
        return df.iloc[-1]["timestamp"]
    return df.index[-1]


def _prepare_market_dataframe(symbol: str, timeframe: str, limit: Optional[int] = None):
    limit = limit or FETCH_LIMITS.get(timeframe, 220)

    raw = fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)

    if raw is None or raw.empty:
        print(f"❌ داده‌ای برای {symbol} | {timeframe} دریافت نشد.")
        return None

    provider = _extract_provider(raw)
    df = add_features(raw)
    df = add_live_enrichment_features(df, symbol=symbol, timeframe=timeframe)

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


def analyze_symbol(symbol: str):
    print("\n" + "#" * 90)
    print(f"🔎 Portfolio Scan: {symbol}")
    print("#" * 90)

    timeframes = _unique_timeframes(MULTI_TIMEFRAMES)
    results: Dict[str, Tuple] = {}
    signals = []

    for timeframe in timeframes:
        print(f"\n--- {symbol} | {timeframe} ---")
        result = _analyze_timeframe(symbol, timeframe)
        df, opportunity, latest_timestamp, price, provider = result

        if opportunity is None:
            print(f"⚠️ تحلیل انجام نشد: {symbol} | {timeframe}")
            continue

        results[timeframe] = result
        signals.append(_build_timeframe_signal(opportunity, timeframe))
        print(
            f"✅ {symbol} {timeframe}: {opportunity.side} | "
            f"Score {opportunity.score} | Confidence {opportunity.confidence.value}%"
        )

    consensus_result = calculate_consensus(signals)
    print_consensus_report(consensus_result)

    primary_result = results.get(PRIMARY_TIMEFRAME)
    if primary_result is None:
        raise RuntimeError(f"Primary timeframe failed: {symbol} | {PRIMARY_TIMEFRAME}")

    df, opportunity, latest_timestamp, price, provider = primary_result
    opportunity = _apply_consensus_to_primary(opportunity, consensus_result)

    item = build_portfolio_item(
        symbol=symbol,
        opportunity=opportunity,
        consensus_result=consensus_result,
        provider=provider,
        price=price,
    )

    return item


def _write_portfolio_log(result: PortfolioScanResult):
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "symbol",
        "timeframe",
        "side",
        "score",
        "confidence",
        "confidence_label",
        "risk_label",
        "actionability",
        "regime",
        "mtf_direction",
        "mtf_consensus",
        "mtf_quality",
        "rank_score",
        "opportunity_score",
        "quality_label",
        "quality_stars",
        "recommendation",
        "trade_quality_grade",
        "trade_quality_score",
        "first_rr",
        "best_rr",
        "recommended_risk_pct",
        "position_notional",
        "expected_drawdown_pct",
        "provider",
        "price",
        "decision_timestamp",
        "entry_zone",
        "stop_zone",
        "targets",
        "breadth_mode",
        "breadth_strength",
        "breadth_market_agreement",
        "breadth_opportunity_strength",
        "breadth_risk_tone",
        "breadth_bullish_pct",
        "breadth_bearish_pct",
        "breadth_neutral_pct",
        "breadth_avg_opportunity",
        "daily_report_file",
        "notes",
    ]

    file_exists = PORTFOLIO_LOG_FILE.exists()

    with PORTFOLIO_LOG_FILE.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for item in result.ranked_items:
            writer.writerow({
                "symbol": item.symbol,
                "timeframe": item.timeframe,
                "side": item.side,
                "score": item.score,
                "confidence": item.confidence,
                "confidence_label": item.confidence_label,
                "risk_label": item.risk_label,
                "actionability": item.actionability,
                "regime": item.regime,
                "mtf_direction": item.mtf_direction,
                "mtf_consensus": item.mtf_consensus,
                "mtf_quality": item.mtf_quality,
                "rank_score": item.rank_score,
                "opportunity_score": item.opportunity_score,
                "quality_label": item.quality_label,
                "quality_stars": item.quality_stars,
                "recommendation": item.recommendation,
                "trade_quality_grade": item.trade_quality_grade,
                "trade_quality_score": item.trade_quality_score,
                "first_rr": item.first_rr,
                "best_rr": item.best_rr,
                "recommended_risk_pct": item.recommended_risk_pct,
                "position_notional": item.position_notional,
                "expected_drawdown_pct": item.expected_drawdown_pct,
                "provider": item.provider,
                "price": item.price,
                "decision_timestamp": item.decision_timestamp,
                "entry_zone": item.entry_zone,
                "stop_zone": item.stop_zone,
                "targets": " | ".join(str(target) for target in item.targets),
                "breadth_mode": result.market_breadth.market_mode if result.market_breadth else "",
                "breadth_strength": result.market_breadth.market_agreement if result.market_breadth else "",
                "breadth_market_agreement": result.market_breadth.market_agreement if result.market_breadth else "",
                "breadth_opportunity_strength": result.market_breadth.opportunity_strength if result.market_breadth else "",
                "breadth_risk_tone": result.market_breadth.risk_tone if result.market_breadth else "",
                "breadth_bullish_pct": result.market_breadth.bullish_pct if result.market_breadth else "",
                "breadth_bearish_pct": result.market_breadth.bearish_pct if result.market_breadth else "",
                "breadth_neutral_pct": result.market_breadth.neutral_pct if result.market_breadth else "",
                "breadth_avg_opportunity": result.market_breadth.average_opportunity_score if result.market_breadth else "",
                "daily_report_file": getattr(result, "daily_report_file", ""),
                "notes": " | ".join(item.notes),
            })

    print(f"🧾 Portfolio scan ذخیره شد: {PORTFOLIO_LOG_FILE}")


def run_portfolio_scan(symbols: List[str] = None, send: bool = False, top_n: int = 8, paper: bool = False) -> PortfolioScanResult:
    symbols = symbols or list(PORTFOLIO_SYMBOLS)
    result = PortfolioScanResult()
    result.daily_report_file = ""
    run_id = "portfolio_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    init_signal_db()

    print("=" * 90)
    print("🏆 Freakto Portfolio Scanner v4.6.1")
    print("=" * 90)
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Primary TF: {PRIMARY_TIMEFRAME}")
    print(f"MTF: {', '.join(_unique_timeframes(MULTI_TIMEFRAMES))}")

    for symbol in symbols:
        try:
            item = analyze_symbol(symbol)
            result.items.append(item)
        except Exception as error:
            print(f"❌ خطا در اسکن {symbol}: {type(error).__name__}: {error}")
            result.failed_symbols.append(symbol)

    result.market_breadth = calculate_market_breadth(result.items)

    daily_report = build_daily_report(result, symbols=symbols)
    report_path = save_daily_report(daily_report)
    result.daily_report_file = str(report_path)

    format_portfolio_console(result, top_n=top_n)
    print(format_daily_report_console(daily_report))
    print(f"🧠 Daily report ذخیره شد: {report_path}")

    _write_portfolio_log(result)
    for item in result.ranked_items:
        save_portfolio_item_signal(item, source="portfolio_scanner", run_id=run_id)

    if paper:
        paper_result = record_paper_trades_from_portfolio(result)
        print(format_paper_record_result(paper_result))

    if send:
        portfolio_sent = send_telegram_message(format_portfolio_telegram(result, top_n=top_n))
        report_sent = send_telegram_message(format_daily_report_telegram(daily_report))

        if portfolio_sent and report_sent:
            print("✅ پیام Portfolio و Daily Report ارسال شد")
        elif portfolio_sent:
            print("⚠️ پیام Portfolio ارسال شد اما Daily Report ارسال نشد")
        elif report_sent:
            print("⚠️ Daily Report ارسال شد اما پیام Portfolio ارسال نشد")
        else:
            print("⚠️ پیام Portfolio و Daily Report ارسال نشدند")

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--symbols",
        type=str,
        default="",
        help="Comma-separated symbols, e.g. BTC/USDT,ETH/USDT,SOL/USDT",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send portfolio summary to Telegram.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=PORTFOLIO_TOP_N,
        help="Number of top results to show/send.",
    )
    parser.add_argument(
        "--paper",
        action="store_true",
        help="Record eligible ACTIONABLE/WATCHLIST candidates as paper trades.",
    )
    args = parser.parse_args()

    symbols = _parse_symbols(args.symbols)
    send = args.send or PORTFOLIO_SEND_TELEGRAM

    run_portfolio_scan(symbols=symbols, send=send, top_n=args.top, paper=args.paper)


if __name__ == "__main__":
    main()
