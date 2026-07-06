import pandas as pd
import ccxt
from config import SYMBOL, TIMEFRAME


EXCHANGE_ORDER = ["kucoin", "kraken", "bybit", "okx"]


def _create_exchange(exchange_name):
    if exchange_name == "okx":
        return ccxt.okx({"enableRateLimit": True})

    if exchange_name == "kucoin":
        return ccxt.kucoin({"enableRateLimit": True})

    if exchange_name == "kraken":
        return ccxt.kraken({"enableRateLimit": True})

    if exchange_name == "bybit":
        return ccxt.bybit({
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        })

    raise ValueError(f"Unsupported exchange: {exchange_name}")


def _normalize_symbol_for_exchange(symbol, exchange_name):
    if exchange_name == "kraken" and symbol == "BTC/USDT":
        return "BTC/USDT"

    return symbol


def _to_dataframe(candles, provider):
    df = pd.DataFrame(
        candles,
        columns=["timestamp", "open", "high", "low", "close", "volume"],
    )

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna().reset_index(drop=True)

    df.attrs["provider"] = provider

    return df


def fetch_ohlcv(symbol=None, timeframe=None, limit=220):
    symbol = symbol or SYMBOL
    timeframe = timeframe or TIMEFRAME

    print("=" * 70)
    print("📥 دریافت کندل‌ها با CCXT")
    print("=" * 70)
    print(f"نماد: {symbol}")
    print(f"تایم‌فریم: {timeframe}")
    print(f"تعداد: {limit}")
    print(f"ترتیب منابع: {', '.join(EXCHANGE_ORDER)}")

    last_error = None

    for exchange_name in EXCHANGE_ORDER:
        try:
            print(f"🔎 تلاش با {exchange_name} ...")

            exchange = _create_exchange(exchange_name)
            exchange_symbol = _normalize_symbol_for_exchange(symbol, exchange_name)

            candles = exchange.fetch_ohlcv(
                symbol=exchange_symbol,
                timeframe=timeframe,
                limit=limit,
            )

            if not candles:
                raise RuntimeError("No candles returned")

            df = _to_dataframe(candles, provider=exchange_name)

            print(f"✅ {len(df)} کندل از {exchange_name} دریافت شد")
            print(f"آخرین قیمت: {df['close'].iloc[-1]}")
            print(f"Provider ذخیره شد: {df.attrs.get('provider')}")

            return df

        except Exception as error:
            last_error = error
            print(f"⚠️ {exchange_name} جواب نداد: {type(error).__name__}: {error}")

    print("❌ هیچ منبعی موفق نشد.")
    if last_error:
        print(f"آخرین خطا: {type(last_error).__name__}: {last_error}")

    return pd.DataFrame()