#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Вспомогательные функции для ai_avatars_stream
"""

import os
import json
import yaml
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Any, Tuple

# ============================================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ФАЙЛАМИ И ДИРЕКТОРИЯМИ
# ============================================================================

def ensure_dir(path: Path) -> Path:
    """Создаёт директорию, если её нет (возвращает путь)"""
    path.mkdir(parents=True, exist_ok=True)
    return path

def create_directory_if_not_exists(directory_path):
    """Создание директории, если она не существует (возвращает bool)"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        return True
    return False

def get_timestamp() -> str:
    """Возвращает временную метку для файлов (YYYYMMDD_HHMMSS)"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def get_current_timestamp():
    """Получение текущей временной метки (для логов)"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def format_log_message(message, level="INFO"):
    """Форматирование сообщения для лога"""
    timestamp = get_current_timestamp()
    return f"[{timestamp}] {level}: {message}"

# ============================================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С YAML
# ============================================================================

def load_yaml_config(filepath):
    """Загрузка YAML конфигурации"""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"❌ Ошибка загрузки YAML файла {filepath}: {e}")
        return None

# ============================================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С JSON
# ============================================================================

def load_json_config(filepath):
    """Загрузка JSON конфигурации"""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"❌ Ошибка загрузки JSON файла {filepath}: {e}")
        return None

def save_json_config(filepath, data):
    """Сохранение данных в JSON файл"""
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения JSON файла {filepath}: {e}")
        return False

def safe_json_load(filepath: str) -> Optional[Any]:
    """Безопасно загружает JSON из файла (без исключений)"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def safe_json_save(filepath: Path, data: Any) -> bool:
    """Безопасно сохраняет JSON в файл (без исключений)"""
    try:
        ensure_dir(filepath.parent)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

# ============================================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ТЕКСТОМ
# ============================================================================

def clean_text(text: str) -> str:
    """Очищает текст от всех тегов эмоций в начале строки"""
    result = text.strip()
    # Удаляем все теги в начале строки (пока они есть)
    while re.match(r'^\[[^\]]+\]', result):
        # Удаляем один тег и следующие за ним пробелы
        result = re.sub(r'^\[[^\]]+\]\s*', '', result)
    return result

def extract_emotion_tag(text: str) -> Tuple[str, str]:
    """Извлекает первый тег эмоции из текста"""
    match = re.match(r'^(\[[^\]]+\])\s*(.*)', text.strip())
    if match:
        return match.group(1), match.group(2).strip()
    return "[НЕЙТРАЛЬНО]", text.strip()

# ============================================================================
# УНИВЕРСАЛЬНЫЕ ФУНКЦИИ (объединяют старые и новые)
# ============================================================================

def create_dir(path):
    """Универсальная функция создания директории"""
    if isinstance(path, str):
        path = Path(path)
    return ensure_dir(path)