"""Дополнительные тесты для utils.py"""
import pytest
from src.utils import format_log_message, get_current_timestamp

def test_format_log_message():
    """Тест форматирования сообщения лога"""
    msg = format_log_message("Тестовое сообщение", "ERROR")
    assert "ERROR" in msg
    assert "Тестовое сообщение" in msg
    assert "[" in msg and "]" in msg

def test_get_current_timestamp():
    """Тест получения текущей временной метки"""
    ts = get_current_timestamp()
    assert len(ts) >= 16  # YYYY-MM-DD HH:MM:SS
    assert " " in ts
    assert "-" in ts
    assert ":" in ts

def test_ensure_dir():
    """Тест создания директории (строки 20-23)"""
    from src.utils import ensure_dir
    from pathlib import Path
    import tempfile
    import shutil
    
    # Создаем временную директорию для теста
    temp_dir = Path(tempfile.mkdtemp())
    test_path = temp_dir / "test_dir"
    
    try:
        # Тест создания новой директории
        result = ensure_dir(test_path)
        assert result == test_path
        assert test_path.exists()
        assert test_path.is_dir()
    finally:
        # Удаляем временную директорию
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_create_directory_if_not_exists():
    """Тест создания директории если не существует (строки 25-30)"""
    from src.utils import create_directory_if_not_exists
    import tempfile
    import shutil
    import os
    
    # Создаем временную директорию для теста
    temp_dir = tempfile.mkdtemp()
    test_path = os.path.join(temp_dir, "new_directory")
    
    try:
        # Тест создания новой директории
        result = create_directory_if_not_exists(test_path)
        assert result is True
        assert os.path.exists(test_path)
        assert os.path.isdir(test_path)
        
        # Тест когда директория уже существует
        result = create_directory_if_not_exists(test_path)
        assert result is False
    finally:
        # Удаляем временную директорию
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_get_timestamp():
    """Тест получения временной метки (строки 32-34)"""
    from src.utils import get_timestamp
    ts = get_timestamp()
    assert isinstance(ts, str)
    assert len(ts) == 15  # YYYYMMDD_HHMMSS
    assert "_" in ts
    assert ts.replace("_", "").replace(" ", "").isdigit()

def test_load_yaml_config():
    """Тест загрузки YAML конфигурации (строки 49-56)"""
    from src.utils import load_yaml_config
    import tempfile
    import yaml
    import os
    
    # Создаем временный YAML файл
    temp_dir = tempfile.mkdtemp()
    yaml_file = os.path.join(temp_dir, "test.yaml")
    
    # Записываем тестовые данные
    test_data = {"key": "value", "number": 42}
    with open(yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(test_data, f, allow_unicode=True)
    
    try:
        # Тест успешной загрузки
        result = load_yaml_config(yaml_file)
        assert result == test_data
        
        # Тест загрузки несуществующего файла
        result = load_yaml_config("nonexistent.yaml")
        assert result is None
    finally:
        # Удаляем временные файлы
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_load_json_config():
    """Тест загрузки JSON конфигурации (строки 62-69)"""
    from src.utils import load_json_config
    import tempfile
    import json
    import os
    
    # Создаем временный JSON файл
    temp_dir = tempfile.mkdtemp()
    json_file = os.path.join(temp_dir, "test.json")
    
    # Записываем тестовые данные
    test_data = {"key": "value", "number": 42}
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False)
    
    try:
        # Тест успешной загрузки
        result = load_json_config(json_file)
        assert result == test_data
        
        # Тест загрузки несуществующего файла
        result = load_json_config("nonexistent.json")
        assert result is None
    finally:
        # Удаляем временные файлы
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_save_json_config():
    """Тест сохранения JSON конфигурации (строки 71-79)"""
    from src.utils import save_json_config
    import tempfile
    import json
    import os
    
    # Создаем временную директорию
    temp_dir = tempfile.mkdtemp()
    json_file = os.path.join(temp_dir, "test.json")
    
    # Тестовые данные
    test_data = {"key": "value", "number": 42}
    
    try:
        # Тест успешного сохранения
        result = save_json_config(json_file, test_data)
        assert result is True
        assert os.path.exists(json_file)
        
        # Проверяем содержимое файла
        with open(json_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        assert saved_data == test_data
        
        # Тест ошибки сохранения (используем путь к директории вместо файла)
        # Это вызовет ошибку, так как ожидается файл, а не директория
        result = save_json_config(temp_dir, test_data)
        assert result is False
    finally:
        # Удаляем временные файлы
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_safe_json_load():
    """Тест безопасной загрузки JSON (строки 81-87)"""
    from src.utils import safe_json_load
    import tempfile
    import json
    import os
    
    # Создаем временный JSON файл
    temp_dir = tempfile.mkdtemp()
    json_file = os.path.join(temp_dir, "test.json")
    
    # Записываем тестовые данные
    test_data = {"key": "value", "number": 42}
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False)
    
    try:
        # Тест успешной загрузки
        result = safe_json_load(json_file)
        assert result == test_data
        
        # Тест загрузки несуществующего файла
        result = safe_json_load("nonexistent.json")
        assert result is None
        
        # Тест загрузки поврежденного JSON
        broken_file = os.path.join(temp_dir, "broken.json")
        with open(broken_file, 'w', encoding='utf-8') as f:
            f.write("{ invalid json")
        
        result = safe_json_load(broken_file)
        assert result is None
    finally:
        # Удаляем временные файлы
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_safe_json_save():
    """Тест безопасного сохранения JSON (строки 89-97)"""
    from src.utils import safe_json_save
    from pathlib import Path
    import tempfile
    import json
    import os
    
    # Создаем временную директорию
    temp_dir = Path(tempfile.mkdtemp())
    json_file = temp_dir / "test.json"
    
    # Тестовые данные
    test_data = {"key": "value", "number": 42}
    
    try:
        # Тест успешного сохранения
        result = safe_json_save(json_file, test_data)
        assert result is True
        assert json_file.exists()
        
        # Проверяем содержимое файла
        with open(json_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        assert saved_data == test_data
        
        # Тест ошибки сохранения (используем путь к директории вместо файла)
        # Это вызовет ошибку, так как ожидается файл, а не директория
        result = safe_json_save(Path(temp_dir), test_data)
        assert result is False
    finally:
        # Удаляем временные файлы
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_clean_text():
    """Тест очистки текста от тегов эмоций (строки 103-110)"""
    from src.utils import clean_text
    
    # Тест с одним тегом
    result = clean_text("[РАДОСТЬ] Привет!")
    assert result == "Привет!"
    
    # Тест с несколькими тегами
    result = clean_text("[РАДОСТЬ] [ВОЗБУЖДЕНИЕ] Привет!")
    assert result == "Привет!"
    
    # Тест без тегов
    result = clean_text("Привет!")
    assert result == "Привет!"
    
    # Тест с пробелами
    result = clean_text("[РАДОСТЬ]   Привет!   ")
    assert result == "Привет!"

def test_extract_emotion_tag():
    """Тест извлечения тега эмоции (строки 112-117)"""
    from src.utils import extract_emotion_tag
    
    # Тест с тегом
    tag, text = extract_emotion_tag("[РАДОСТЬ] Привет!")
    assert tag == "[РАДОСТЬ]"
    assert text == "Привет!"
    
    # Тест без тега
    tag, text = extract_emotion_tag("Привет!")
    assert tag == "[НЕЙТРАЛЬНО]"
    assert text == "Привет!"
    
    # Тест с пробелами
    tag, text = extract_emotion_tag("[РАДОСТЬ]   Привет!   ")
    assert tag == "[РАДОСТЬ]"
    assert text == "Привет!"

def test_create_dir():
    """Тест универсальной функции создания директории (строки 123-127)"""
    from src.utils import create_dir
    from pathlib import Path
    import tempfile
    import shutil
    
    # Создаем временную директорию для теста
    temp_dir = Path(tempfile.mkdtemp())
    test_path = temp_dir / "test_dir"
    test_path_str = str(test_path)
    
    try:
        # Тест с Path объектом
        result = create_dir(test_path)
        assert result == test_path
        assert test_path.exists()
        assert test_path.is_dir()
        
        # Тест со строкой
        test_path2 = temp_dir / "test_dir2"
        result = create_dir(str(test_path2))
        assert result == test_path2
        assert test_path2.exists()
        assert test_path2.is_dir()
    finally:
        # Удаляем временную директорию
        shutil.rmtree(temp_dir, ignore_errors=True)