"""Тесты для DialogManager"""
import pytest
from src.dialog_manager import DialogManager

def test_dialog_initialization(dialog_manager):
    """Тест инициализации"""
    assert dialog_manager.turn_order == ["agent_1", "agent_2"]
    assert dialog_manager.reply_count == 0

def test_get_next_agent(dialog_manager):
    """Тест получения следующего агента"""
    first = dialog_manager.get_next_agent()
    second = dialog_manager.get_next_agent()
    
    assert first == "agent_1"
    assert second == "agent_2"
    assert first != second

def test_add_to_history(dialog_manager):
    """Тест добавления в историю"""
    dialog_manager.add_to_history("user", "Тестовое сообщение")
    assert len(dialog_manager.history) == 1
    assert dialog_manager.history[0]["content"] == "Тестовое сообщение"

def test_get_recent_history(dialog_manager):
    """Тест получения последних реплик"""
    for i in range(5):
        dialog_manager.add_to_history("user", f"Сообщение {i}")
    
    recent = dialog_manager.get_recent_history(n=3)
    assert len(recent) == 3
    assert "Сообщение 4" in recent[-1]["content"]