"""Интеграционные тесты"""
import pytest
from src.gigachat_manager import GigaChatManager
from src.prompt_builder import PromptBuilder
from src.dialog_manager import DialogManager
from src.tts_engine import TTSEngine

def test_full_flow():
    """Тест полного цикла без аудио"""
    gm = GigaChatManager(model="GigaChat")
    pb = PromptBuilder("config/agents_config.yaml")
    dm = DialogManager(gm, pb)
    tts = TTSEngine(use_salute=True)
    
    agent_id, full_text, clean_text, tokens = dm.get_next_reply(
        topic="тестовая тема"
    )
    
    assert agent_id in ["agent_1", "agent_2"]
    assert len(clean_text) > 0
    assert tokens > 0
    
    audio_file = tts.text_to_speech(clean_text, agent_id=agent_id)
    assert audio_file is not None