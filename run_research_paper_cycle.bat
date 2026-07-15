@echo off
setlocal
cd /d %~dp0

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Virtual environment not found: .venv\Scripts\python.exe
  pause
  exit /b 1
)

".venv\Scripts\python.exe" -X utf8 paper_research_orchestrator.py --once
set EXIT_CODE=%ERRORLEVEL%
pause
exit /b %EXIT_CODE%
