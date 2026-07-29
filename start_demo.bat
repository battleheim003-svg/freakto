@echo off
setlocal
set "ROOT=%~dp0"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
  echo [BLOCKED] Project virtual environment not found: "%PYTHON%" 1>&2
  exit /b 2
)
"%PYTHON%" -X utf8 "%ROOT%start_demo.py" %*
exit /b %ERRORLEVEL%
