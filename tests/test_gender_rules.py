"""Тесты гендерных правил"""
import pytest
from src.dialog_manager import DialogManager
from src.prompt_builder import PromptBuilder

@pytest.fixture
def prompt_builder():
    """Фикстура для PromptBuilder"""
    return PromptBuilder("config/agents_config.yaml")

@pytest.fixture
def dialog_manager(prompt_builder):
    """Фикстура для DialogManager с заглушкой GigaChat"""
    return DialogManager(None, prompt_builder)

def test_forbidden_words_filter(dialog_manager):
    """Тест фильтрации запрещённых слов"""
    test_phrases = [
        "Привет, дружище!",
        "Слушай, брат, это интересно",
        "Эй, парень, как дела?",
    ]
    
    for agent_id in ["agent_1", "agent_2"]:
        for phrase in test_phrases:
            fixed = dialog_manager._validate_and_fix_reply(phrase, agent_id)
            assert "дружище" not in fixed
            assert "брат" not in fixed
            assert "парень" not in fixed
            assert "коллега" in fixed or fixed != phrase