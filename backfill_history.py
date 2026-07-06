"""
backfill_history.py

پر کردن دیتابیس تاریخی Freakto با Snapshotهای کندل‌های گذشته.

اجرا:
    python backfill_history.py

هدف:
ساخت حافظه اولیه برای Historical Similarity Engine.
"""

from config import SYMBOL, TIMEFRAME
from data_fetcher import fetch_ohlcv
from features import add_features
from engine.decision import DecisionEngine
from history_db import save_snapshot, init_history_db


MIN_CANDLES_FOR_ANALYSIS = 100
FETCH_LIMIT = 500


def _extract_provider(df):
    try:
        return df.attrs.get("provider")
    except Exception:
        return None


def _get_timestamp(df):
    if "timestamp" in df.columns:
        return df.iloc[-1]["timestamp"]
    return df.index[-1]


def run_backfill():
    print("=" * 70)
    print("🧠 Freakto History Backfill")
    print("=" * 70)

    init_history_db()

    raw = fetch_ohlcv(
        symbol=SYMBOL,
        timeframe=TIMEFRAME,
        limit=FETCH_LIMIT,
    )

    if raw is None or raw.empty:
        print("❌ داده‌ای دریافت نشد.")
        return

    provider = _extract_provider(raw)

    df = add_features(raw)

    if provider:
        df.attrs["provider"] = provider

    required_columns = [
        "close",
        "rsi_14",
        "bb_high",
        "bb_low",
        "macd_diff",
        "sma_10",
        "sma_30",
        "ema_10",
        "atr_pct",
    ]

    df = df.dropna(subset=required_columns).reset_index(drop=True)

    if len(df) < MIN_CANDLES_FOR_ANALYSIS:
        print("❌ داده کافی برای Backfill وجود ندارد.")
        return

    engine = DecisionEngine(min_side_score=50)

    saved = 0
    skipped = 0
    failed = 0

    for end_index in range(MIN_CANDLES_FOR_ANALYSIS, len(df) + 1):
        window = df.iloc[:end_index].copy()

        if provider:
            window.attrs["provider"] = provider

        latest_timestamp = _get_timestamp(window)
        price = float(window.iloc[-1]["close"])

        try:
            opportunity = engine.analyze(
                window,
                symbol=SYMBOL,
                timeframe=TIMEFRAME,
            )

            was_saved = save_snapshot(
                opportunity=opportunity,
                latest_timestamp=latest_timestamp,
                price=price,
                provider=provider,
            )

            if was_saved:
                saved += 1
            else:
                skipped += 1

        except Exception as error:
            failed += 1
            print(f"⚠️ خطا در Backfill کندل {latest_timestamp}: {type(error).__name__}: {error}")

    print("=" * 70)
    print("✅ Backfill تمام شد")
    print(f"Saved   : {saved}")
    print(f"Skipped : {skipped}")
    print(f"Failed  : {failed}")
    print("=" * 70)


if __name__ == "__main__":
    run_backfill()