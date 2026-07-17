@echo off
cd /d "%~dp0"
set LIVE_TRADING_ENABLED=false
set REAL_CAPITAL_ENABLED=false
".venv\Scripts\python.exe" -X utf8 -m freakto.cli paper cycle

