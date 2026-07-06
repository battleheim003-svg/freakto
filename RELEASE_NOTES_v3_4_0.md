# Freakto v3.4.0 — Telegram Reliability & Message Sanitizer

## Goal

This release improves Telegram delivery reliability and fixes common `400 Bad Request` failures caused by Markdown formatting, long messages, and unsafe characters in generated reports.

## Added

- Safer Telegram message sender in `telegram_notifier.py`
- MarkdownV2 sanitizer
- Automatic long-message chunking
- Fallback plain-text retry if Telegram rejects Markdown
- Sensitive URL/token-safe error logging
- New diagnostic CLI:

```bash
python telegram_diagnostics.py
python telegram_diagnostics.py --long
```

## Changed

- `send_telegram_message()` remains backward-compatible and still returns `True` / `False`.
- Internally it now uses `send_telegram_message_detailed()`.
- Existing callers do not need to change.

## Why this matters

Previous logs showed Telegram returning `400`, most likely because of Markdown parsing issues in long, table-like, or symbol-rich messages. v3.4 reduces those failures by escaping MarkdownV2 characters and retrying without parse mode when needed.

## Test

```bash
python telegram_diagnostics.py
python telegram_diagnostics.py --long
python monitor.py --once
python portfolio_scanner.py --send
```
