"""Дополнительные тесты для DialogManager"""
import pytest
from unittest.mock import Mock, patch
from src.dialog_manager import DialogManager
from src.gigachat_manager import GigaChatManager
from src.prompt_builder import PromptBuilder

@pytest.fixture
def mock_gigachat():
    """Мок для GigaChatManager"""
    return Mock(spec=GigaChatManager)

@pytest.fixture
def mock_prompt_builder():
    """Мок для PromptBuilder"""
    mock = Mock(spec=PromptBuilder)
    mock.dialog_config = {"turn_order": ["agent_1", "agent_2"]}
    mock.get_agent_config.return_value = {
        "name": "Тестовый агент",
        "emotions": [{"tag": "[ТЕСТ]"}]
    }
    mock.get_temperature.return_value = 0.7
    mock.get_max_tokens.return_value = 100
    mock.build_system_prompt.return_value = "Тестовый промпт"
    return mock

@pytest.fixture
def dialog_manager(mock_gigachat, mock_prompt_builder):
    """Фикстура для DialogManager"""
    return DialogManager(
        gigachat_manager=mock_gigachat,
        prompt_builder=mock_prompt_builder,
        turn_order=["agent_1", "agent_2"],
        max_history=5
    )

def test_dialog_reset(dialog_manager):
    """Тест сброса диалога (строки 344-351)"""
    # Добавляем несколько реплик в историю
    dialog_manager.add_to_history("user", "Тест")
    dialog_manager.reply_count = 5
    dialog_manager.total_tokens = 100
    
    # Сбрасываем диалог
    dialog_manager.reset_dialog()
    
    # Проверяем, что всё сброшено
    assert len(dialog_manager.history) == 0
    assert dialog_manager.reply_count == 0
    assert dialog_manager.total_tokens == 0
    assert dialog_manager.agent_queue[0] == "agent_1"

def test_dialog_summary(dialog_manager):
    """Тест получения сводки диалога (строки 353-362)"""
    # Добавляем тестовые данные
    dialog_manager.reply_count = 3
    dialog_manager.total_tokens = 150
    
    summary = dialog_manager.get_dialog_summary()
    
    # Проверяем, что сводка содержит нужные данные
    assert "СВОДКА ДИАЛОГА" in summary
    assert "Реплик: 3" in summary
    assert "Токенов: 150" in summary

def test_validate_and_fix_reply_empty(dialog_manager):
    """Тест проверки и исправления пустой реплики (строки 185-191)"""
    # Тест для agent_1
    result1 = dialog_manager._validate_and_fix_reply("", "agent_1")
    assert "Интересная мысль" in result1
    
    # Тест для agent_2
    result2 = dialog_manager._validate_and_fix_reply("   ", "agent_2")
    assert "расскажи подробнее" in result2

def test_validate_and_fix_reply_long(dialog_manager):
    """Тест обрезки длинной реплики (строки 193-196)"""
    long_text = "Слово " * 300  # 300 слов, >1000 символов
    result = dialog_manager._validate_and_fix_reply(long_text, "agent_1")
    
    assert len(result) <= 1000
    assert result.endswith("...")

def test_validate_and_fix_reply_forbidden_words(dialog_manager):
    """Тест замены запрещённых слов (строки 220-225)"""
    text_with_forbidden = "Привет, дружище! Как дела?"
    result = dialog_manager._validate_and_fix_reply(text_with_forbidden, "agent_1")
    
    assert "дружище" not in result
    assert "коллега" in result

def test_extract_emotion_found(dialog_manager):
    """Тест извлечения найденной эмоции (строки 229-248)"""
    text_with_emotion = "[ТЕСТ] Привет, как дела?"
    
    # Настраиваем мок для возврата списка эмоций
    agent_config = {"emotions": [{"tag": "[ТЕСТ]"}]}
    
    emotion, clean_text = dialog_manager._extract_emotion(text_with_emotion, agent_config)
    
    assert emotion == "[ТЕСТ]"
    assert clean_text == "Привет, как дела?"

def test_extract_emotion_not_found(dialog_manager):
    """Тест добавления нейтральной эмоции при отсутствии тега (строки 246-248)"""
    text_without_emotion = "Привет, как дела?"
    agent_config = {"emotions": [{"tag": "[ТЕСТ]"}]}
    
    emotion, clean_text = dialog_manager._extract_emotion(text_without_emotion, agent_config)
    
    assert emotion == "[НЕЙТРАЛЬНО]"
    assert clean_text == "Привет, как дела?"

def test_get_next_reply_first_with_topic(dialog_manager):
    """Тест первой реплики с темой (строки 276-289)"""
    # Настраиваем моки
    dialog_manager.gigachat.generate_response.return_value = ("Тестовый ответ", 10)
    
    agent_id, full_text, clean_text, tokens = dialog_manager.get_next_reply(topic="Тестовая тема")
    
    # Проверяем результаты
    assert agent_id == "agent_1"
    assert full_text == "Тестовый ответ"
    assert clean_text == "Тестовый ответ"
    assert tokens == 10
    
    # Проверяем, что был вызван метод генерации с правильными параметрами
    dialog_manager.gigachat.generate_response.assert_called_once()

def test_get_next_reply_exception(dialog_manager):
    """Тест обработки исключения при генерации (строки 304-311)"""
    # Настраиваем мок для выброса исключения
    dialog_manager.gigachat.generate_response.side_effect = Exception("Test error")
    
    agent_id, full_text, clean_text, tokens = dialog_manager.get_next_reply()
    
    # Проверяем, что возвращается заглушка
    # Первый агент в очереди - agent_1
    assert agent_id == "agent_1"
    assert "расскажи подробнее" in full_text or "задумался" in full_text or "Извините" in full_text
    assert tokens == 10

def test_get_statistics(dialog_manager):
    """Тест получения статистики (строки 163-175)"""
    # Добавляем тестовые данные
    dialog_manager.reply_count = 5
    dialog_manager.total_tokens = 250
    dialog_manager.add_to_history("user", "Тест")
    
    stats = dialog_manager.get_statistics()
    
    # Проверяем статистику
    assert stats["total_replies"] == 5
    assert stats["total_tokens"] == 250
    assert stats["history_length"] == 1
    assert "current_turn" in stats
    assert "duration_seconds" in stats

def test_save_dialog_log(dialog_manager):
    """Тест сохранения лога диалога (строки 135-161)"""
    # Добавляем тестовые данные
    dialog_manager.add_to_history("user", "Тест")
    
    with patch("builtins.open") as mock_open:
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        dialog_manager.save_dialog_log("test_dialog.json")
        
        # Проверяем, что файл был открыт для записи
        mock_open.assert_called_once_with("test_dialog.json", 'w', encoding='utf-8')
        
        # Проверяем, что в файл были записаны данные
        # json.dump вызывает write несколько раз, поэтому проверяем, что write был вызван
        assert mock_file.write.call_count > 0