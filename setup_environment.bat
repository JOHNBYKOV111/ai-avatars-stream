@echo off
REM Скрипт настройки окружения для ai_avatars_stream (Windows)

echo Setting up AI Avatars Stream environment...

REM Проверка наличия Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Создание виртуального окружения
echo Creating virtual environment...
python -m venv venv

REM Активация виртуального окружения
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Установка зависимостей
echo Installing dependencies...
pip install -r requirements.txt

echo Environment setup complete!
echo To activate the environment in the future, run: venv\Scripts\activate.bat
pause