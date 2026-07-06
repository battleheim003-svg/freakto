"""
historical_outcomes.py

محاسبه نتیجه تاریخی Snapshotهای ذخیره‌شده در SQLite.

این فایل برای هر Snapshot بررسی می‌کند بعد از آن کندل چه اتفاقی افتاده:
- بازده 4h / 12h / 24h
- آیا حرکت مثبت/منفی بوده
- آیا تارگت‌های ساده 1% / 2% / 3% خورده‌اند
- آیا حرکت خلاف جهت تا حد Stop ساده رفته است

اجرا:
    python historical_outcomes.py
"""

import sqlite3
from pathlib import Path

import pandas as pd

from config import SYMBOL, TIMEFRAME
from data_fetcher import fetch_ohlcv
from history_db import DB_FILE, init_history_db


OUTCOME_HORIZONS = {
    "4h": 1,
    "12h": 3,
    "24h": 6,
}

TARGETS_PCT = {
    "t1": 1.0,
    "t2": 2.0,
    "t3": 3.0,
}

STOP_PCT = 1.2


def _connect():
    return sqlite3.connect(DB_FILE)


def init_outcomes_table():
    init_history_db()

    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS snapshot_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                candle_timestamp TEXT NOT NULL,

                side TEXT,
                entry_price REAL,

                available_future_candles INTEGER,
                evaluation_status TEXT,

                return_after_4h_pct REAL,
                return_after_12h_pct REAL,
                return_after_24h_pct REAL,

                mfe_pct REAL,
                mae_pct REAL,

                t1_hit INTEGER,
                t2_hit INTEGER,
                t3_hit INTEGER,
                stop_hit INTEGER,

                outcome_label TEXT,

                UNIQUE(symbol, timeframe, candle_timestamp)
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_snapshot_outcomes_key
            ON snapshot_outcomes(symbol, timeframe, candle_timestamp)
        """)


def _load_market_data():
    raw = fetch_ohlcv(
        symbol=SYMBOL,
        timeframe=TIMEFRAME,
        limit=500,
    )

    if raw is None or raw.empty:
        print("❌ داده بازار دریافت نشد.")
        return pd.DataFrame()

    df = raw.copy()

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])
        df = df.set_index("timestamp")

    df = df.sort_index()

    return df


def _load_snapshots():
    init_history_db()

    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT
                candle_timestamp,
                symbol,
                timeframe,
                side,
                price
            FROM snapshots
            WHERE symbol = ?
              AND timeframe = ?
            ORDER BY candle_timestamp ASC
        """, (SYMBOL, TIMEFRAME)).fetchall()

    return rows


def _find_candle_index(market_df, timestamp):
    ts = pd.to_datetime(timestamp, errors="coerce")

    if pd.isna(ts):
        return None

    matches = market_df.index[market_df.index == ts]

    if len(matches) == 0:
        return None

    return market_df.index.get_loc(matches[0])


def _directional_return(side, entry_price, future_price):
    if not entry_price or not future_price:
        return None

    change = ((future_price - entry_price) / entry_price) * 100

    if side == "SHORT":
        change *= -1

    return round(change, 4)


def _evaluate_targets(side, entry_price, future_df):
    if future_df.empty or not entry_price:
        return {
            "mfe_pct": None,
            "mae_pct": None,
            "t1_hit": 0,
            "t2_hit": 0,
            "t3_hit": 0,
            "stop_hit": 0,
        }

    highs = future_df["high"].astype(float)
    lows = future_df["low"].astype(float)

    if side == "LONG":
        mfe_pct = ((highs.max() - entry_price) / entry_price) * 100
        mae_pct = ((lows.min() - entry_price) / entry_price) * 100

        t1_hit = int(mfe_pct >= TARGETS_PCT["t1"])
        t2_hit = int(mfe_pct >= TARGETS_PCT["t2"])
        t3_hit = int(mfe_pct >= TARGETS_PCT["t3"])
        stop_hit = int(mae_pct <= -STOP_PCT)

    elif side == "SHORT":
        mfe_pct = ((entry_price - lows.min()) / entry_price) * 100
        mae_pct = ((entry_price - highs.max()) / entry_price) * 100

        t1_hit = int(mfe_pct >= TARGETS_PCT["t1"])
        t2_hit = int(mfe_pct >= TARGETS_PCT["t2"])
        t3_hit = int(mfe_pct >= TARGETS_PCT["t3"])
        stop_hit = int(mae_pct <= -STOP_PCT)

    else:
        mfe_pct = ((highs.max() - entry_price) / entry_price) * 100
        mae_pct = ((lows.min() - entry_price) / entry_price) * 100

        t1_hit = 0
        t2_hit = 0
        t3_hit = 0
        stop_hit = 0

    return {
        "mfe_pct": round(mfe_pct, 4),
        "mae_pct": round(mae_pct, 4),
        "t1_hit": t1_hit,
        "t2_hit": t2_hit,
        "t3_hit": t3_hit,
        "stop_hit": stop_hit,
    }


def _outcome_label(side, return_24h, t1_hit, stop_hit):
    if side not in {"LONG", "SHORT"}:
        return "NEUTRAL"

    if stop_hit and not t1_hit:
        return "LOSS"

    if t1_hit:
        return "WIN"

    if return_24h is None:
        return "PENDING"

    if return_24h >= 1.0:
        return "WIN"

    if return_24h <= -1.0:
        return "LOSS"

    return "FLAT"


def calculate_historical_outcomes():
    print("=" * 70)
    print("📈 Freakto Historical Outcome Engine")
    print("=" * 70)

    init_outcomes_table()

    market_df = _load_market_data()
    if market_df.empty:
        return

    snapshots = _load_snapshots()

    if not snapshots:
        print("ℹ️ هیچ Snapshot تاریخی پیدا نشد.")
        return

    max_horizon = max(OUTCOME_HORIZONS.values())

    saved = 0
    skipped = 0
    pending = 0

    rows_to_insert = []

    for snapshot in snapshots:
        timestamp = snapshot["candle_timestamp"]
        entry_idx = _find_candle_index(market_df, timestamp)

        if entry_idx is None:
            skipped += 1
            continue

        available_future_candles = len(market_df) - entry_idx - 1

        if available_future_candles <= 0:
            pending += 1
            continue

        side = snapshot["side"]
        entry_price = float(snapshot["price"] or 0)

        result = {
            "symbol": snapshot["symbol"],
            "timeframe": snapshot["timeframe"],
            "candle_timestamp": timestamp,
            "side": side,
            "entry_price": entry_price,
            "available_future_candles": available_future_candles,
            "evaluation_status": "PARTIAL",
            "return_after_4h_pct": None,
            "return_after_12h_pct": None,
            "return_after_24h_pct": None,
        }

        completed = 0

        for label, offset in OUTCOME_HORIZONS.items():
            column = f"return_after_{label}_pct"

            if available_future_candles >= offset:
                future_close = float(market_df.iloc[entry_idx + offset]["close"])
                result[column] = _directional_return(
                    side=side,
                    entry_price=entry_price,
                    future_price=future_close,
                )
                completed += 1

        if completed == len(OUTCOME_HORIZONS):
            result["evaluation_status"] = "COMPLETE"

        future_df = market_df.iloc[
            entry_idx + 1:
            entry_idx + min(max_horizon, available_future_candles) + 1
        ]

        target_result = _evaluate_targets(
            side=side,
            entry_price=entry_price,
            future_df=future_df,
        )

        result.update(target_result)

        result["outcome_label"] = _outcome_label(
            side=side,
            return_24h=result["return_after_24h_pct"],
            t1_hit=result["t1_hit"],
            stop_hit=result["stop_hit"],
        )

        rows_to_insert.append(result)

    with _connect() as conn:
        for row in rows_to_insert:
            conn.execute("""
                INSERT OR REPLACE INTO snapshot_outcomes (
                    symbol,
                    timeframe,
                    candle_timestamp,
                    side,
                    entry_price,
                    available_future_candles,
                    evaluation_status,
                    return_after_4h_pct,
                    return_after_12h_pct,
                    return_after_24h_pct,
                    mfe_pct,
                    mae_pct,
                    t1_hit,
                    t2_hit,
                    t3_hit,
                    stop_hit,
                    outcome_label
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["symbol"],
                row["timeframe"],
                row["candle_timestamp"],
                row["side"],
                row["entry_price"],
                row["available_future_candles"],
                row["evaluation_status"],
                row["return_after_4h_pct"],
                row["return_after_12h_pct"],
                row["return_after_24h_pct"],
                row["mfe_pct"],
                row["mae_pct"],
                row["t1_hit"],
                row["t2_hit"],
                row["t3_hit"],
                row["stop_hit"],
                row["outcome_label"],
            ))

            saved += 1

    print("✅ Historical Outcomes محاسبه شد")
    print(f"Saved/Persisted : {saved}")
    print(f"Skipped         : {skipped}")
    print(f"Pending         : {pending}")
    print("=" * 70)


if __name__ == "__main__":
    calculate_historical_outcomes()