"""Один тест, который покрывает всё в audio_router.py - МАКСИМАЛЬНОЕ ПОКРЫТИЕ"""
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.audio_router import AudioRouter, SILENCE_FALLBACK_PATH, VAC_DEVICE_MAP

def test_audio_router_complete_coverage():
    """ОДИН ТЕСТ, покрывающий 100% строк audio_router.py"""
    
    # ===== ТЕСТ 1: Инициализация и проверка устройств (строки 17-35) =====
    with patch('sounddevice.query_devices') as mock_query:
        mock_query.side_effect = [Exception("Device error"), None, None]
        router = AudioRouter()  # Не должно падать (строка 43-44)
    
    # ===== ТЕСТ 2: Создание заглушки (строки 52-58) =====
    if SILENCE_FALLBACK_PATH.exists():
        SILENCE_FALLBACK_PATH.unlink()
    router = AudioRouter()
    assert SILENCE_FALLBACK_PATH.exists()
    assert SILENCE_FALLBACK_PATH.stat().st_size > 0
    
    # ===== ТЕСТ 3: Стерео -> моно (строки 70-72) =====
    test_file = Path("assets/audio_temp") / "complete_test.wav"
    import soundfile as sf
    stereo = np.column_stack([np.ones(48000), np.ones(48000) * 0.5])
    sf.write(test_file, stereo, 48000)
    
    with patch('sounddevice.play') as mock_play:
        result = router.play_audio(str(test_file), agent_id='agent_1', wait=False)
        assert result is True
    
    # ===== ТЕСТ 4: Ресемплинг (строки 77-83) =====
    test_file2 = Path("assets/audio_temp") / "resample_complete.wav"
    sf.write(test_file2, np.ones(24000), 24000)
    
    with patch('sounddevice.play') as mock_play:
        router.play_audio(str(test_file2), agent_id='agent_1', wait=False)
        args, kwargs = mock_play.call_args
        assert args[1] == 48000
    
    # ===== ТЕСТ 5: Ошибка ресемплинга (строки 134-135) =====
    with patch('scipy.signal.resample') as mock_resample:
        mock_resample.side_effect = Exception("Resample error")
        result = router.play_audio(str(test_file2), agent_id='agent_1', wait=False)
        assert result is False  # Возвращает False при ошибке
    
    # ===== ТЕСТ 6: Нормализация с разными амплитудами (строки 86-96) =====
    # Нормальная амплитуда
    sf.write(test_file, np.ones(48000) * 0.5, 48000)
    with patch('sounddevice.play'):
        result = router.play_audio(str(test_file), agent_id='agent_1', wait=False)
        assert result is True
    
    # ===== ТЕСТ 7: Очень маленькая амплитуда (строки 99, 101) =====
    sf.write(test_file, np.array([0.000001]), 48000)
    result = router.play_audio(str(test_file), agent_id='agent_1', wait=False)
    assert result is True  # Использует заглушку
    
    # ===== ТЕСТ 8: Нулевая амплитуда (строки 99, 101) =====
    sf.write(test_file, np.zeros(48000), 48000)
    result = router.play_audio(str(test_file), agent_id='agent_1', wait=False)
    assert result is True  # Использует заглушку
    
    # ===== ТЕСТ 9: Ошибка нормализации (строки 73-75) =====
    with patch('numpy.max') as mock_max:
        mock_max.side_effect = Exception("Normalization error")
        result = router.play_audio(str(test_file), agent_id='agent_1', wait=False)
        assert result is False
    
    # ===== ТЕСТ 10: Ошибка чтения файла (строки 112, 114, 117) =====
    with patch('soundfile.read') as mock_read:
        mock_read.side_effect = Exception("Read error")
        result = router.play_audio(str(test_file), agent_id='agent_1', wait=False)
        assert result is False
    
    # ===== ТЕСТ 11: Файл не найден (строки 159-161) =====
    result = router.play_audio("nonexistent_file.wav", agent_id='agent_1', wait=False)
    assert result is True  # Использует заглушку
    
    # ===== ТЕСТ 12: Основная ошибка воспроизведения (строки 152-187) =====
    with patch('sounddevice.play') as mock_play:
        mock_play.side_effect = Exception("Playback error")
        result = router.play_audio(str(test_file), agent_id='agent_1', wait=False)
        assert result is False
    
    # ===== ТЕСТ 13: Логирование (строки 140-141) =====
    with patch('logging.Logger.info') as mock_log:
        router.play_audio(str(test_file), agent_id='agent_1', wait=False)
        assert mock_log.called
    
    # ===== ТЕСТ 14: Неверный agent_id (строки 122-123) =====
    with patch('sounddevice.play') as mock_play:
        result = router.play_audio(str(test_file), agent_id='неверный_агент', wait=False)
        assert result is True
        mock_play.assert_called_once()
    
    # ===== ТЕСТ 15: Проверка VAC_DEVICE_MAP (строки 13-14) =====
    assert VAC_DEVICE_MAP is not None
    assert 'agent_1' in VAC_DEVICE_MAP
    assert 'agent_2' in VAC_DEVICE_MAP
    assert VAC_DEVICE_MAP['agent_1'] != VAC_DEVICE_MAP['agent_2']
    
    # ===== ТЕСТ 16: Последний fallback (строки 192-196) =====
    with patch('soundfile.read') as mock_read:
        mock_read.side_effect = Exception("Fatal error")
        result = router.play_audio("fatal_error.wav", agent_id='agent_1', wait=False)
        assert result is False
    
    # ===== ТЕСТ 17: Дополнительная проверка заглушки =====
    assert SILENCE_FALLBACK_PATH.exists()
    fallback_size = SILENCE_FALLBACK_PATH.stat().st_size
    assert fallback_size > 0

def test_silence_fallback_creation():
    """Тест создания файла-заглушки"""
    if SILENCE_FALLBACK_PATH.exists():
        SILENCE_FALLBACK_PATH.unlink()
    router = AudioRouter()
    assert SILENCE_FALLBACK_PATH.exists()
    assert SILENCE_FALLBACK_PATH.stat().st_size > 0

def test_device_fallback():
    """Тест fallback на устройство по умолчанию"""
    router = AudioRouter()
    with patch('sounddevice.play') as mock_play:
        result = router.play_audio(
            str(SILENCE_FALLBACK_PATH), 
            agent_id='неверный_агент', 
            wait=False
        )
        assert result is True
        mock_play.assert_called_once()

def test_audio_router_device_map():
    """Тест маппинга устройств"""
    assert VAC_DEVICE_MAP is not None
    assert 'agent_1' in VAC_DEVICE_MAP
    assert 'agent_2' in VAC_DEVICE_MAP
    assert isinstance(VAC_DEVICE_MAP['agent_1'], int)
    assert isinstance(VAC_DEVICE_MAP['agent_2'], int)

def test_audio_router_device_check_failure():
    """Покрывает строки 43-44"""
    with patch('sounddevice.query_devices') as mock_query:
        mock_query.side_effect = Exception("Device error")
        router = AudioRouter()
        assert router is not None

def test_audio_router_resample_exception():
    """Покрывает строки 134-135"""
    router = AudioRouter()
    test_file = Path("assets/audio_temp") / "resample_exception.wav"
    import soundfile as sf
    sf.write(test_file, np.ones(24000), 24000)

    with patch('scipy.signal.resample') as mock_resample:
        mock_resample.side_effect = Exception("Resample error")
        result = router.play_audio(str(test_file), agent_id='agent_1', wait=False)
        assert result is False

def test_audio_router_playback_exception():
    """Покрывает строки 152-187"""
    router = AudioRouter()
    test_file = Path("assets/audio_temp") / "playback_exception.wav"
    import soundfile as sf
    sf.write(test_file, np.ones(48000), 48000)
    
    with patch('sounddevice.play') as mock_play:
        mock_play.side_effect = Exception("Playback error")
        result = router.play_audio(str(test_file), agent_id='agent_1', wait=False)
        assert result is False

def test_audio_router_final_fallback():
    """Покрывает строки 192-196"""
    router = AudioRouter()
    assert SILENCE_FALLBACK_PATH.exists()
    with patch('soundfile.read') as mock_read:
        mock_read.side_effect = Exception("Read error")
        result = router.play_audio("any_file.wav", agent_id='agent_1', wait=False)
        assert result is False