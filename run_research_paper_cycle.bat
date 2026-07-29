@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Virtual environment not found: .venv\Scripts\python.exe
  pause
  exit /b 1
)

set LIVE_TRADING_ENABLED=false
set REAL_CAPITAL_ENABLED=false
".venv\Scripts\python.exe" -X utf8 -m freakto.cli paper cycle
set EXIT_CODE=%ERRORLEVEL%
pause
exit /b %EXIT_CODE%
