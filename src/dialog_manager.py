"""
Менеджер диалога для двух AI-агентов
Управляет очередью, историей, вызовом GigaChat
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from collections import deque
import os
import re

from src.gigachat_manager import GigaChatManager
from src.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)

class DialogManager:
    """
    Управляет диалогом между двумя AI-агентами
    Поддерживает очередь, историю, логирование
    """
    
    # Запрещённые слова для обращений (гендерные ошибки)
    FORBIDDEN_WORDS = ["дружище", "брат", "парень", "чувак", "мужик"]
    
    def __init__(
        self,
        gigachat_manager: GigaChatManager,
        prompt_builder: PromptBuilder,
        turn_order: Optional[List[str]] = None,
        max_history: int = 10
    ):
        """
        Инициализация менеджера диалога
        
        Args:
            gigachat_manager: Экземпляр GigaChatManager
            prompt_builder: Экземпляр PromptBuilder
            turn_order: Очерёдность агентов (по умолчанию из конфига)
            max_history: Максимальная длина истории
        """
        self.gigachat = gigachat_manager
        self.prompt_builder = prompt_builder
        
        # Загружаем порядок из конфига или используем переданный
        if turn_order is None:
            turn_order = self.prompt_builder.dialog_config.get(
                "turn_order", 
                ["agent_1", "agent_2"]
            )
        
        self.turn_order = turn_order
        self.max_history = max_history
        
        # Очередь агентов (бесконечный цикл)
        self.agent_queue = deque(turn_order)
        
        # История диалога
        self.history = []
        
        # Статистика
        self.total_tokens = 0
        self.reply_count = 0
        self.start_time = datetime.now()
        
        logger.info(f"✅ DialogManager инициализирован")
        logger.info(f"📋 Очерёдность: {turn_order}")
        logger.info(f"📚 Макс. история: {max_history} реплик")
    
    def get_next_agent(self) -> str:
        """
        Возвращает следующего агента из очереди и циклически переключает
        
        Returns:
            str: ID агента (например "agent_1")
        """
        agent_id = self.agent_queue[0]
        self.agent_queue.rotate(-1)  # Циклический сдвиг
        logger.debug(f"🔄 Следующий агент: {agent_id}")
        return agent_id
    
    def add_to_history(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Добавляет реплику в историю
        
        Args:
            role: "user" или "assistant"
            content: Текст реплики
            metadata: Дополнительные данные (токены, эмоция, время)
        """
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        if metadata:
            entry.update(metadata)
        
        self.history.append(entry)
        
        # Ограничиваем длину истории
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        logger.debug(f"💾 Добавлено в историю ({role}): {content[:50]}...")
    
    def get_recent_history(self, n: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Возвращает последние N реплик из истории
        
        Args:
            n: Количество реплик (по умолчанию max_history)
            
        Returns:
            List[Dict]: История в формате для GigaChat
        """
        if n is None:
            n = self.max_history
        
        recent = self.history[-n:]
        
        # Преобразуем в формат для API
        formatted = []
        for entry in recent:
            formatted.append({
                "role": entry["role"],
                "content": entry["content"]
            })
        
        return formatted
    
    def save_dialog_log(self, filepath: Optional[str] = None):
        """
        Сохраняет полный диалог в JSON-файл
        
        Args:
            filepath: Путь к файлу (по умолчанию logs/dialog_YYYYMMDD_HHMMSS.json)
        """
        if filepath is None:
            os.makedirs("logs", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"logs/dialog_{timestamp}.json"
        
        dialog_data = {
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_replies": self.reply_count,
            "total_tokens": self.total_tokens,
            "turn_order": self.turn_order,
            "history": self.history
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(dialog_data, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Диалог сохранён в {filepath}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения диалога: {e}")
    
    def get_statistics(self) -> Dict:
        """Возвращает статистику диалога"""
        return {
            "total_replies": self.reply_count,
            "total_tokens": self.total_tokens,
            "average_tokens_per_reply": (
                self.total_tokens / self.reply_count 
                if self.reply_count > 0 else 0
            ),
            "history_length": len(self.history),
            "current_turn": self.agent_queue[0],
            "duration_seconds": (datetime.now() - self.start_time).seconds
        }
    
    def _validate_and_fix_reply(self, text: str, agent_id: str) -> str:
        """
        Проверяет и исправляет реплику
        
        - Проверяет на пустоту
        - Исправляет гендерные ошибки
        - Обрезает слишком длинные ответы
        """
        # 1. Проверка на пустоту
        if not text or len(text.strip()) < 5:
            logger.warning(f"⚠️ Пустая реплика от {agent_id}, заменяю заглушкой")
            if agent_id == "agent_1":
                return "[РАДОСТЬ] Интересная мысль! Продолжим обсуждение?"
            else:
                return "[ЛЮБОПЫТСТВО] Ой, а расскажи подробнее!"
        
        # 2. Обрезка слишком длинных ответов (макс 1000 символов)
        if len(text) > 1000:
            logger.warning(f"⚠️ Реплика слишком длинная ({len(text)} символов), обрезаю до 1000")
            text = text[:997] + "..."
        
        # 3. Исправление гендерных ошибок
        fixed_text = text
        if agent_id == "agent_2":  # Доктор Кошка (женщина)
            # Замена мужских окончаний на женские с использованием регулярных выражений
            replacements = [
                (r'\bя уверен\b', 'я уверена'),
                (r'\bя был\b', 'я была'),
                (r'\bя подумал\b', 'я подумала'),
                (r'\bя сказал\b', 'я сказала'),
                (r'\bя рад\b', 'я рада'),
                (r'\bсогласен\b', 'согласна'),
                (r'\bхотел бы\b', 'хотела бы'),
                (r'\bготов\b', 'готова'),
                (r'\bуверен\b', 'уверена'),
                (r'\bбыл\b', 'была'),
                (r'\bподумал\b', 'подумала'),
                (r'\bсказал\b', 'сказала'),
                (r'\bрад\b', 'рада'),
            ]
            for wrong, correct in replacements:
                fixed_text = re.sub(wrong, correct, fixed_text, flags=re.IGNORECASE)
        
        # 4. Проверка на запрещённые слова (для любого агента)
        for word in self.FORBIDDEN_WORDS:
            if word in fixed_text.lower():
                logger.warning(f"⚠️ Найдено запрещённое слово '{word}', удаляю")
                # Удаляем слово (с сохранением пробелов)
                fixed_text = re.sub(rf'\b{word}\b', 'коллега', fixed_text, flags=re.IGNORECASE)
        
        return fixed_text
    
    def _extract_emotion(self, text: str, agent_config: Dict) -> Tuple[str, str]:
        """
        Извлекает тег эмоции из текста
        
        Returns:
            Tuple[str, str]: (эмоция, текст без эмоции)
        """
        default_emotion = "[НЕЙТРАЛЬНО]"
        
        # Ищем тег в тексте
        for emotion in agent_config.get("emotions", []):
            tag = emotion["tag"]
            if tag in text:
                # Если тег найден, удаляем его из текста
                clean_text = text.replace(tag, "").strip()
                return tag, clean_text
        
        # Если тег не найден, добавляем нейтральный в начало
        logger.warning(f"⚠️ Тег эмоции не найден, добавляю {default_emotion}")
        return default_emotion, text.strip()
    
    def get_next_reply(self, topic: Optional[str] = None) -> Tuple[str, str, str, int]:
        """
        Генерирует следующую реплику в диалоге
        
        Returns:
            Tuple[str, str, str, int]: 
                - ID агента
                - Полный текст ответа (с тегом эмоции)
                - Текст без тега (для TTS)
                - Количество токенов
        """
        # 1. Получаем следующего агента
        agent_id = self.get_next_agent()
        agent_config = self.prompt_builder.get_agent_config(agent_id)
        agent_name = agent_config["name"]
        
        logger.info(f"🎭 Ход агента: {agent_name} ({agent_id})")
        
        # 2. Получаем историю диалога
        history = self.get_recent_history()
        
        # 3. Определяем, первая ли это реплика
        is_first = (self.reply_count == 0)
        
        # 4. Формируем промпт и получаем ответ
        try:
            if is_first and topic:
                # Первая реплика - задаём тему
                prompt = self.prompt_builder.build_system_prompt(
                    agent_id=agent_id,
                    is_first_reply=True,
                    topic=topic
                )
                response_text, tokens = self.gigachat.generate_response(
                    system_prompt=prompt,
                    history=[],
                    user_input=None,
                    temperature=self.prompt_builder.get_temperature(agent_id),
                    max_tokens=self.prompt_builder.get_max_tokens(agent_id)
                )
            else:
                # Обычная реплика с историей
                system_prompt = self.prompt_builder.build_system_prompt(
                    agent_id=agent_id,
                    history=history
                )
                
                response_text, tokens = self.gigachat.generate_response(
                    system_prompt=system_prompt,
                    history=history,
                    user_input=None,
                    temperature=self.prompt_builder.get_temperature(agent_id),
                    max_tokens=self.prompt_builder.get_max_tokens(agent_id)
                )
        except Exception as e:
            logger.error(f"❌ Ошибка генерации ответа: {e}")
            # Заглушка при ошибке
            if agent_id == "agent_1":
                response_text = "[РАДОСТЬ] Что-то я задумался. Продолжим?"
            else:
                response_text = "[ЛЮБОПЫТСТВО] Ой, а давай вернёмся к теме!"
            tokens = 10
        
        # 5. Проверяем и исправляем реплику
        response_text = self._validate_and_fix_reply(response_text, agent_id)
        
        # 6. Обновляем статистику
        self.reply_count += 1
        self.total_tokens += tokens
        
        # 7. Извлекаем эмоцию из текста
        emotion_tag, clean_text = self._extract_emotion(response_text, agent_config)
        
        # 8. Сохраняем в историю (полный текст с тегом)
        metadata = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "emotion": emotion_tag,
            "tokens": tokens,
            "temperature": self.prompt_builder.get_temperature(agent_id)
        }
        
        self.add_to_history(
            role="assistant",
            content=response_text,
            metadata=metadata
        )
        
        logger.info(f"💬 {agent_name}: {clean_text[:100]}...")
        logger.info(f"📊 Токенов: {tokens}, Эмоция: {emotion_tag}")
        
        # 9. Возвращаем всё, что нужно для VTube и TTS
        return agent_id, response_text, clean_text, tokens
    
    def reset_dialog(self):
        """Сбрасывает диалог в начальное состояние"""
        self.history = []
        self.agent_queue = deque(self.turn_order)
        self.reply_count = 0
        self.total_tokens = 0
        self.start_time = datetime.now()
        logger.info("🔄 Диалог сброшен")
    
    def get_dialog_summary(self) -> str:
        """Возвращает краткую сводку диалога"""
        stats = self.get_statistics()
        summary = f"""
📋 СВОДКА ДИАЛОГА:
   Реплик: {stats['total_replies']}
   Токенов: {stats['total_tokens']}
   Время: {stats['duration_seconds']} сек
   Текущий агент: {stats['current_turn']}
        """
        return summary