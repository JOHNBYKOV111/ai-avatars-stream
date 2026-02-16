"""Тесты восстановления после ошибок"""
import pytest
from unittest.mock import Mock, patch
from src.gigachat_manager import GigaChatManager
from src.tts_engine import TTSEngine

def test_gigachat_retry_on_failure():
    """Тест повторных попыток при ошибке"""
    gm = GigaChatManager()
    
    with patch('requests.post') as mock_post:
        mock_post.side_effect = [
            Exception("Network error"),
            Exception("Network error"),
            Mock(status_code=200, json=lambda: {
                "choices": [{"message": {"content": "Тестовый ответ"}}],
                "usage": {"total_tokens": 10}
            })
        ]
        
        response, tokens = gm.generate_response(
            system_prompt="Тест",
            retry_count=3
        )
        
        assert response == "Тестовый ответ"
        assert tokens == 10
        assert mock_post.call_count == 3

def test_tts_fallback():
    """Тест падения на Silero"""
    with patch('src.tts_engine.SaluteSpeechTTS') as mock_salute:
        mock_salute.return_value.available = False
        
        tts = TTSEngine(use_salute=True)
        assert tts.salute_engine.available is False
        assert tts.silero_engine is not None