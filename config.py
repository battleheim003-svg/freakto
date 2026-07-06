"""
config.py - تنظیمات مرکزی پروژه

مقادیر حساس مثل API Key و Token نباید داخل کد ذخیره شوند.
این فایل ابتدا .env کنار پروژه را می‌خواند و سپس از متغیرهای محیطی مقدار می‌گیرد.
برای شروع، .env.example را کپی کن و با نام .env ذخیره کن.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent


def _load_dotenv(path: Path = BASE_DIR / ".env") -> None:
    """لود ساده‌ی فایل .env بدون وابستگی اضافی."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_list(name: str, default: str = "") -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]



_load_dotenv()

# ========== مسیرهای فایل‌ها ==========
MODEL_PATH = BASE_DIR / os.getenv("MODEL_PATH", "model.joblib")
PAPER_TRADING_LOG_FILE = BASE_DIR / os.getenv("PAPER_TRADING_LOG_FILE", "paper_trading_log.json")
LIVE_DATA_LOG_FILE = BASE_DIR / os.getenv("LIVE_DATA_LOG_FILE", "live_enriched_data_log.csv")

# ========== تنظیمات WunderTrading ==========
WUNDERTRADING_API_KEY = os.getenv("WUNDERTRADING_API_KEY", "")
WUNDERTRADING_PASSWORD = os.getenv("WUNDERTRADING_PASSWORD", "")
WUNDERTRADING_BASE_URL = os.getenv("WUNDERTRADING_BASE_URL", "https://api.wundertrading.com")

# ========== تنظیمات بازار ==========
EXCHANGE_ID = os.getenv("EXCHANGE_ID", "okx")
SYMBOL = os.getenv("SYMBOL", "BTC/USDT")
TIMEFRAME = os.getenv("TIMEFRAME", "4h")
CANDLES_LIMIT = int(os.getenv("CANDLES_LIMIT", "1000"))
TRAINING_CANDLES = int(os.getenv("TRAINING_CANDLES", "12000"))

# ========== تنظیمات لیبل‌گذاری / مدل‌های قدیمی ==========
LOOKAHEAD_CANDLES = int(os.getenv("LOOKAHEAD_CANDLES", "1"))
ATR_MULTIPLIER = float(os.getenv("ATR_MULTIPLIER", "0.3"))
TRAIN_WINDOW_CANDLES = int(os.getenv("TRAIN_WINDOW_CANDLES", "2000"))
RETRAIN_STEP_CANDLES = int(os.getenv("RETRAIN_STEP_CANDLES", "180"))
MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.50"))

# ========== Paper Trading ==========
PAPER_TRADING_ENABLED = _get_bool("PAPER_TRADING_ENABLED", True)
PAPER_TRADING_SOURCE = os.getenv("PAPER_TRADING_SOURCE", "wundertrading")
PAPER_TRADING_BALANCE = float(os.getenv("PAPER_TRADING_BALANCE", "10000"))
PAPER_TRADING_POSITION_SIZE = float(os.getenv("PAPER_TRADING_POSITION_SIZE", "0.1"))
PAPER_TRADING_MAKER_FEE = float(os.getenv("PAPER_TRADING_MAKER_FEE", "0.001"))
PAPER_TRADING_TAKER_FEE = float(os.getenv("PAPER_TRADING_TAKER_FEE", "0.0015"))

# ========== API KEYS ==========
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
COINALYZE_API_KEY = os.getenv("COINALYZE_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ========== اجرای زنده ==========
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "60"))
# ========== Opportunity Engine ==========
OPPORTUNITY_ENGINE_ENABLED = _get_bool("OPPORTUNITY_ENGINE_ENABLED", True)
OPPORTUNITY_MIN_SCORE = int(os.getenv("OPPORTUNITY_MIN_SCORE", "70"))
SEND_NEUTRAL_REPORTS = _get_bool("SEND_NEUTRAL_REPORTS", False)
# ========== Portfolio Scanner ==========
PORTFOLIO_SYMBOLS = _get_list(
    "PORTFOLIO_SYMBOLS",
    "BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT,XRP/USDT,DOGE/USDT",
)
PORTFOLIO_TOP_N = int(os.getenv("PORTFOLIO_TOP_N", "8"))
PORTFOLIO_SEND_TELEGRAM = _get_bool("PORTFOLIO_SEND_TELEGRAM", False)


# ========== Portfolio Scanner v2.6 ==========
PORTFOLIO_MIN_OPPORTUNITY_SCORE = float(os.getenv("PORTFOLIO_MIN_OPPORTUNITY_SCORE", "55"))
PORTFOLIO_ELITE_SCORE = float(os.getenv("PORTFOLIO_ELITE_SCORE", "85"))
PORTFOLIO_ACTIONABLE_SCORE = float(os.getenv("PORTFOLIO_ACTIONABLE_SCORE", "72"))
PORTFOLIO_WATCHLIST_SCORE = float(os.getenv("PORTFOLIO_WATCHLIST_SCORE", "55"))
PORTFOLIO_SHOW_MONITOR_CANDIDATES = _get_bool("PORTFOLIO_SHOW_MONITOR_CANDIDATES", True)

# ========== Trade Intelligence v2.7 ==========
TRADE_ACCOUNT_SIZE = float(os.getenv("TRADE_ACCOUNT_SIZE", "10000"))
TRADE_RISK_PCT = float(os.getenv("TRADE_RISK_PCT", "1.0"))
TRADE_MAX_RISK_PCT = float(os.getenv("TRADE_MAX_RISK_PCT", "2.0"))
