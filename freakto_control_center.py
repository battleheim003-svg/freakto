"""The only official Streamlit entry point for Freakto."""

from pathlib import Path


source = Path(__file__).resolve().parent / "freakto" / "ui" / "control_center_app.py"
exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"))
