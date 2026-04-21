@echo off
cd /d "%~dp0farming-bot\coinbot"
echo Checking Coinbot Status...
python status.py
pause
