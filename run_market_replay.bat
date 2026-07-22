@echo off
setlocal
cd /d "%~dp0"
set LIVE_TRADING_ENABLED=false
set REAL_CAPITAL_ENABLED=false
if not exist ".venv\Scripts\python.exe" (echo [ERROR] Virtual environment not found.& exit /b 1)
".venv\Scripts\python.exe" -X utf8 -m freakto.cli replay full --symbols BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT,XRP/USDT,DOGE/USDT --timeframe 4h --years 3 --step 6 --compact
set EXIT_CODE=%ERRORLEVEL%
pause
exit /b %EXIT_CODE%
