"""Тесты для PromptBuilder"""
import pytest
from src.prompt_builder import PromptBuilder

def test_prompt_builder_init():
    """Тест инициализации"""
    pb = PromptBuilder("config/agents_config.yaml")
    assert pb.config is not None
    assert "agents" in pb.config

def test_get_agent_config(prompt_builder):
    """Тест получения конфигурации агента"""
    agent1 = prompt_builder.get_agent_config("agent_1")
    agent2 = prompt_builder.get_agent_config("agent_2")
    
    assert agent1["name"] == "Профессор Кот"
    assert agent2["name"] == "Доктор Кошка"

def test_get_emotion_list(prompt_builder):
    """Тест получения списка эмоций"""
    emotions = prompt_builder.get_emotion_list("agent_1")
    assert "[" in emotions
    assert "]" in emotions
    assert len(emotions) > 0

def test_format_speech_patterns(prompt_builder):
    """Тест форматирования речевых паттернов"""
    patterns = prompt_builder.format_speech_patterns("agent_1")
    assert "-" in patterns
    assert len(patterns) > 0

def test_build_system_prompt(prompt_builder):
    """Тест построения системного промпта"""
    prompt = prompt_builder.build_system_prompt(
        agent_id="agent_1",
        history=[]
    )
    assert "Ты" in prompt

def test_get_agent_voice(prompt_builder):
    """Тест получения голоса агента"""
    voice = prompt_builder.get_agent_voice("agent_1")
    assert voice is not None
    assert isinstance(voice, str)
    # Проверяем, что голос соответствует ожидаемому
    assert voice in ["aidar", "baya", "Tam_24000", "May_24000", "Nec_24000", "Tur_24000"]