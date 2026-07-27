@echo off
setlocal
cd /d "%~dp0"
set "LIVE_TRADING_ENABLED=false"
set "REAL_CAPITAL_ENABLED=false"
set "LIVE_DEMO_EXECUTION_ENABLED=false"
set "FREAKTO_OPERATIONAL_ROOT=%CD%"

if not exist ".venv\Scripts\python.exe" (
  echo Freakto virtual environment not found: .venv\Scripts\python.exe
  exit /b 1
)

".venv\Scripts\python.exe" -X utf8 -m streamlit run live_paper_web_dashboard.py
exit /b %ERRORLEVEL%
