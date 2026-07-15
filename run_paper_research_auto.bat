@echo off
setlocal
cd /d %~dp0

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Virtual environment not found: .venv\Scripts\python.exe
  echo Create/activate the project virtual environment first.
  pause
  exit /b 1
)

echo ================================================================================
echo Freakto Automated Research Paper Cycle
echo - Runs immediately, then after every closed 4h UTC candle
echo - Daily: incremental history update + Fresh OOS replay
echo - Research/Strategy Paper only; Live orders remain disabled
echo - Press Ctrl+C for a graceful stop
echo ================================================================================

".venv\Scripts\python.exe" -X utf8 paper_research_orchestrator.py --loop
set EXIT_CODE=%ERRORLEVEL%

echo.
echo Orchestrator stopped with exit code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%
