"""Тесты контроля длительности реплик"""
import pytest
from src.gigachat_manager import GigaChatManager

def test_duration_estimation():
    """Тест оценки длительности речи"""
    gm = GigaChatManager()
    
    test_texts = [
        ("Короткая фраза", 1.0),
        ("Это тестовое предложение из пяти слов", 2.0),
        ("Это очень длинное предложение которое должно занимать примерно семь-восемь слов", 3.0),
    ]
    
    for text, expected in test_texts:
        duration = gm._estimate_audio_duration(text)
        assert duration > 0
        assert duration < 10