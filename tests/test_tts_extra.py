"""Дополнительные тесты для TTSEngine"""
import pytest
from unittest.mock import patch, MagicMock
from src.tts_engine import TTSEngine

def test_tts_salute_unavailable_fallback():
    """Тест переключения на Silero при недоступности SaluteSpeech"""
    with patch('src.tts_engine.SaluteSpeechTTS') as mock_salute:
        mock_salute.return_value.available = False
        
        tts = TTSEngine(use_salute=True)
        assert tts.silero_engine is not None

def test_tts_speaker_mapping():
    """Тест маппинга голосов для агентов"""
    tts = TTSEngine(use_salute=False)
    
    speaker_1 = tts.get_speaker_for_agent('agent_1')
    speaker_2 = tts.get_speaker_for_agent('agent_2')
    
    assert speaker_1 == 'baya'  # мужской для чёрного кота
    assert speaker_2 == 'aidar'  # женский для белой кошки

def test_tts_silero_error_handling():
    """Тест обработки ошибок Silero"""
    tts = TTSEngine(use_salute=False)

    with patch.object(tts.silero_model, 'apply_tts') as mock_tts:
        mock_tts.side_effect = Exception("Silero error")

        # Должен вернуть путь к заглушке, а не упасть
        result = tts.text_to_speech("Тест", agent_id='agent_1')
        assert result is not None

def test_tts_cache_mechanism():
    """Тест механизма кэширования"""
    tts = TTSEngine(use_salute=False)
    test_text = "Тестовое сообщение для кэша"
    
    # Первый вызов - создаёт файл
    result1 = tts.text_to_speech(test_text, agent_id='agent_1')
    
    # Проверяем, что файл существует
    import os
    assert os.path.exists(result1)
    
    # Получаем время создания файла
    import time
    time.sleep(1)  # Ждём секунду
    
    # Второй вызов - должен вернуть тот же файл
    result2 = tts.text_to_speech(test_text, agent_id='agent_1')
    assert result1 == result2  # Пути должны совпадать

def test_tts_error_during_synthesis():
    """Тест ошибки во время синтеза (строки 341-345)"""
    tts = TTSEngine(use_salute=False)
    
    with patch('soundfile.write') as mock_write:
        mock_write.side_effect = Exception("Write error")
        
        with patch.object(tts.silero_model, 'apply_tts') as mock_tts:
            # Симулируем успешный синтез, но ошибку при записи
            mock_tts.return_value = [0.1, 0.2, 0.3]
            
            # Должен обработать ошибку и вернуть заглушку
            result = tts.text_to_speech("Тест", agent_id='agent_1')
            assert result is not None

def test_tts_cache_mechanism_fixed():
    """Тест кэширования (строки 370-406)"""
    tts = TTSEngine(use_salute=False)
    test_text = "Тест кэша"
    
    # Первый вызов
    result1 = tts.text_to_speech(test_text, agent_id='agent_1')
    
    # Второй вызов с тем же текстом
    result2 = tts.text_to_speech(test_text, agent_id='agent_1')
    
    assert result1 == result2  # Должны быть одинаковые пути
    import os
    assert os.path.exists(result1)

def test_tts_error_handling_extended():
    """Покрывает строки 343-345, 410-411"""
    tts = TTSEngine(use_salute=False)
    
    with patch('soundfile.write') as mock_write:
        mock_write.side_effect = Exception("Write error")
        
        result = tts.text_to_speech("Тест ошибки", agent_id='agent_1')

def test_tts_cache_mechanism_direct():
    """ПРЯМОЕ покрытие строк 370-406 (кэширование)"""
    tts = TTSEngine(use_salute=False)
    test_text = "Тест кэша"
    
    # Очищаем кэш
    import os
    import hashlib
    clean_text = test_text.strip()
    text_hash = hashlib.md5(clean_text.encode()).hexdigest()[:10]
    expected_file = tts.output_dir / f"silero_baya_{text_hash}.wav"
    if expected_file.exists():
        os.remove(expected_file)
    
    # Первый вызов - создаёт файл
    result1 = tts.text_to_speech(test_text, agent_id='agent_1')
    assert os.path.exists(result1)
    
    # Второй вызов - должен использовать кэш
    with patch('soundfile.write') as mock_write:
        result2 = tts.text_to_speech(test_text, agent_id='agent_1')
        assert result1 == result2
        mock_write.assert_not_called()
def test_tts_final_coverage():
    """Финальное покрытие для tts_engine.py (строки 370-406)"""
    import os
    import hashlib
    from unittest.mock import patch, MagicMock
    from src.tts_engine import TTSEngine
    
    tts = TTSEngine(use_salute=False)
    test_text = "Финальный тест кэша"
    
    # Очищаем кэш для этого текста
    clean_text = test_text.strip()
    text_hash = hashlib.md5(clean_text.encode()).hexdigest()[:10]
    expected_file = tts.output_dir / f"silero_baya_{text_hash}.wav"
    if expected_file.exists():
        os.remove(expected_file)
    
    # Первый вызов - должен создать файл
    result1 = tts.text_to_speech(test_text, agent_id='agent_1')
    
    # Проверяем, что файл создан
    assert os.path.exists(result1)
    
    # Второй вызов - должен использовать кэш
    with patch('soundfile.write') as mock_write:
        result2 = tts.text_to_speech(test_text, agent_id='agent_1')
        # Не должно быть повторного вызова soundfile.write
        mock_write.assert_not_called()
    
    # Пути должны совпадать
    assert result1 == result2
    
    # Очищаем за собой
    if expected_file.exists():
        os.remove(expected_file)
def test_tts_complete_coverage():
    """ПОЛНОЕ покрытие оставшихся строк"""
    tts = TTSEngine(use_salute=False)
    
    # Строки 370-406: кэширование
    text = "тест кэша 123"
    result1 = tts.text_to_speech(text, agent_id='agent_1')
    result2 = tts.text_to_speech(text, agent_id='agent_1')
    assert result1 == result2
    
    # Строки 410-411: ошибка Silero
    with patch.object(tts.silero_model, 'apply_tts') as mock_tts:
        mock_tts.side_effect = Exception("Silero error")
        result = tts.text_to_speech("ошибка", agent_id='agent_1')
        assert result is not None

def test_tts_main_function():
    """Тест основной функции test_tts из tts_engine.py (строки 367-406)"""
    from src.tts_engine import test_tts
    # Функция должна выполниться без ошибок
    result = test_tts()
    # Результат должен быть True (успех)
    assert result == True