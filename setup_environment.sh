#!/bin/bash
# Скрипт настройки окружения для ai_avatars_stream (Linux/Mac)

echo "Setting up AI Avatars Stream environment..."

# Проверка наличия Python
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Создание виртуального окружения
echo "Creating virtual environment..."
python3 -m venv venv

# Активация виртуального окружения
echo "Activating virtual environment..."
source venv/bin/activate

# Установка зависимостей
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Environment setup complete!"
echo "To activate the environment in the future, run: source venv/bin/activate"