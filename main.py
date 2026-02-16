#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ГЛАВНЫЙ СКРИПТ ПРОЕКТА AI AVATARS STREAM
==========================================
Фаза 5: Полная интеграция и запуск стрима
- Основной цикл диалога
- Управление OBS (подсветка)
- TTS + VAC + VTube Studio (поддержка двух кабелей)
- Обработка сигналов
- Логирование и статистика
- Диагностика времени выполнения
- Естественное завершение с прощанием
"""

import sys
import os
import time
import logging
import signal
from pathlib import Path

# Добавляем корневую папку в путь
sys.path.append(str(Path(__file__).parent))

from src.gigachat_manager import GigaChatManager
from src.prompt_builder import PromptBuilder
from src.dialog_manager import DialogManager
from src.tts_engine import TTSEngine
from src.audio_router import AudioRouter
from src.obs_controller import OBSController

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/stream.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AIAvatarStream:
    """Главный класс стрима"""
    
    def __init__(self):
        """Инициализация всех компонентов"""
        logger.info("="*70)
        logger.info("🚀 ЗАПУСК AI AVATARS STREAM")
        logger.info("="*70)
        
        self.running = True
        self.current_agent = None
        
        try:
            # 1. Подключение к OBS
            logger.info("\n🎬 Подключение к OBS...")
            self.obs = OBSController()
            
            # 2. Инициализация GigaChat
            logger.info("\n📡 Подключение к GigaChat...")
            self.gigachat = GigaChatManager(model="GigaChat")
            
            # 3. Загрузка конфигурации агентов
            logger.info("\n📋 Загрузка агентов...")
            self.prompt_builder = PromptBuilder("config/agents_config.yaml")
            
            # 4. Создание менеджера диалога
            logger.info("\n💬 Создание диалога...")
            self.dialog = DialogManager(self.gigachat, self.prompt_builder)
            
            # 5. Инициализация TTS
            logger.info("\n🎤 Загрузка голосов...")
            self.tts = TTSEngine(use_salute=True)
            
            # 6. Инициализация аудио-маршрутизатора
            logger.info("\n🔌 Подключение к VAC (два кабеля)...")
            self.audio = AudioRouter()
            
            # 7. Настройка обработчика сигналов
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            
            logger.info("\n✅ ВСЕ КОМПОНЕНТЫ ГОТОВЫ!")
            logger.info("="*70)
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка инициализации: {e}")
            self.cleanup()
            raise
    
    def signal_handler(self, signum, frame):
        """Обработка сигналов завершения"""
        logger.info("\n\n⏹️ Получен сигнал завершения...")
        self.running = False
    
    def run_dialog_round(self, agent_id, topic=None):
        """
        Единый цикл для одного говорящего с диагностикой времени
        
        Args:
            agent_id: ID агента ("agent_1" или "agent_2")
            topic: Тема для первой реплики
        
        Returns:
            bool: Успешно ли выполнен раунд
        """
        round_start = time.time()
        
        try:
            # 1. Генерируем реплику
            gen_start = time.time()
            agent_id, full_text, clean_text, tokens = self.dialog.get_next_reply(
                topic=topic if self.dialog.reply_count == 0 else None
            )
            gen_time = time.time() - gen_start
            logger.info(f"⏱️ GigaChat ответил за {gen_time:.2f} сек")
            
            # 2. Получаем данные агента
            agent_config = self.prompt_builder.get_agent_config(agent_id)
            agent_name = agent_config['name']
            speaker = self.tts.get_speaker_for_agent(agent_id)
            
            # 3. Переключаем подсветку в OBS
            self.obs.set_active_speaker(agent_id)
            
            logger.info(f"\n🗣️ [{agent_name}] ({speaker})")
            logger.info(f"   {clean_text}")
            
            # 4. Синтезируем речь
            tts_start = time.time()
            audio_file = self.tts.text_to_speech(clean_text, agent_id=agent_id)
            tts_time = time.time() - tts_start
            logger.info(f"⏱️ TTS сгенерировал за {tts_time:.2f} сек")
            
            # 5. Воспроизводим в VAC с указанием агента
            audio_start = time.time()
            self.audio.play_audio(audio_file, agent_id=agent_id, wait=True)
            audio_time = time.time() - audio_start
            logger.info(f"⏱️ Воспроизведение длилось {audio_time:.2f} сек")
            
            # 6. Минимальная пауза между репликами (только для естественности)
            time.sleep(0.8)
            
            round_time = time.time() - round_start
            logger.info(f"⏱️ ОБЩЕЕ ВРЕМЯ РАУНДА: {round_time:.2f} сек")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка в раунде диалога: {e}")
            return False
    
    def run_stream(self, turns=6, topic="роль теломер в старении клеток"):
        """
        Главный цикл стрима
        
        Args:
            turns: Количество реплик
            topic: Тема обсуждения
        """
        logger.info("\n" + "="*70)
        logger.info(f"🎬 НАЧАЛО СТРИМА")
        logger.info(f"📋 Тема: {topic}")
        logger.info(f"🔄 Реплик: {turns}")
        logger.info("="*70)
        
        try:
            # Сброс диалога
            self.dialog.reset_dialog()
            
            # Основной цикл
            while self.running and self.dialog.reply_count < turns:
                # Получаем следующего агента без генерации
                next_agent = self.dialog.agent_queue[0]
                
                # Выполняем раунд
                success = self.run_dialog_round(
                    next_agent, 
                    topic if self.dialog.reply_count == 0 else None
                )
                
                if not success:
                    logger.warning("⚠️ Пропускаем реплику...")
                    time.sleep(1)
                    continue
                
                # Небольшая пауза для читаемости лога
                time.sleep(0.3)
            
        except Exception as e:
            logger.error(f"❌ Ошибка в основном цикле: {e}")
        
        finally:
            self.finish_stream()
    
    def finish_stream(self):
        """Завершение стрима с естественным прощанием"""
        logger.info("\n" + "="*70)
        logger.info("🏁 ЗАВЕРШЕНИЕ СТРИМА")
        logger.info("="*70)
        
        # Финальная реплика-прощание
        try:
            logger.info("\n💬 Финальное прощание...")
            
            # Выбираем агента для прощания (Профессор Кот)
            agent_id = "agent_1"
            agent_config = self.prompt_builder.get_agent_config(agent_id)
            agent_name = agent_config['name']
            
            farewell_text = f"[РАДОСТЬ] Спасибо за увлекательную дискуссию, дорогая коллега! Было очень интересно обсудить теломеры и старение. До новых встреч!"
            
            # Извлекаем чистый текст для TTS
            clean_farewell = farewell_text.split(']')[-1].strip()
            
            logger.info(f"\n🗣️ [{agent_name}] (прощание)")
            logger.info(f"   {clean_farewell}")
            
            # Синтезируем и воспроизводим прощание
            audio_file = self.tts.text_to_speech(clean_farewell, agent_id=agent_id)
            self.audio.play_audio(audio_file, agent_id=agent_id, wait=True)
            
            # Небольшая пауза после прощания
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"❌ Ошибка при прощании: {e}")
        
        # Сохраняем лог диалога
        self.dialog.save_dialog_log()
        
        # Показываем статистику
        stats = self.dialog.get_statistics()
        logger.info("\n📊 СТАТИСТИКА:")
        logger.info(f"   Реплик: {stats['total_replies']}")
        logger.info(f"   Токенов: {stats['total_tokens']}")
        logger.info(f"   Среднее: {stats['average_tokens_per_reply']:.0f} токенов/реплика")
        logger.info(f"   Время: {stats['duration_seconds']} сек")
        
        # Сбрасываем подсветку в OBS (оба кота яркие)
        try:
            self.obs._set_filter_state("Захват окна", "Хромакей", False)
            self.obs._set_filter_state("Захват окна 2", "Хромакей", False)
        except:
            pass
        
        self.cleanup()
    
    def cleanup(self):
        """Очистка ресурсов"""
        logger.info("\n🧹 Очистка ресурсов...")
        
        try:
            self.obs.disconnect()
        except:
            pass
        
        logger.info("✅ Ресурсы освобождены")


def main():
    """Точка входа"""
    # Создаём необходимые папки
    os.makedirs("logs", exist_ok=True)
    os.makedirs("assets/audio_temp", exist_ok=True)
    
    stream = None
    
    try:
        # Создаём экземпляр стрима
        stream = AIAvatarStream()
        
        # Запускаем стрим
        stream.run_stream(
            turns=6,
            topic="роль теломер в старении клеток"
        )
        
    except KeyboardInterrupt:
        logger.info("\n\n👋 Программа остановлена пользователем")
        if stream:
            stream.cleanup()
    
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        if stream:
            stream.cleanup()
        raise
    
    logger.info("\n✨ Стрим-сессия завершена")
    logger.info("="*70 + "\n")


if __name__ == "__main__":
    main()