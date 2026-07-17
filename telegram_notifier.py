"""
telegram_notifier.py - ارسال امن پیام به Telegram

Freakto v3.4.0
- Sanitizes Markdown messages before sending.
- Splits long messages into safe chunks.
- Retries once without parse_mode if Telegram rejects Markdown.
- Avoids printing sensitive bot token / raw Telegram URL.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


TELEGRAM_MAX_MESSAGE_LENGTH = 4096
SAFE_CHUNK_SIZE = 3600
TELEGRAM_TIMEOUT_SECONDS = 12


def _number(value: float, digits: int = 2, suffix: str = "") -> str:
    return f"{float(value):+.{digits}f}{suffix}"


def format_paper_trade_open(trade: dict, *, debug: str = "", mode: str = "NORMAL") -> str:
    """پیام کوتاه و صریح معامله شبیه‌سازی‌شده؛ بدون ارسال شبکه."""
    text = "\n".join([
        "🧪 معامله آزمایشی جدید", "", f"نماد: {trade.get('symbol', 'نامشخص')}",
        f"جهت: {trade.get('side', 'نامشخص')}", f"ورود فرضی: {trade.get('entry', 'نامشخص')}",
        f"حد ضرر: {trade.get('stop', 'نامشخص')}", f"هدف: {trade.get('target', trade.get('target_1', 'نامشخص'))}",
        f"ریسک فرضی: {trade.get('risk_r', 1)}R", f"هزینه تخمینی: {float(trade.get('cost_pct', 0)):.2f}%",
        "", "وضعیت: باز", "سرمایه واقعی: صفر",
    ])
    return text + (f"\n\nجزئیات DEBUG:\n{debug}" if mode.upper() == "DEBUG" and debug else "")


def format_paper_trade_closed(trade: dict, stats: dict, *, debug: str = "", mode: str = "NORMAL") -> str:
    net_r = float(trade.get("net_r", 0)); icon = "✅" if net_r > 0 else "❌"
    label = "سود" if net_r > 0 else "زیان"
    pf = stats.get("profit_factor", 0)
    text = "\n".join([
        f"{icon} معامله آزمایشی بسته شد", "", f"نماد: {trade.get('symbol', 'نامشخص')}",
        f"نتیجه: {_number(net_r)}R", f"{label} خالص فرضی: {_number(trade.get('net_return_pct', 0), suffix='%')}",
        f"علت خروج: {trade.get('close_reason', 'نامشخص')}", f"مدت معامله: {trade.get('duration', 'نامشخص')}", "",
        "آمار کلی:", f"برد/باخت: {stats.get('wins', 0)} / {stats.get('losses', 0)}",
        f"وین‌ریت: {float(stats.get('win_rate_pct', 0)):.1f}%", f"Profit Factor: {pf}",
        f"Expectancy: {_number(stats.get('expectancy_r', 0))}R", f"سود تجمعی: {_number(stats.get('cumulative_r', 0))}R",
        f"Max Drawdown: {float(stats.get('max_drawdown_r', 0)):.2f}R", "سرمایه واقعی: صفر",
    ])
    return text + (f"\n\nجزئیات DEBUG:\n{debug}" if mode.upper() == "DEBUG" and debug else "")


def format_paper_daily_summary(stats: dict) -> str:
    return "\n".join([
        "📊 خلاصه معاملات آزمایشی", "", f"سیگنال‌ها: {stats.get('total_signals', 0)}",
        f"معاملات بسته: {stats.get('closed_trades', 0)}", f"معاملات باز: {stats.get('open_trades', 0)}",
        f"برد/باخت: {stats.get('wins', 0)} / {stats.get('losses', 0)}",
        f"وین‌ریت: {float(stats.get('win_rate_pct', 0)):.1f}%", f"Profit Factor: {stats.get('profit_factor', 0)}",
        f"Expectancy: {_number(stats.get('expectancy_r', 0))}R", f"سود تجمعی: {_number(stats.get('cumulative_r', 0))}R",
        f"Max Drawdown: {float(stats.get('max_drawdown_r', 0)):.2f}R", "", "وضعیت: جمع‌آوری داده پژوهشی", "سرمایه واقعی: صفر",
    ])


@dataclass
class TelegramSendResult:
    ok: bool
    attempted_chunks: int = 0
    sent_chunks: int = 0
    failed_chunks: int = 0
    last_error: str = ""


_MARKDOWN_SPECIALS = {
    "_": r"\_",
    "[": r"\[",
    "]": r"\]",
    "(": r"\(",
    ")": r"\)",
    "~": r"\~",
    "`": r"\`",
    ">": r"\>",
    "#": r"\#",
    "+": r"\+",
    "-": r"\-",
    "=": r"\=",
    "|": r"\|",
    "{": r"\{",
    "}": r"\}",
    ".": r"\.",
    "!": r"\!",
}


def _normalize_message(message: object) -> str:
    if message is None:
        return ""

    text = str(message)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def _strip_unsupported_control_chars(text: str) -> str:
    return "".join(
        ch for ch in text
        if ch == "\n" or ch == "\t" or ord(ch) >= 32
    )


def _chunk_message(text: str, max_len: int = SAFE_CHUNK_SIZE) -> List[str]:
    text = _normalize_message(text)

    if not text:
        return []

    if len(text) <= max_len:
        return [text]

    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for paragraph in text.split("\n"):
        paragraph_len = len(paragraph) + 1

        if paragraph_len > max_len:
            if current:
                chunks.append("\n".join(current).strip())
                current = []
                current_len = 0

            for start in range(0, len(paragraph), max_len):
                chunks.append(paragraph[start:start + max_len].strip())
            continue

        if current_len + paragraph_len > max_len and current:
            chunks.append("\n".join(current).strip())
            current = [paragraph]
            current_len = paragraph_len
        else:
            current.append(paragraph)
            current_len += paragraph_len

    if current:
        chunks.append("\n".join(current).strip())

    return [chunk for chunk in chunks if chunk]


def _escape_markdown_v2(text: str) -> str:
    """
    Escape Telegram MarkdownV2 special characters.

    This function is intentionally conservative. It preserves line breaks but
    escapes characters that often cause Telegram 400 errors when messages contain
    tables, scores, pipes, parentheses, dots, dashes, or exclamation marks.
    """
    escaped = []
    for ch in text:
        escaped.append(_MARKDOWN_SPECIALS.get(ch, ch))
    return "".join(escaped)


def _post_telegram(text: str, parse_mode: Optional[str]) -> tuple[bool, str]:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }

    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        response = requests.post(url, data=payload, timeout=TELEGRAM_TIMEOUT_SECONDS)
    except Exception as exc:
        return False, f"request_error: {exc}"

    if response.status_code == 200:
        return True, ""

    detail = ""
    try:
        body = response.json()
        detail = str(body.get("description", ""))
    except Exception:
        detail = response.text[:300]

    return False, f"http_{response.status_code}: {detail}"


def send_telegram_message(message: str, *, parse_mode: str = "MarkdownV2") -> bool:
    """
    Backward-compatible Telegram sender.

    Returns True only if all chunks are sent successfully.
    """
    result = send_telegram_message_detailed(message, parse_mode=parse_mode)
    return result.ok


def send_telegram_message_detailed(message: str, *, parse_mode: str = "MarkdownV2") -> TelegramSendResult:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram token یا chat ID تنظیم نشده")
        return TelegramSendResult(ok=False, last_error="missing_credentials")

    text = _strip_unsupported_control_chars(_normalize_message(message))

    if not text:
        print("⚠️ پیام Telegram خالی است و ارسال نشد")
        return TelegramSendResult(ok=False, last_error="empty_message")

    raw_chunks = _chunk_message(text)

    if len(raw_chunks) > 1:
        raw_chunks = [
            f"Part {idx}/{len(raw_chunks)}\n\n{chunk}"
            for idx, chunk in enumerate(raw_chunks, start=1)
        ]

    sent = 0
    failed = 0
    last_error = ""

    for chunk in raw_chunks:
        prepared = chunk
        selected_parse_mode: Optional[str] = None

        if parse_mode == "MarkdownV2":
            prepared = _escape_markdown_v2(chunk)
            selected_parse_mode = "MarkdownV2"
        elif parse_mode:
            selected_parse_mode = parse_mode

        ok, error = _post_telegram(prepared, selected_parse_mode)

        if not ok and selected_parse_mode:
            # Fallback for Telegram 400 parse errors or unexpected Markdown issues.
            ok, fallback_error = _post_telegram(chunk, None)
            if not ok:
                error = f"{error} | fallback_plain_failed: {fallback_error}"

        if ok:
            sent += 1
        else:
            failed += 1
            last_error = error
            print(f"❌ خطا در ارسال Telegram: {error}")
            break

    if failed == 0:
        if len(raw_chunks) == 1:
            print("✅ پیام ارسال شد")
        else:
            print(f"✅ پیام Telegram در {len(raw_chunks)} بخش ارسال شد")
        return TelegramSendResult(
            ok=True,
            attempted_chunks=len(raw_chunks),
            sent_chunks=sent,
            failed_chunks=0,
            last_error="",
        )

    return TelegramSendResult(
        ok=False,
        attempted_chunks=len(raw_chunks),
        sent_chunks=sent,
        failed_chunks=failed,
        last_error=last_error,
    )


if __name__ == "__main__":
    test_message = "🔔 تست پیام Telegram - Freakto v3.4"
    send_telegram_message(test_message)
