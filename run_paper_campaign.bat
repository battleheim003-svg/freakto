@echo off
setlocal
cd /d "%~dp0"

set "LIVE_TRADING_ENABLED=false"
set "REAL_CAPITAL_ENABLED=false"
set "PYTHONUTF8=1"

if not exist ".venv\Scripts\python.exe" (
  echo Freakto virtual environment was not found: .venv\Scripts\python.exe 1>&2
  exit /b 2
)

".venv\Scripts\python.exe" -X utf8 -m freakto.paper.orchestrator --loop --no-immediate
exit /b %ERRORLEVEL%
