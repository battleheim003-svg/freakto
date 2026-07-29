@echo off
setlocal
cd /d "%~dp0"
set LIVE_TRADING_ENABLED=false
set REAL_CAPITAL_ENABLED=false
if not exist ".venv\Scripts\python.exe" (echo [ERROR] Virtual environment not found.& exit /b 1)
".venv\Scripts\python.exe" -X utf8 -m streamlit run freakto_control_center.py --server.headless true
exit /b %ERRORLEVEL%
