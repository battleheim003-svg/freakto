@echo off
setlocal
cd /d "%~dp0"
set LIVE_TRADING_ENABLED=false
set REAL_CAPITAL_ENABLED=false
if not exist ".venv\Scripts\python.exe" (echo [خطا] محیط .venv پیدا نشد.& exit /b 1)
".venv\Scripts\python.exe" -X utf8 -m freakto.cli paper preflight || exit /b 1
".venv\Scripts\python.exe" -X utf8 -m freakto.cli paper arm-research || exit /b 1
echo حالت خودکار پژوهشی شروع می‌شود. برای توقف Ctrl+C و سپس stop_paper_trading.bat را اجرا کنید.
echo سرمایه واقعی: صفر
".venv\Scripts\python.exe" -X utf8 -m freakto.cli paper auto
