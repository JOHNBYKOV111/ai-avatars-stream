"""Тесты для вспомогательных функций"""
import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, mock_open
from src.utils import (
    ensure_dir,
    get_timestamp,
    safe_json_load,
    safe_json_save,
    clean_text,
    extract_emotion_tag,
    load_yaml_config,
    save_json_config
)

class TestEnsureDir:
    """Тесты для функции ensure_dir"""

    def test_ensure_dir_new(self):
        """Тест создания новой директории"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "new" / "nested" / "dir"
            assert not test_dir.exists()
            result = ensure_dir(test_dir)
            assert test_dir.exists()
            assert result == test_dir

    def test_ensure_dir_exists(self):
        """Тест когда директория уже существует"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "existing"
            test_dir.mkdir(parents=True)
            result = ensure_dir(test_dir)
            assert test_dir.exists()
            assert result == test_dir

    def test_ensure_dir_with_file(self):
        """Тест создания директории, когда путь содержит файл"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "file.txt"
            test_file.touch()
            test_dir = test_file / "subdir"  # Это невалидный путь
            with pytest.raises(OSError):
                ensure_dir(test_dir)


class TestGetTimestamp:
    """Тесты для функции get_timestamp"""

    def test_timestamp_format(self):
        """Тест формата временной метки"""
        timestamp = get_timestamp()
        assert len(timestamp) == 15  # YYYYMMDD_HHMMSS
        assert "_" in timestamp
        parts = timestamp.split('_')
        assert len(parts) == 2
        assert len(parts[0]) == 8  # YYYYMMDD
        assert len(parts[1]) == 6  # HHMMSS
        assert parts[0].isdigit()
        assert parts[1].isdigit()

    def test_timestamp_unique(self):
        """Тест уникальности временных меток"""
        timestamps = [get_timestamp() for _ in range(10)]
        # В течение одной секунды могут быть одинаковыми
        # Проверяем, что все они валидного формата
        for ts in timestamps:
            assert len(ts) == 15


class TestSafeJsonLoad:
    """Тесты для функции safe_json_load"""

    def test_load_valid_json(self):
        """Тест загрузки валидного JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"test": "data", "number": 42}')
            f.flush()
            fname = f.name
        
        try:
            data = safe_json_load(fname)
            assert data == {"test": "data", "number": 42}
        finally:
            os.unlink(fname)

    def test_load_empty_file(self):
        """Тест загрузки пустого файла"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('')
            f.flush()
            fname = f.name
        
        try:
            data = safe_json_load(fname)
            assert data is None
        finally:
            os.unlink(fname)

    def test_load_invalid_json(self):
        """Тест загрузки невалидного JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{not valid json')
            f.flush()
            fname = f.name
        
        try:
            data = safe_json_load(fname)
            assert data is None
        finally:
            os.unlink(fname)

    def test_load_nonexistent_file(self):
        """Тест загрузки несуществующего файла"""
        data = safe_json_load("не_существует.json")
        assert data is None

    def test_load_with_unicode(self):
        """Тест загрузки JSON с Unicode"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', encoding='utf-8', delete=False) as f:
            f.write('{"text": "Привет мир!"}')
            f.flush()
            fname = f.name
        
        try:
            data = safe_json_load(fname)
            assert data == {"text": "Привет мир!"}
        finally:
            os.unlink(fname)


class TestSafeJsonSave:
    """Тесты для функции safe_json_save"""

    def test_save_valid_json(self):
        """Тест сохранения валидного JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            data = {"key": "value", "number": 42, "list": [1, 2, 3]}
            
            result = safe_json_save(test_file, data)
            assert result is True
            assert test_file.exists()
            
            # Проверка содержимого
            with open(test_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            assert loaded == data

    def test_save_nested_directories(self):
        """Тест сохранения с созданием вложенных папок"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "deep" / "nested" / "path" / "test.json"
            data = {"test": "data"}
            
            result = safe_json_save(test_file, data)
            assert result is True
            assert test_file.exists()
            assert test_file.parent.exists()

    def test_save_permission_error(self):
        """Тест сохранения при ошибке доступа"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            
            # Создаём файл и делаем его read-only
            with open(test_file, 'w') as f:
                f.write('initial')
            os.chmod(test_file, 0o444)  # Только чтение
            
            result = safe_json_save(test_file, {"new": "data"})
            assert result is False
            
            # Возвращаем права для удаления
            os.chmod(test_file, 0o666)

    def test_save_with_unicode(self):
        """Тест сохранения JSON с Unicode"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "unicode.json"
            data = {"text": "Привет мир!", "emoji": "🐱"}
            
            result = safe_json_save(test_file, data)
            assert result is True
            
            with open(test_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            assert loaded == data


class TestCleanText:
    """Тесты для функции clean_text"""

    @pytest.mark.parametrize("input_text,expected", [
        ("[РАДОСТЬ] Привет!", "Привет!"),
        ("[УДИВЛЕНИЕ]   С пробелами  ", "С пробелами"),
        ("Текст без тега", "Текст без тега"),
        ("[ТЕГ][ТЕГ] Двойной тег", "Двойной тег"),
        ("[НЕЙТРАЛЬНО] ", ""),
        ("", ""),
        ("   ", ""),
        ("[ТЕГ]Текст без пробела", "Текст без пробела"),
        ("\n[ТЕГ]\nТекст с переносом\n", "Текст с переносом"),
        ("Текст с [тегом] внутри", "Текст с [тегом] внутри"),
    ])
    def test_clean_text_various(self, input_text, expected):
        """Тест очистки текста с разными входными данными"""
        assert clean_text(input_text) == expected


class TestExtractEmotionTag:
    """Тесты для функции extract_emotion_tag"""

    @pytest.mark.parametrize("input_text,expected_tag,expected_text", [
        ("[РАДОСТЬ] Привет!", "[РАДОСТЬ]", "Привет!"),
        ("[УДИВЛЕНИЕ] Ого!", "[УДИВЛЕНИЕ]", "Ого!"),
        ("Текст без тега", "[НЕЙТРАЛЬНО]", "Текст без тега"),
        ("[ТЕГ] [ТЕГ] Два тега", "[ТЕГ]", "[ТЕГ] Два тега"),
        ("[НЕЙТРАЛЬНО] ", "[НЕЙТРАЛЬНО]", ""),
        ("", "[НЕЙТРАЛЬНО]", ""),
        ("   ", "[НЕЙТРАЛЬНО]", ""),
        ("[РАДОСТЬ]Привет!", "[РАДОСТЬ]", "Привет!"),
        ("   [ТЕГ]   Текст с пробелами", "[ТЕГ]", "Текст с пробелами"),
        ("[СЛОЖНЫЙ_ТЕГ_123] Текст", "[СЛОЖНЫЙ_ТЕГ_123]", "Текст"),
    ])
    def test_extract_emotion_tag_various(self, input_text, expected_tag, expected_text):
        """Тест извлечения тега с разными входными данными"""
        tag, text = extract_emotion_tag(input_text)
        assert tag == expected_tag
        assert text == expected_text

    def test_extract_emotion_tag_no_space(self):
        """Тест извлечения тега без пробела"""
        tag, text = extract_emotion_tag("[РАДОСТЬ]Привет!")
        assert tag == "[РАДОСТЬ]"
        assert text == "Привет!"

    def test_extract_emotion_tag_multiple_brackets(self):
        """Тест извлечения тега с несколькими скобками в тексте"""
        tag, text = extract_emotion_tag("[ТЕГ] Текст со [скобками] внутри")
        assert tag == "[ТЕГ]"
        assert text == "Текст со [скобками] внутри"


class TestIntegration:
    """Интеграционные тесты для нескольких функций"""

    def test_save_and_load_cycle(self):
        """Тест цикла сохранения и загрузки"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            original_data = {"key": "value", "timestamp": get_timestamp()}
            
            # Сохраняем
            save_result = safe_json_save(test_file, original_data)
            assert save_result is True
            
            # Загружаем
            loaded_data = safe_json_load(str(test_file))
            assert loaded_data == original_data

    def test_clean_and_extract_cycle(self):
        """Тест цикла очистки и извлечения"""
        text = "[РАДОСТЬ] Привет, мир!"
        
        # Извлекаем тег
        tag, content = extract_emotion_tag(text)
        assert tag == "[РАДОСТЬ]"
        assert content == "Привет, мир!"
        
        # Очищаем текст
        cleaned = clean_text(text)
        assert cleaned == "Привет, мир!"


# ============================================================================
# ТЕСТЫ ДЛЯ НЕПОКРЫТЫХ ФУНКЦИЙ
# ============================================================================

class TestLoadYamlConfig:
    """Тесты для функции load_yaml_config"""

    def test_load_yaml_config_file_not_found(self):
        """Тест загрузки несуществующего YAML файла"""
        result = load_yaml_config("не_существует.yaml")
        assert result is None

    def test_load_yaml_config_invalid_yaml(self):
        """Тест загрузки невалидного YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("{invalid: yaml:")  # Некорректный YAML
            f.flush()
            fname = f.name
        
        try:
            result = load_yaml_config(fname)
            assert result is None
        finally:
            os.unlink(fname)


class TestSaveJsonConfig:
    """Тесты для функции save_json_config"""

    def test_save_json_config_permission_error(self):
        """Тест сохранения JSON при ошибке доступа"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Создаём файл и делаем его read-only
            test_file = Path(tmpdir) / "test.json"
            with open(test_file, 'w') as f:
                f.write('initial')
            os.chmod(test_file, 0o444)  # Только чтение
            
            result = save_json_config(test_file, {"key": "value"})
            assert result is False
            
            # Возвращаем права для удаления
            os.chmod(test_file, 0o666)

    def test_save_json_config_success(self):
        """Тест успешного сохранения JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            data = {"key": "value"}
            result = save_json_config(test_file, data)
            assert result is True
            
            with open(test_file, 'r') as f:
                loaded = json.load(f)
            assert loaded == data


# ============================================================================
# ДОПОЛНИТЕЛЬНЫЕ ТЕСТЫ ДЛЯ ПОКРЫТИЯ
# ============================================================================

def test_clean_text_with_multiple_tags_and_spaces():
    """Тест очистки с множественными тегами и пробелами"""
    text = "  [ТЕГ1]  [ТЕГ2]   Текст с пробелами  "
    result = clean_text(text)
    assert result == "Текст с пробелами"

def test_safe_json_save_invalid_path():
    """Тест сохранения в невалидный путь"""
    result = safe_json_save(Path(":/invalid/path"), {"test": "data"})
    assert result is False

def test_safe_json_save_exception():
    """Тест сохранения с исключением"""
    with patch('builtins.open', side_effect=Exception("Write error")):
        result = safe_json_save(Path("test.json"), {"test": "data"})
        assert result is False


def test_format_log_message():
    """Тест функции format_log_message"""
    from src.utils import format_log_message
    
    msg = format_log_message("Тест", "ERROR")
    assert "ERROR" in msg
    assert "Тест" in msg
    # Проверяем, что сообщение содержит временную метку в правильном формате
    assert "[" in msg and "]" in msg
    # Проверяем, что уровень лога присутствует
    assert "ERROR:" in msg

# ============================================================================
# ТЕСТЫ ДЛЯ create_directory_if_not_exists и create_dir
# ============================================================================

def test_create_directory_if_not_exists():
    """Тест функции create_directory_if_not_exists"""
    import tempfile
    import os
    from src.utils import create_directory_if_not_exists
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Тест создания новой директории
        new_dir = os.path.join(tmpdir, "new_directory")
        result = create_directory_if_not_exists(new_dir)
        assert result is True
        assert os.path.exists(new_dir)
        
        # Тест с уже существующей директорией
        result = create_directory_if_not_exists(new_dir)
        assert result is False
        assert os.path.exists(new_dir)

def test_create_dir():
    """Тест функции create_dir"""
    import tempfile
    from src.utils import create_dir
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Тест с путем как строкой
        dir_path_str = os.path.join(tmpdir, "test_dir_str")
        result = create_dir(dir_path_str)
        assert isinstance(result, Path)
        assert result.exists()
        
        # Тест с путем как Path
        dir_path_obj = Path(tmpdir) / "test_dir_path"
        result = create_dir(dir_path_obj)
        assert isinstance(result, Path)
        assert result.exists()

# ============================================================================
# ТЕСТЫ ДЛЯ load_json_config
# ============================================================================

class TestLoadJsonConfig:
    """Тесты для функции load_json_config"""
    
    def test_load_json_config_success(self):
        """Тест успешной загрузки JSON конфигурации"""
        import tempfile
        import json
        from src.utils import load_json_config
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = {"key": "value", "number": 42}
            json.dump(test_data, f)
            f.flush()
            fname = f.name
        
        try:
            result = load_json_config(fname)
            assert result == test_data
        finally:
            import os
            os.unlink(fname)
    
    def test_load_json_config_file_not_found(self):
        """Тест загрузки несуществующего JSON файла"""
        from src.utils import load_json_config
        
        result = load_json_config("не_существует.json")
        assert result is None
    
    def test_load_json_config_invalid_json(self):
        """Тест загрузки невалидного JSON"""
        import tempfile
        from src.utils import load_json_config
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{invalid json')
            f.flush()
            fname = f.name
        
        try:
            result = load_json_config(fname)
            assert result is None
        finally:
            import os
            os.unlink(fname)
    
    def test_load_json_config_with_unicode(self):
        """Тест загрузки JSON с Unicode"""
        import tempfile
        import json
        from src.utils import load_json_config
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', encoding='utf-8', delete=False) as f:
            test_data = {"text": "Привет мир!", "emoji": "🐱"}
            json.dump(test_data, f, ensure_ascii=False)
            f.flush()
            fname = f.name
        
        try:
            result = load_json_config(fname)
            assert result == test_data
        finally:
            import os
            os.unlink(fname)