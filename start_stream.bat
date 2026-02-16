@echo off
REM Скрипт запуска стрима для ai_avatars_stream (Windows)

echo Starting AI Avatars Stream...

REM Активация виртуального окружения
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Запуск главного скрипта
echo Starting stream...
python src/main.py

pause