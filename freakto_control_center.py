"""Streamlit entry point for the unified Freakto control center."""

from pathlib import Path


source = Path(__file__).resolve().parent / "freakto" / "ui" / "control_center.py"
exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"))
