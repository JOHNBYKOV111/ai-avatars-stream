"""Тесты обработки пустых реплик"""
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

def test_empty_reply_handling(dialog_manager):
    """Тест обработки пустой реплики"""
    empty_replies = ["", " ", "✨", ".", "??", "..."]
    
    for agent_id in ["agent_1", "agent_2"]:
        for empty in empty_replies:
            fixed = dialog_manager._validate_and_fix_reply(empty, agent_id)
            assert len(fixed) > 10, f"Слишком короткий ответ для '{empty}'"
            assert "[" in fixed, f"Нет тега эмоции в ответе для '{empty}'"
            # Проверяем, что это не пустой ответ
            assert fixed != empty, f"Ответ не изменился для '{empty}'"

def test_forbidden_words_filter(dialog_manager):
    """Тест фильтрации запрещённых слов"""
    # Запрещённые слова из класса DialogManager
    forbidden = ["дружище", "брат", "парень", "чувак", "мужик"]
    
    test_phrases = [
        ("Привет, дружище!", "Привет, коллега!"),
        ("Слушай, брат, это интересно", "Слушай, коллега, это интересно"),
        ("Эй, парень, как дела?", "Эй, коллега, как дела?"),
        ("Спасибо, чувак!", "Спасибо, коллега!"),
        ("Ну ты даёшь, мужик!", "Ну ты даёшь, коллега!"),
    ]
    
    for agent_id in ["agent_1", "agent_2"]:
        for bad_phrase, expected_good in test_phrases:
            fixed = dialog_manager._validate_and_fix_reply(bad_phrase, agent_id)
            
            # Проверяем, что все запрещённые слова заменены
            for word in forbidden:
                assert word not in fixed.lower(), f"Найдено запрещённое слово '{word}' в '{fixed}'"
            
            # Проверяем, что длина осталась разумной
            assert len(fixed) > 0
            assert len(fixed) < 1000

def test_very_long_reply_truncation(dialog_manager):
    """Тест обрезки слишком длинных ответов"""
    # Создаём очень длинный текст (2000 символов)
    long_text = "а" * 2000
    
    for agent_id in ["agent_1", "agent_2"]:
        fixed = dialog_manager._validate_and_fix_reply(long_text, agent_id)
        assert len(fixed) <= 1000, f"Ответ не обрезан: {len(fixed)} > 1000"

def test_gender_fixes(dialog_manager):
    """Тест исправления гендерных окончаний"""
    # Только для agent_2 (женский род)
    test_phrases = [
        ("я уверен", "я уверена"),
        ("я был", "я была"),
        ("я подумал", "я подумала"),
        ("я сказал", "я сказала"),
        ("я рад", "я рада"),
        ("согласен", "согласна"),
        ("хотел бы", "хотела бы"),
        ("готов", "готова"),
    ]
    
    agent_id = "agent_2"  # Только для женского агента
    
    for wrong, correct in test_phrases:
        # Создаём предложение с неправильным окончанием
        test_text = f"Я {wrong} с этим утверждением."
        fixed = dialog_manager._validate_and_fix_reply(test_text, agent_id)
        
        # Проверяем, что исправление произошло
        assert correct in fixed.lower() or wrong not in fixed.lower()
        # Исходное неправильное слово должно быть заменено или отсутствовать
        assert wrong not in fixed.lower() or correct in fixed.lower()

def test_mixed_fixes(dialog_manager):
    """Тест комбинации разных исправлений"""
    agent_id = "agent_2"
    
    # Смесь запрещённых слов и неправильных окончаний
    test_text = "Привет, дружище! Я был очень рад это услышать."
    
    fixed = dialog_manager._validate_and_fix_reply(test_text, agent_id)
    
    # Проверяем замену запрещённого слова
    assert "дружище" not in fixed.lower()
    assert "коллега" in fixed.lower() or fixed != test_text
    
    # Проверяем исправление окончаний
    assert "я была" in fixed.lower() or "я был" not in fixed.lower()
    assert "рада" in fixed.lower() or "рад" not in fixed.lower()
    
    # Проверяем, что текст не стал пустым
    assert len(fixed) > 10

def test_no_fixes_needed(dialog_manager):
    """Тест корректных фраз, которые не нужно исправлять"""
    test_phrases = [
        "[РАДОСТЬ] Привет, дорогая коллега!",
        "Я уверена в этом утверждении.",
        "Спасибо за интересную дискуссию, коллега.",
        "Это очень важное открытие!",
    ]
    
    for agent_id in ["agent_1", "agent_2"]:
        for phrase in test_phrases:
            fixed = dialog_manager._validate_and_fix_reply(phrase, agent_id)
            # Фраза может немного измениться, но не должна стать пустой
            assert len(fixed) > 0
            # Не должно быть ошибок
            assert fixed is not None

def test_agent_specific_fixes(dialog_manager):
    """Тест, что исправления применяются только к нужным агентам"""
    test_text = "Я уверен, что это правильно."
    
    # Для agent_1 (мужской) - не должно меняться
    fixed_1 = dialog_manager._validate_and_fix_reply(test_text, "agent_1")
    assert "я уверен" in fixed_1.lower()
    
    # Для agent_2 (женский) - должно исправиться
    fixed_2 = dialog_manager._validate_and_fix_reply(test_text, "agent_2")
    assert "я уверена" in fixed_2.lower() or "я уверен" not in fixed_2.lower()