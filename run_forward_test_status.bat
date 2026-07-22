@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (echo [ERROR] Virtual environment not found.& exit /b 1)
".venv\Scripts\python.exe" -X utf8 -m freakto.cli report forward
set EXIT_CODE=%ERRORLEVEL%
pause
exit /b %EXIT_CODE%
