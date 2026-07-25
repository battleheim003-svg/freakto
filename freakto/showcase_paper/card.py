"""Render branded Paper-trade share cards from simulation records."""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 1080, 1350


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _price(value: Any) -> str:
    number = float(value or 0)
    if abs(number) >= 1000:
        return f"{number:,.2f}"
    if abs(number) >= 1:
        return f"{number:,.4f}"
    return f"{number:.6f}"


def _gradient() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#050a10")
    draw = ImageDraw.Draw(image)
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        draw.line((0, y, WIDTH, y), fill=(5 + int(5 * ratio), 10 + int(12 * ratio), 16 + int(18 * ratio)))
    return image


def _decorative_trace(draw: ImageDraw.ImageDraw, seed: str, color: str) -> None:
    rng = random.Random(seed)
    points = []
    value = 0.5
    for index in range(18):
        value = min(0.92, max(0.08, value + rng.uniform(-0.18, 0.2)))
        points.append((470 + index * 34, 610 - int(value * 260)))
    draw.line(points, fill=color, width=7, joint="curve")
    for x, y in points[::3]:
        draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=color)


def render_trade_card(trade: dict[str, Any], output_path: str | Path, *, logo_path: str | Path | None = None) -> Path:
    """Create a 1080x1350 PNG. The card is explicitly marked as simulated."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    image = _gradient()
    draw = ImageDraw.Draw(image, "RGBA")
    side = str(trade.get("side", "LONG")).upper()
    status = str(trade.get("status", "OPEN")).upper()
    pnl_pct = float(trade.get("pnl_pct", 0) or 0)
    accent = "#32e59b" if pnl_pct >= 0 else "#ff6685"
    side_color = "#32e59b" if side == "LONG" else "#ff6685"

    draw.rounded_rectangle((34, 34, WIDTH - 34, HEIGHT - 34), radius=34, outline="#24495b", width=3, fill="#07111be8")
    draw.ellipse((580, 110, 1220, 750), fill="#12334750")
    draw.ellipse((720, 330, 1210, 820), fill="#176c8050")
    _decorative_trace(draw, str(trade.get("trade_id", "trade")), side_color)

    if logo_path and Path(logo_path).is_file():
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((116, 116))
        image.paste(logo, (68, 62), logo)
    draw.text((205, 74), "FREAKTO", font=_font(48, bold=True), fill="#f4fbff")
    draw.text((205, 132), "PAPER SHOWCASE", font=_font(22, bold=True), fill="#53dcd1")
    draw.text((WIDTH - 68, 86), str(trade.get("updated_utc") or trade.get("opened_utc") or "")[:19].replace("T", " "), font=_font(22), fill="#8aa1b0", anchor="ra")

    symbol = str(trade.get("symbol", "—")).replace("/", "")
    draw.text((68, 250), f"{symbol}  PAPER", font=_font(42, bold=True), fill="#f4fbff")
    draw.text((68, 312), f"{status} {side}", font=_font(31, bold=True), fill=side_color)
    draw.text((365, 312), f"{float(trade.get('leverage', 1) or 1):g}x", font=_font(31), fill="#f4fbff")

    pnl_label = "UNREALIZED PnL" if status == "OPEN" else "REALIZED PnL"
    draw.text((68, 420), pnl_label, font=_font(23), fill="#8aa1b0")
    draw.text((68, 458), f"{pnl_pct:+.2f}%", font=_font(82, bold=True), fill=accent)
    draw.text((68, 558), f"{float(trade.get('pnl_usdt', 0) or 0):+.2f} USDT", font=_font(31, bold=True), fill=accent)

    fields = [
        ("Entry Price", _price(trade.get("entry_price"))),
        ("Mark Price" if status == "OPEN" else "Exit Price", _price(trade.get("current_price") or trade.get("exit_price"))),
        ("Stop / Target", f"{_price(trade.get('stop_price'))}  /  {_price(trade.get('target_price'))}"),
        ("Paper Notional", f"{float(trade.get('notional_usdt', 0) or 0):,.2f} USDT"),
    ]
    top = 700
    for index, (label, value) in enumerate(fields):
        y = top + index * 118
        draw.text((68, y), label, font=_font(23), fill="#7892a2")
        draw.text((68, y + 34), value, font=_font(37, bold=True), fill="#f4fbff")

    draw.rounded_rectangle((68, 1196, WIDTH - 68, 1275), radius=18, fill="#0b2b2a", outline="#23746b", width=2)
    draw.text((WIDTH // 2, 1235), "SIMULATED · ZERO REAL CAPITAL · NOT GO-LIVE EVIDENCE", font=_font(20, bold=True), fill="#79e9d5", anchor="mm")
    image.save(path, format="PNG", optimize=True)
    return path
