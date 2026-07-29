@echo off
setlocal
cd /d "%~dp0"
echo [DEPRECATED] Paper Dashboard is now Spot Paper Trading in Control Center. 1>&2
call "%~dp0run_control_center.bat"
exit /b %ERRORLEVEL%
