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
SYMBOLS = _get_list(
    "SYMBOLS",
    os.getenv("PORTFOLIO_SYMBOLS", os.getenv("SYMBOL", "BTC/USDT")),
)
SYMBOL = os.getenv("SYMBOL", SYMBOLS[0] if SYMBOLS else "BTC/USDT")
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
GAPGPT_API_KEY = os.getenv("GAPGPT_API_KEY", "").strip() or OPENAI_API_KEY
GAPGPT_BASE_URL = os.getenv("GAPGPT_BASE_URL", "").strip() or "https://api.gapgpt.app/v1"
GAPGPT_MODEL = os.getenv("GAPGPT_MODEL", "").strip() or OPENAI_MODEL
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

# ========== External feature enrichment ==========
ENABLE_CROSS_EXCHANGE_VOLUME = _get_bool("ENABLE_CROSS_EXCHANGE_VOLUME", False)
ENABLE_NEWS_SENTIMENT = _get_bool("ENABLE_NEWS_SENTIMENT", False)
ENABLE_ONCHAIN_FEATURES = _get_bool("ENABLE_ONCHAIN_FEATURES", False)
CROSS_EXCHANGE_VOLUME_LIMIT = int(os.getenv("CROSS_EXCHANGE_VOLUME_LIMIT", "80"))
GLASSNODE_API_KEY = os.getenv("GLASSNODE_API_KEY", "")
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")

# ========== Model Lab ==========
MODEL_TYPE = os.getenv("MODEL_TYPE", "auto")
MODEL_LAB_OUTPUT_DIR = os.getenv("MODEL_LAB_OUTPUT_DIR", str(BASE_DIR / "logs" / "model_lab"))

# ========== Trade Intelligence v2.7 ==========
TRADE_ACCOUNT_SIZE = float(os.getenv("TRADE_ACCOUNT_SIZE", "10000"))
TRADE_RISK_PCT = float(os.getenv("TRADE_RISK_PCT", "1.0"))
TRADE_MAX_RISK_PCT = float(os.getenv("TRADE_MAX_RISK_PCT", "2.0"))

# ========== Airdrop Radar ==========
AIRDROP_MIN_SCORE = int(os.getenv("AIRDROP_MIN_SCORE", "65"))
AIRDROP_MAX_ITEMS_PER_RUN = int(os.getenv("AIRDROP_MAX_ITEMS_PER_RUN", "8"))
AIRDROP_CHECK_INTERVAL_MINUTES = int(os.getenv("AIRDROP_CHECK_INTERVAL_MINUTES", "360"))
AIRDROP_USE_DEFILLAMA = _get_bool("AIRDROP_USE_DEFILLAMA", True)
AIRDROP_DEFILLAMA_MIN_TVL = float(os.getenv("AIRDROP_DEFILLAMA_MIN_TVL", "1000000"))
AIRDROP_DEFILLAMA_MAX_ITEMS = int(os.getenv("AIRDROP_DEFILLAMA_MAX_ITEMS", "200"))
AIRDROP_WATCHLIST_FILE = os.getenv("AIRDROP_WATCHLIST_FILE", str(BASE_DIR / "data" / "airdrop_watchlist.json"))
AIRDROP_DB_PATH = os.getenv("AIRDROP_DB_PATH", str(BASE_DIR / "history" / "airdrop_radar.db"))
AIRDROP_RSS_FEEDS = os.getenv("AIRDROP_RSS_FEEDS", "")
AIRDROP_DOMAIN_BLACKLIST = os.getenv("AIRDROP_DOMAIN_BLACKLIST", "")
GOPLUS_API_TOKEN = os.getenv("GOPLUS_API_TOKEN", "")
