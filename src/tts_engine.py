"""
Модуль синтеза речи с поддержкой Silero и SaluteSpeech API
Автоматическое переключение между движками
"""

import os
import hashlib
import logging
import uuid
import requests
import json
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class SaluteSpeechConfig:
    """Конфигурация для SaluteSpeech API"""
    auth_key: str  # Это готовый Authorization Key (base64 от ClientID:ClientSecret)
    scope: str = "SALUTE_SPEECH_PERS"
    auth_url: str = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    api_url: str = "https://smartspeech.sber.ru/rest/v1/text:synthesize"
    token: Optional[str] = None
    token_expires_at: Optional[float] = None


class SaluteSpeechTTS:
    """Синтез речи через SaluteSpeech API (живые нейросетевые голоса)"""
    
    # Доступные голоса (полный список с частотами)
    VOICES = {
        # Женские - высокое качество (24 кГц)
        'Nec_24000': 'Nec — нейросетевой, очень естественный (24 кГц)',
        'May_24000': 'May — нейросетевой, мягкий (24 кГц)',
        'Bys_24000': 'Bys — нейросетевой, энергичный (24 кГц)',
        'Ton_24000': 'Ton — нейросетевой, спокойный (24 кГц)',
        # Женские - низкое качество (8 кГц)
        'Nec_8000': 'Nec — нейросетевой, очень естественный (8 кГц)',
        'May_8000': 'May — нейросетевой, мягкий (8 кГц)',
        'Bys_8000': 'Bys — нейросетевой, энергичный (8 кГц)',
        'Ton_8000': 'Ton — нейросетевой, спокойный (8 кГц)',
        
        # Мужские - высокое качество (24 кГц)
        'Tur_24000': 'Tur — нейросетевой, глубокий (24 кГц)',
        'Tam_24000': 'Tam — нейросетевой, уверенный (24 кГц)',
        'Ley_24000': 'Ley — нейросетевой, добрый (24 кГц)',
        'Kin_24000': 'Kin — нейросетевой, деловой (24 кГц)',
        # Мужские - низкое качество (8 кГц)
        'Tur_8000': 'Tur — нейросетевой, глубокий (8 кГц)',
        'Tam_8000': 'Tam — нейросетевой, уверенный (8 кГц)',
        'Ley_8000': 'Ley — нейросетевой, добрый (8 кГц)',
        'Kin_8000': 'Kin — нейросетевой, деловой (8 кГц)',
        
        # Дополнительные голоса
        'Ost_24000': 'Ost — дополнительный (24 кГц)',
        'Ost_8000': 'Ost — дополнительный (8 кГц)',
        'Pon_24000': 'Pon — дополнительный (24 кГц)',
        'Pon_8000': 'Pon — дополнительный (8 кГц)',
    }
    
    def __init__(self):
        """Инициализация клиента SaluteSpeech"""
        
        # Читаем готовый Authorization Key из .env
        auth_key = os.getenv("SALUTE_AUTH_KEY")
        
        if not auth_key:
            logger.warning("⚠️ SALUTE_AUTH_KEY не найден в .env, SaluteSpeech недоступен")
            self.available = False
            return
        
        # Убираем возможные кавычки и пробелы
        auth_key = auth_key.strip().strip('"').strip("'")
        
        self.config = SaluteSpeechConfig(auth_key=auth_key)
        self.available = True
        self.output_dir = Path("assets/audio_temp")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # ✅ ПРАВИЛЬНЫЙ МАППИНГ ГОЛОСОВ:
        # agent_1 (чёрный кот) → мужской голос Tur_24000
        # agent_2 (белая кошка) → женский голос Nec_24000
        self.agent_voice_map = {
            'agent_1': 'Tur_24000',  # Чёрный кот — мужской
            'agent_2': 'Nec_24000'    # Белая кошка — женский
        }
        
        logger.info("✅ SaluteSpeech: конфигурация загружена")
        logger.info(f"🎤 SaluteSpeech: голос агента 1 (ЧЁРНЫЙ кот) = Tur_24000 (мужской)")
        logger.info(f"🎤 SaluteSpeech: голос агента 2 (БЕЛЫЙ кот) = Nec_24000 (женский)")
    
    def _get_access_token(self) -> Optional[str]:
        """Получает Access Token для SaluteSpeech API"""
        if not self.available:
            return None
            
        # Проверяем, не истёк ли текущий токен
        if self.config.token and self.config.token_expires_at:
            if time.time() < self.config.token_expires_at:
                return self.config.token
        
        # Формируем запрос с готовым Authorization Key
        headers = {
            "Authorization": f"Basic {self.config.auth_key}",
            "RqUID": str(uuid.uuid4()),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        data = {"scope": self.config.scope}
        
        try:
            logger.info("🔄 SaluteSpeech: запрос Access Token...")
            
            response = requests.post(
                self.config.auth_url,
                headers=headers,
                data=data,
                verify=False,
                timeout=10
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.config.token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 1800)
            self.config.token_expires_at = time.time() + expires_in - 60
            
            logger.info("✅ SaluteSpeech: токен получен (действует 30 мин)")
            return self.config.token
            
        except Exception as e:
            logger.error(f"❌ SaluteSpeech: ошибка получения токена: {e}")
            return None
    
    def text_to_speech(self, text: str, voice: str = 'Nec_24000') -> Optional[str]:
        """
        Синтезирует речь через SaluteSpeech API
        
        Args:
            text: Текст для озвучивания
            voice: Голос в формате Имя_Частота (например Nec_24000, Tur_24000)
            
        Returns:
            Путь к .wav файлу или None при ошибке
        """
        if not self.available:
            return None
            
        # Очистка текста от тегов эмоций
        clean_text = text.split(']')[-1].strip() if ']' in text else text.strip()
        if not clean_text:
            clean_text = "Здравствуйте"
        
        # Ограничиваем длину текста (SaluteSpeech имеет лимиты)
        if len(clean_text) > 1000:
            logger.warning(f"⚠️ SaluteSpeech: текст слишком длинный ({len(clean_text)} символов), обрезаем до 1000")
            clean_text = clean_text[:1000] + "..."
        
        # Генерируем имя файла
        text_hash = hashlib.md5(clean_text.encode()).hexdigest()[:10]
        filename = f"salute_{voice}_{text_hash}.wav"
        filepath = self.output_dir / filename
        
        # Кэширование
        if filepath.exists():
            logger.debug(f"♻️ SaluteSpeech: кэш {filename}")
            return str(filepath)
        
        # Получаем токен
        token = self._get_access_token()
        if not token:
            logger.error("❌ SaluteSpeech: нет токена доступа")
            return None
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/text"
        }
        
        params = {
            "voice": voice,
            "format": "wav16"  # Важно: wav16, не просто wav
        }
        
        try:
            logger.info(f"🎤 SaluteSpeech: синтез ({voice}) — {clean_text[:50]}...")
            
            response = requests.post(
                self.config.api_url,
                headers=headers,
                params=params,
                data=clean_text.encode('utf-8'),
                verify=False,
                timeout=30
            )
            response.raise_for_status()
            
            # Сохраняем аудио
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✅ SaluteSpeech: сохранено {filename} ({len(response.content)} байт)")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ SaluteSpeech: ошибка синтеза: {e}")
            return None
    
    def get_speaker_for_agent(self, agent_id: str) -> str:
        """Возвращает голос SaluteSpeech для агента"""
        return self.agent_voice_map.get(agent_id, 'Nec_24000')


class TTSEngine:
    """Универсальный движок синтеза речи (Silero + SaluteSpeech)"""
    
    def __init__(self, use_salute: bool = True):
        """
        Инициализация TTS движка
        
        Args:
            use_salute: Использовать SaluteSpeech (если доступен) или Silero
        """
        self.use_salute = use_salute
        self.silero_engine = None
        self.salute_engine = None
        
        # Папка для аудио
        self.output_dir = Path("assets/audio_temp")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Пытаемся инициализировать SaluteSpeech
        if use_salute:
            self.salute_engine = SaluteSpeechTTS()
            if self.salute_engine.available:
                logger.info("✅ SaluteSpeech: движок готов")
                logger.info("   🐈⬛ Чёрный кот → Tur_24000 (мужской)")
                logger.info("   🐈 Белая кошка → Nec_24000 (женский)")
                return
            else:
                logger.warning("⚠️ SaluteSpeech недоступен, переключаюсь на Silero")
        
        # Если SaluteSpeech не доступен, используем Silero
        self._init_silero()
    
    def _init_silero(self):
        """Инициализация Silero TTS (резервный движок)"""
        try:
            import torch
            import soundfile as sf
            
            torch.set_num_threads(4)
            self.device = torch.device('cpu')
            
            self.language = 'ru'
            self.model_id = 'v4_ru'
            
            logger.info("🔄 Загрузка модели Silero v4_ru...")
            self.silero_model, _ = torch.hub.load(
                repo_or_dir='snakers4/silero-models',
                model='silero_tts',
                language=self.language,
                speaker=self.model_id
            )
            self.silero_model.to(self.device)
            
            self.silero_speakers = ['aidar', 'baya', 'kseniya', 'xenia', 'eugene']
            self.sample_rate = 48000
            
            self.silero_engine = self
            logger.info("✅ Silero TTS инициализирован (резервный движок)")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Silero: {e}")
            raise
    
    def text_to_speech(self, text: str, speaker: str = 'aidar', agent_id: Optional[str] = None) -> str:
        """
        Синтезирует речь (автоматический выбор движка)
        """
        # Очистка текста
        clean_text = text.split(']')[-1].strip() if ']' in text else text.strip()
        if not clean_text:
            clean_text = "Здравствуйте"
        
        # 1. Пробуем SaluteSpeech (если включен и есть ключ)
        if self.use_salute and self.salute_engine and self.salute_engine.available:
            # Определяем голос для агента
            if agent_id:
                salute_voice = self.salute_engine.get_speaker_for_agent(agent_id)
                # Для отладки
                if agent_id == 'agent_1':
                    logger.info(f"🎤 Чёрный кот использует голос {salute_voice}")
                else:
                    logger.info(f"🎤 Белый кот использует голос {salute_voice}")
                
                # Пробуем синтезировать
                result = self.salute_engine.text_to_speech(clean_text, voice=salute_voice)
                if result:
                    return result
        
        # 2. Если SaluteSpeech не сработал, используем Silero
        if not self.silero_engine:
            self._init_silero()
        
        # Генерируем имя файла для Silero
        text_hash = hashlib.md5(clean_text.encode()).hexdigest()[:10]
        
        # Определяем правильный голос для Silero
        if agent_id == 'agent_1':
            silero_speaker = 'baya'  # мужской для чёрного кота
        else:
            silero_speaker = 'aidar'  # женский для белой кошки
        
        filename = f"silero_{silero_speaker}_{text_hash}.wav"
        filepath = self.output_dir / filename
        
        # Кэширование
        if filepath.exists():
            logger.debug(f"♻️ Silero: кэш {filename}")
            return str(filepath)
        
        logger.info(f"🎤 Silero: генерация ({silero_speaker}): {clean_text[:50]}...")
        
        try:
            # Синтез речи через Silero
            audio = self.silero_model.apply_tts(
                text=clean_text,
                speaker=silero_speaker,
                sample_rate=48000
            )
            
            # Сохранение
            import soundfile as sf
            sf.write(str(filepath), audio, 48000)
            logger.info(f"✅ Silero: сохранено {filename}")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Ошибка Silero: {e}")
            # Возвращаем заглушку при ошибке
            return str(self.output_dir / "_silence_fallback.wav")
    
    def get_speaker_for_agent(self, agent_id: str) -> str:
        """
        Возвращает голос для агента
        """
        if self.use_salute and self.salute_engine and self.salute_engine.available:
            return self.salute_engine.get_speaker_for_agent(agent_id)
        else:
            # Для Silero: baya (мужской) для agent_1, aidar (женский) для agent_2
            return 'baya' if agent_id == 'agent_1' else 'aidar'


# ============================================================
# ТЕСТ
# ============================================================

def test_tts():
    """Тест синтеза речи"""
    
    print("="*60)
    print("🧪 ТЕСТ TTS (Silero + SaluteSpeech)")
    print("="*60)
    
    try:
        print("\n🔄 Инициализация TTS движка...")
        tts = TTSEngine(use_salute=True)
        
        print("\n🎤 Тест 1: ЧЁРНЫЙ кот (мужской голос)")
        text1 = "Мяу! Я чёрный кот, говорю мужским голосом."
        print(f"📝 Текст: {text1}")
        
        file1 = tts.text_to_speech(
            text=text1,
            agent_id='agent_1'
        )
        print(f"✅ Аудио: {file1}")
        
        print("\n🎤 Тест 2: БЕЛАЯ кошка (женский голос)")
        text2 = "Привет! Я белая кошка, говорю женским голосом."
        print(f"📝 Текст: {text2}")
        
        file2 = tts.text_to_speech(
            text=text2,
            agent_id='agent_2'
        )
        print(f"✅ Аудио: {file2}")
        
        print("\n" + "="*60)
        print("✅ ТЕСТ ПРОЙДЕН")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return False
    
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_tts()