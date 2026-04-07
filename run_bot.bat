@echo off
:START
echo Starting SMT BOT...
python bot.py
echo BOT CRASHED - RESTARTING...
timeout /t 5
goto START
