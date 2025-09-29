@echo off
title Telegram Bot Launcher

echo 🔵 تفعيل البيئة الافتراضية...
call venv\Scripts\activate.bat

echo 🟢 تشغيل البوت...
python main.py

pause
