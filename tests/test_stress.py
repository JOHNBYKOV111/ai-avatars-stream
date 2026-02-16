"""Нагрузочные тесты"""
import pytest
import time
import psutil
import os
from src.gigachat_manager import GigaChatManager
from src.prompt_builder import PromptBuilder
from src.dialog_manager import DialogManager

@pytest.mark.slow
def test_long_dialog_stress():
    """Тест длительного диалога (20 реплик)"""
    gm = GigaChatManager(model="GigaChat")
    pb = PromptBuilder("config/agents_config.yaml")
    dm = DialogManager(gm, pb)
    
    start_time = time.time()
    replies_count = 0
    total_tokens = 0
    
    for i in range(20):
        try:
            agent_id, full_text, clean_text, tokens = dm.get_next_reply(
                topic="тест" if i == 0 else None
            )
            replies_count += 1
            total_tokens += tokens
        except Exception as e:
            pytest.fail(f"Ошибка на реплике {i}: {e}")
    
    duration = time.time() - start_time
    
    assert replies_count == 20
    assert total_tokens > 0
    assert duration < 120

@pytest.mark.slow
def test_memory_leak():
    """Тест на утечки памяти"""
    process = psutil.Process(os.getpid())
    memory_start = process.memory_info().rss / 1024 / 1024
    
    gm = GigaChatManager(model="GigaChat")
    pb = PromptBuilder("config/agents_config.yaml")
    dm = DialogManager(gm, pb)
    
    for i in range(20):
        dm.get_next_reply(topic="тест" if i == 0 else None)
    
    memory_end = process.memory_info().rss / 1024 / 1024
    memory_growth = memory_end - memory_start
    
    assert memory_growth < 50, f"Утечка памяти: {memory_growth:.1f} МБ"