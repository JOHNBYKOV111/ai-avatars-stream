"""Дополнительные тесты для PromptBuilder"""
import pytest
from src.prompt_builder import PromptBuilder

def test_get_agent_voice(prompt_builder):
    """Тест получения голоса агента"""
    voice = prompt_builder.get_agent_voice("agent_1")
    assert voice is not None
    assert isinstance(voice, str)

def test_get_emotion_animation_default(prompt_builder):
    """Тест получения анимации по умолчанию"""
    animation = prompt_builder.get_emotion_animation("agent_1", "[НЕСУЩЕСТВУЮЩИЙ]")
    assert animation == "Idle"

def test_get_temperature_default(prompt_builder):
    """Тест получения температуры по умолчанию"""
    temp = prompt_builder.get_temperature("agent_1")
    assert isinstance(temp, float)
    assert 0 <= temp <= 1

def test_format_speech_patterns(prompt_builder):
    """Тест форматирования особенностей речи (строки 51-55)"""
    patterns = prompt_builder.format_speech_patterns("agent_1")
    assert isinstance(patterns, str)

def test_format_topics(prompt_builder):
    """Тест форматирования тем (строки 57-61)"""
    topics = prompt_builder.format_topics("agent_1")
    assert isinstance(topics, str)

def test_get_max_tokens(prompt_builder):
    """Тест получения максимального количества токенов (строки 151-153)"""
    tokens = prompt_builder.get_max_tokens("agent_1")
    assert isinstance(tokens, int)
    assert tokens > 0

def test_format_history_empty(prompt_builder):
    """Тест форматирования пустой истории (строки 119-129)"""
    result = prompt_builder._format_history(None)
    assert result == "Диалог начинается."

def test_format_history_with_messages(prompt_builder):
    """Тест форматирования истории с сообщениями (строки 119-129)"""
    history = [
        {"role": "user", "content": "Привет"},
        {"role": "assistant", "content": "Здравствуйте!"}
    ]
    result = prompt_builder._format_history(history)
    assert "Собеседник: Привет" in result
    assert "Вы: Здравствуйте!" in result

def test_build_system_prompt_first_reply(prompt_builder):
    """Тест формирования первой реплики (строки 85-90)"""
    prompt = prompt_builder.build_system_prompt(
        agent_id="agent_1",
        is_first_reply=True,
        topic="тестовая тема"
    )
    assert isinstance(prompt, str)
    assert len(prompt) > 0

def test_get_agent_name(prompt_builder):
    """Тест получения имени агента (строки 131-133)"""
    name = prompt_builder.get_agent_name("agent_1")
    assert isinstance(name, str)
    assert len(name) > 0