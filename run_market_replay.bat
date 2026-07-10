@echo off
set PYTHONUTF8=1
python -X utf8 market_replay_dashboard.py --full --symbols BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT,XRP/USDT,DOGE/USDT --timeframe 4h --years 3 --step 6 --compact
pause
