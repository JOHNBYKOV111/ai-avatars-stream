#!/bin/bash
# Скрипт запуска стрима для ai_avatars_stream (Linux/Mac)

echo "Starting AI Avatars Stream..."

# Активация виртуального окружения
echo "Activating virtual environment..."
source venv/bin/activate

# Запуск главного скрипта
echo "Starting stream..."
python src/main.py

echo "Stream started!"