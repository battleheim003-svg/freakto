from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Callable

import ccxt
import pandas as pd

from config import SYMBOL, TIMEFRAME
from engine.market_data_contract import keep_closed_candles_only
from freakto.paper.cycle_contract import NETWORK_EXHAUSTED_EXIT_CODE


EXCHANGE_ORDER = ["kucoin", "kraken", "bybit", "okx"]


class FetchStatus(str, Enum):
    SUCCESS = "SUCCESS"
    NETWORK_EXHAUSTED = "NETWORK_EXHAUSTED"
    EMPTY_RESPONSE = "EMPTY_RESPONSE"
    NO_CLOSED_CANDLE = "NO_CLOSED_CANDLE"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    DATA_VALIDATION_ERROR = "DATA_VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass(frozen=True)
class ProviderAttempt:
    provider: str
    status: str
    error_type: str | None = None


@dataclass(frozen=True)
class FetchResult:
    frame: pd.DataFrame
    status: FetchStatus
    attempts: tuple[ProviderAttempt, ...]

    @property
    def ok(self) -> bool:
        return self.status is FetchStatus.SUCCESS and not self.frame.empty


def _create_exchange(exchange_name):
    if exchange_name == "okx":
        return ccxt.okx({"enableRateLimit": True})
    if exchange_name == "kucoin":
        return ccxt.kucoin({"enableRateLimit": True})
    if exchange_name == "kraken":
        return ccxt.kraken({"enableRateLimit": True})
    if exchange_name == "bybit":
        return ccxt.bybit(
            {
                "enableRateLimit": True,
                "options": {"defaultType": "spot"},
            }
        )
    raise ValueError(f"Unsupported exchange: {exchange_name}")


def _normalize_symbol_for_exchange(symbol, exchange_name):
    if exchange_name == "kraken" and symbol == "BTC/USDT":
        return "BTC/USDT"
    return symbol


def _to_dataframe(candles, provider):
    frame = pd.DataFrame(
        candles,
        columns=["timestamp", "open", "high", "low", "close", "volume"],
    )
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="ms")
    for column in ["open", "high", "low", "close", "volume"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna().reset_index(drop=True)
    frame.attrs["provider"] = provider
    return frame


def _safe_error(error: Exception) -> str:
    message = re.sub(
        r"(https?://[^\s?]+)\?[^\s]*",
        r"\1?<redacted>",
        str(error),
    )
    message = re.sub(
        r"(?i)\b(api[_-]?key|secret|token|signature)=([^\s&]+)",
        r"\1=<redacted>",
        message,
    )
    return f"{type(error).__name__}: {message[:240]}"


def _error_status(error: Exception) -> str:
    if isinstance(error, ccxt.NetworkError):
        return "NETWORK_ERROR"
    if isinstance(error, (ccxt.BadSymbol, ccxt.AuthenticationError)):
        return FetchStatus.CONFIGURATION_ERROR.value
    if isinstance(error, (TypeError, ValueError, KeyError)):
        return FetchStatus.DATA_VALIDATION_ERROR.value
    return FetchStatus.INTERNAL_ERROR.value


def fetch_ohlcv_result(
    symbol=None,
    timeframe=None,
    limit=220,
    *,
    exchange_order=None,
    exchange_factory: Callable[[str], object] | None = None,
):
    symbol = symbol or SYMBOL
    timeframe = timeframe or TIMEFRAME
    providers = tuple(exchange_order or EXCHANGE_ORDER)
    factory = exchange_factory or _create_exchange

    print("=" * 70)
    print("📥 دریافت کندل‌ها با CCXT")
    print("=" * 70)
    print(f"نماد: {symbol}")
    print(f"تایم‌فریم: {timeframe}")
    print(f"تعداد: {limit}")
    print(f"ترتیب منابع: {', '.join(providers)}")

    last_error = None
    attempts = []
    for exchange_name in providers:
        try:
            print(f"🔎 تلاش با {exchange_name} ...")
            exchange = factory(exchange_name)
            exchange_symbol = _normalize_symbol_for_exchange(symbol, exchange_name)
            candles = exchange.fetch_ohlcv(
                symbol=exchange_symbol,
                timeframe=timeframe,
                limit=limit,
            )
            if not candles:
                attempts.append(
                    ProviderAttempt(exchange_name, FetchStatus.EMPTY_RESPONSE.value)
                )
                continue

            frame = _to_dataframe(candles, provider=exchange_name)
            frame, incomplete_removed = keep_closed_candles_only(frame, timeframe)
            if frame.empty:
                attempts.append(
                    ProviderAttempt(exchange_name, FetchStatus.NO_CLOSED_CANDLE.value)
                )
                continue

            print(f"✅ {len(frame)} کندل از {exchange_name} دریافت شد")
            print(f"آخرین قیمت: {frame['close'].iloc[-1]}")
            print(f"Provider ذخیره شد: {frame.attrs.get('provider')}")
            if incomplete_removed:
                print(f"Incomplete candles removed: {incomplete_removed}")
            attempts.append(ProviderAttempt(exchange_name, FetchStatus.SUCCESS.value))
            return FetchResult(frame, FetchStatus.SUCCESS, tuple(attempts))
        except Exception as error:
            last_error = error
            attempts.append(
                ProviderAttempt(
                    exchange_name,
                    _error_status(error),
                    type(error).__name__,
                )
            )
            print(f"⚠️ {exchange_name} پاسخ نداد: {_safe_error(error)}")

    print("❌ هیچ منبعی موفق نشد.")
    if last_error:
        print(f"آخرین خطا: {_safe_error(last_error)}")

    statuses = {attempt.status for attempt in attempts}
    if attempts and statuses == {"NETWORK_ERROR"}:
        final_status = FetchStatus.NETWORK_EXHAUSTED
    elif FetchStatus.CONFIGURATION_ERROR.value in statuses:
        final_status = FetchStatus.CONFIGURATION_ERROR
    elif FetchStatus.DATA_VALIDATION_ERROR.value in statuses:
        final_status = FetchStatus.DATA_VALIDATION_ERROR
    elif FetchStatus.INTERNAL_ERROR.value in statuses:
        final_status = FetchStatus.INTERNAL_ERROR
    elif FetchStatus.NO_CLOSED_CANDLE.value in statuses:
        final_status = FetchStatus.NO_CLOSED_CANDLE
    else:
        final_status = FetchStatus.EMPTY_RESPONSE

    frame = pd.DataFrame()
    frame.attrs["fetch_status"] = final_status.value
    return FetchResult(frame, final_status, tuple(attempts))


def fetch_ohlcv(symbol=None, timeframe=None, limit=220):
    """Compatibility wrapper returning only the historical DataFrame contract."""
    return fetch_ohlcv_result(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
    ).frame


__all__ = [
    "EXCHANGE_ORDER",
    "FetchResult",
    "FetchStatus",
    "NETWORK_EXHAUSTED_EXIT_CODE",
    "ProviderAttempt",
    "fetch_ohlcv",
    "fetch_ohlcv_result",
]
