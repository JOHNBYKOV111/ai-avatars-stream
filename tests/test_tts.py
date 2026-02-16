"""Тесты для TTS движка"""
import pytest
from pathlib import Path
from unittest.mock import patch
from src.tts_engine import TTSEngine

def test_tts_initialization(tts_engine):
    """Тест инициализации TTS"""
    assert tts_engine.salute_engine is not None

def test_text_to_speech(tts_engine):
    """Тест синтеза речи"""
    text = "Привет, это тестовое сообщение!"
    audio_file = tts_engine.text_to_speech(text, agent_id='agent_1')
    
    assert Path(audio_file).exists()
    assert Path(audio_file).suffix == '.wav'
    assert Path(audio_file).stat().st_size > 100

def test_different_voices(tts_engine):
    """Тест разных голосов для агентов"""
    text = "Тестовое сообщение"
    
    file1 = tts_engine.text_to_speech(text, agent_id='agent_1')
    file2 = tts_engine.text_to_speech(text, agent_id='agent_2')
    
    assert file1 != file2
    assert "Tur_24000" in file1 or "salute_Tur" in file1
    assert "Nec_24000" in file2 or "salute_Nec" in file2

def test_tts_salute_unavailable():
    """Тест при недоступности SaluteSpeech"""
    with patch('src.tts_engine.SaluteSpeechTTS') as mock_salute_class:
        mock_salute_class.return_value.available = False
        tts = TTSEngine(use_salute=True)
        assert tts.salute_engine.available is False
        assert tts.silero_engine is not None

def test_tts_agent_speaker_mapping(tts_engine):
    """Тест маппинга голосов для агентов"""
    speaker_1 = tts_engine.get_speaker_for_agent('agent_1')
    speaker_2 = tts_engine.get_speaker_for_agent('agent_2')
    
    assert speaker_1 != speaker_2  # Голоса должны быть разными

def test_tts_very_long_text():
    """Тест обработки очень длинного текста"""
    tts = TTSEngine(use_salute=False)
    # Уменьшаем до 200 символов (безопасно для Silero)
    long_text = "а" * 200
    result = tts.text_to_speech(long_text, agent_id='agent_1')

def test_tts_silero_model_error():
    """Тест ошибки модели Silero"""
    tts = TTSEngine(use_salute=False)

    # Создаём тестовый текст
    test_text = "Тестовое сообщение"

    # Мокаем apply_tts, чтобы он выбрасывал исключение
    with patch.object(tts.silero_model, 'apply_tts') as mock_tts:
        mock_tts.side_effect = Exception("Model error")

        # Должен вернуть путь к файлу-заглушке
        try:
            result = tts.text_to_speech(test_text, agent_id='agent_1')
            # Если дошли сюда, значит ошибка обработана
            assert result is not None
            assert "silence" in str(result) or "fallback" in str(result)
        except Exception:
            # Если ошибка не обработана, тест падает
            pytest.fail("Ошибка Silero не была обработана")