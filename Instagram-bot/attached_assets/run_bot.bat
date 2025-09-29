@echo off
title Telegram Bot Launcher - Powered by Abu Laith


echo 🔵 تفعيل البيئة الافتراضية...
call telegram_bot\venv\Scripts\activate.bat



echo 🟢 تشغيل البوت...
python main.py

pause
