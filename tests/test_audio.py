"""Тесты для AudioRouter"""
import pytest
import numpy as np
import soundfile as sf
from pathlib import Path
from src.audio_router import AudioRouter, VAC_DEVICE_MAP

def test_audio_router_init():
    """Тест инициализации"""
    router = AudioRouter()
    assert router.sample_rate == 48000

def test_play_audio():
    """Тест воспроизведения (без реального звука)"""
    router = AudioRouter()
    
    # Создаём тестовый аудиофайл
    test_dir = Path("assets/audio_temp")
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / "test_audio.wav"
    
    # Генерируем тестовый сигнал (1 секунда тишины)
    sf.write(test_file, np.zeros(48000), 48000)
    
    # Проверяем, что функция не падает
    result = router.play_audio(str(test_file), agent_id='agent_1', wait=False)
    assert result is True

def test_device_mapping():
    """Тест маппинга устройств"""
    # Проверяем, что словарь устройств определён
    assert VAC_DEVICE_MAP is not None
    assert 'agent_1' in VAC_DEVICE_MAP
    assert 'agent_2' in VAC_DEVICE_MAP
    
    # Проверяем, что ID устройств - числа
    assert isinstance(VAC_DEVICE_MAP['agent_1'], int)
    assert isinstance(VAC_DEVICE_MAP['agent_2'], int)
    
    # Проверяем, что ID устройств положительные
    assert VAC_DEVICE_MAP['agent_1'] > 0
    assert VAC_DEVICE_MAP['agent_2'] > 0
    
    # Проверяем, что ID для разных агентов разные
    assert VAC_DEVICE_MAP['agent_1'] != VAC_DEVICE_MAP['agent_2']

def test_play_audio_invalid_file():
    """Тест воспроизведения несуществующего файла"""
    router = AudioRouter()
    result = router.play_audio("несуществующий_файл.wav", agent_id='agent_1', wait=False)
    # Функция возвращает True при использовании заглушки
    assert result is True

def test_play_audio_invalid_agent():
    """Тест воспроизведения с неверным ID агента"""
    router = AudioRouter()
    
    # Создаём тестовый аудиофайл
    test_dir = Path("assets/audio_temp")
    test_file = test_dir / "test_audio.wav"
    
    # Проверяем с несуществующим агентом (должен использовать значение по умолчанию)
    result = router.play_audio(str(test_file), agent_id='несуществующий_агент', wait=False)
    assert result is True

def test_play_audio_with_fallback():
    """Тест использования заглушки при отсутствии файла"""
    router = AudioRouter()
    # Удаляем несуществующий файл, чтобы убедиться, что используется заглушка
    result = router.play_audio("несуществующий_файл_для_теста.wav", agent_id='agent_1', wait=False)
    # Должен вернуть True, так как используется заглушка
    assert result is True