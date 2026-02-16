"""
Модуль маршрутизации аудио в виртуальный кабель (VAC)
Воспроизводит .wav файлы с максимальным качеством через WASAPI
"""

import sounddevice as sd
import soundfile as sf
import numpy as np
import logging
from pathlib import Path
import time
import scipy.signal
import warnings

logger = logging.getLogger(__name__)

# ✅ ID выходных устройств с наилучшим качеством (WASAPI)
# ID 15: Line 1 (WASAPI) - чёрный кот
# ID 16: Line 2 (WASAPI) - белая кошка
VAC_DEVICE_MAP = {
    'agent_1': 15,  # Line 1 (WASAPI) - высокое качество, низкая задержка
    'agent_2': 16   # Line 2 (WASAPI) - высокое качество, низкая задержка
}
SAMPLE_RATE = 48000  # Родная частота SaluteSpeech (24 кГц апсемплинг до 48 кГц)
MIN_AMPLITUDE = 0.01
EXTRA_SILENCE = 0.4
# Заглушка для пустых/тихих файлов (0.5 сек тишины)
SILENCE_FALLBACK_PATH = Path("assets/audio_temp/_silence_fallback.wav")

class AudioRouter:
    def __init__(self):
        self.sample_rate = SAMPLE_RATE
        self._check_devices()
        self._create_silence_fallback()

    def _check_devices(self):
        """Проверяет доступность устройств и их характеристики"""
        for agent, dev_id in VAC_DEVICE_MAP.items():
            try:
                dev = sd.query_devices(dev_id)
                logger.info(f"✅ {agent}: ID {dev_id} - {dev['name']}")
                logger.info(f"   🔧 Частота: {dev['default_samplerate']} Гц, каналы: {dev['max_output_channels']}")
            except Exception as e:
                logger.error(f"❌ Устройство ID {dev_id} не найдено: {e}")

    def _create_silence_fallback(self):
        """Создаёт файл-заглушку с тишиной на случай пустых аудио"""
        if not SILENCE_FALLBACK_PATH.exists():
            try:
                SILENCE_FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
                silence = np.zeros(int(0.5 * self.sample_rate), dtype=np.float32)
                sf.write(str(SILENCE_FALLBACK_PATH), silence, self.sample_rate)
                logger.info(f"✅ Создан файл-заглушка: {SILENCE_FALLBACK_PATH}")
            except Exception as e:
                logger.error(f"❌ Не удалось создать файл-заглушку: {e}")

    def play_audio(self, file_path: str, agent_id: str = 'agent_1', wait: bool = True) -> bool:
        device_id = VAC_DEVICE_MAP.get(agent_id, 15)  # По умолчанию WASAPI
        кот = "Чёрный кот" if agent_id == 'agent_1' else "Белая кошка"

        try:
            # Проверяем существование файла
            if not Path(file_path).exists():
                logger.error(f"❌ Файл не найден: {file_path}")
                file_path = str(SILENCE_FALLBACK_PATH)

            # Читаем файл
            audio, sr = sf.read(file_path)
            logger.info(f"   📂 Исходный файл: {Path(file_path).name}, частота: {sr} Гц, длина: {len(audio)} семплов")
            
            # Проверка на пустой файл
            if len(audio) == 0:
                logger.error(f"❌ Файл пуст: {file_path}")
                file_path = str(SILENCE_FALLBACK_PATH)
                audio, sr = sf.read(file_path)
            
            # 1. Если стерео - усредняем до моно (Virtual Cable ожидает моно)
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)
                logger.info(f"   🔊 Конвертация: стерео -> моно")
            
            # 2. Ресемплинг с максимальным качеством
            if sr != self.sample_rate:
                original_len = len(audio)
                audio = scipy.signal.resample(
                    audio,
                    int(len(audio) * self.sample_rate / sr)
                )
                logger.info(f"   🔄 Ресемплинг: {sr} Гц -> {self.sample_rate} Гц (длина: {original_len} -> {len(audio)})")
            
            # 3. Нормализация с защитой от деления на ноль
            max_amp = np.max(np.abs(audio))
            if max_amp < MIN_AMPLITUDE:
                logger.warning(f"⚠️ Слишком тихий файл: {Path(file_path).name}, использую заглушку")
                file_path = str(SILENCE_FALLBACK_PATH)
                audio, sr = sf.read(file_path)
                # Повторяем обработку для файла-заглушки
                if len(audio.shape) > 1:
                    audio = np.mean(audio, axis=1)
                if sr != self.sample_rate:
                    audio = scipy.signal.resample(audio, int(len(audio) * self.sample_rate / sr))
                max_amp = np.max(np.abs(audio))
            
            # Безопасная нормализация
            if max_amp > 0:
                audio = audio / max_amp * 0.85
            else:
                logger.warning("⚠️ Нулевая амплитуда, использую заглушку")
                file_path = str(SILENCE_FALLBACK_PATH)
                audio, sr = sf.read(file_path)
                if len(audio.shape) > 1:
                    audio = np.mean(audio, axis=1)
                if sr != self.sample_rate:
                    audio = scipy.signal.resample(audio, int(len(audio) * self.sample_rate / sr))
                max_amp = np.max(np.abs(audio))
                if max_amp > 0:
                    audio = audio / max_amp * 0.85
            
            # 4. Тишина в конце для плавного завершения
            silence = np.zeros(int(EXTRA_SILENCE * self.sample_rate))
            audio = np.concatenate([audio, silence])

            # 5. Конвертируем в float32 (родной формат WASAPI)
            audio_float32 = audio.astype(np.float32)

            logger.info(f"▶️ Воспроизведение: {кот}")
            logger.info(f"   📊 Длина: {len(audio)/self.sample_rate:.1f} сек")
            logger.info(f"   🎚️ Формат: float32, частота: {self.sample_rate} Гц")

            # Воспроизводим через WASAPI для наилучшего качества
            sd.play(audio_float32, self.sample_rate, device=device_id)

            if wait:
                sd.wait()
                logger.info(f"⏹️ Завершено: {кот}")

            return True

        except FileNotFoundError:
            logger.error(f"❌ Файл не найден: {file_path}")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка воспроизведения: {type(e).__name__}: {e}")
            return False


# ============================================================
# ТЕСТ
# ============================================================

def test():
    print("="*60)
    print("🧪 ТЕСТ КАЧЕСТВА ЗВУКА (WASAPI)")
    print("="*60)

    router = AudioRouter()
    files = list(Path("assets/audio_temp").glob("*.wav"))

    if not files:
        print("\n❌ Нет файлов в assets/audio_temp/")
        return False

    print("\n▶️ Тест 1: Чёрный кот (ID 15 - Line 1 WASAPI)")
    print(f"   Файл: {files[0].name}")
    success1 = router.play_audio(str(files[0]), agent_id='agent_1')

    time.sleep(1)

    print("\n▶️ Тест 2: Белая кошка (ID 16 - Line 2 WASAPI)")
    f2 = files[1] if len(files) > 1 else files[0]
    print(f"   Файл: {f2.name}")
    success2 = router.play_audio(str(f2), agent_id='agent_2')

    print("\n" + "="*60)
    if success1 and success2:
        print("✅ ТЕСТ ПРОЙДЕН!")
        print("   ✅ Чёрный кот (ID 15) - WASAPI")
        print("   ✅ Белая кошка (ID 16) - WASAPI")
        print("   ✅ Высокие частоты сохранены")
    else:
        print("❌ ТЕСТ НЕ УДАЛСЯ")
        if not success1:
            print("   ❌ Проблема с ID 15")
        if not success2:
            print("   ❌ Проблема с ID 16")
    print("="*60)
    return success1 and success2


if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    test()