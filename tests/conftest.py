"""Общие фикстуры для всех тестов"""
import pytest
from src.gigachat_manager import GigaChatManager
from src.prompt_builder import PromptBuilder
from src.dialog_manager import DialogManager
from src.tts_engine import TTSEngine

@pytest.fixture
def gigachat_manager():
    """Фикстура для GigaChat менеджера"""
    return GigaChatManager(model="GigaChat")

@pytest.fixture
def prompt_builder():
    """Фикстура для построителя промптов"""
    return PromptBuilder("config/agents_config.yaml")

@pytest.fixture
def dialog_manager(gigachat_manager, prompt_builder):
    """Фикстура для менеджера диалога"""
    return DialogManager(gigachat_manager, prompt_builder)

@pytest.fixture
def tts_engine():
    """Фикстура для TTS движка"""
    return TTSEngine(use_salute=True)