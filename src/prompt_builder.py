"""
Построитель промптов для агентов GigaChat
Загружает конфигурацию из YAML, подставляет переменные и историю
"""

import yaml
import os
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PromptBuilder:
    """Загружает конфигурацию агентов и формирует промпты"""
    
    def __init__(self, config_path: str = "config/agents_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.dialog_config = self.config.get("dialog", {})
        self.templates = self.config.get("templates", {})
        
    def _load_config(self) -> Dict:
        """Загружает YAML конфигурацию"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"✅ Загружена конфигурация агентов из {self.config_path}")
            logger.info(f"📋 Агенты: {list(config['agents'].keys())}")
            return config
        except FileNotFoundError:
            logger.error(f"❌ Файл {self.config_path} не найден")
            raise
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки конфигурации: {e}")
            raise
    
    def get_agent_config(self, agent_id: str) -> Dict:
        """Возвращает конфигурацию агента по ID"""
        agent = self.config["agents"].get(agent_id)
        if not agent:
            raise ValueError(f"❌ Агент {agent_id} не найден в конфигурации")
        return agent
    
    def get_emotion_list(self, agent_id: str) -> str:
        """Возвращает список доступных эмоций агента в виде строки"""
        agent = self.get_agent_config(agent_id)
        emotions = [e["tag"] for e in agent.get("emotions", [])]
        return ", ".join(emotions)
    
    def format_speech_patterns(self, agent_id: str) -> str:
        """Форматирует особенности речи в читаемый текст"""
        agent = self.get_agent_config(agent_id)
        patterns = agent.get("speech_patterns", [])
        return "\n".join([f"- {p}" for p in patterns])
    
    def format_topics(self, agent_id: str) -> str:
        """Форматирует научные темы"""
        agent = self.get_agent_config(agent_id)
        topics = agent.get("topics", [])
        return ", ".join(topics)
    
    def build_system_prompt(
        self,
        agent_id: str,
        history: Optional[List[Dict[str, str]]] = None,
        is_first_reply: bool = False,
        topic: str = "старение клеток"
    ) -> str:
        """
        Формирует системный промпт для агента
        
        Args:
            agent_id: ID агента
            history: История диалога
            is_first_reply: Это первая реплика в диалоге?
            topic: Тема для обсуждения (для первой реплики)
            
        Returns:
            str: Готовый промпт для отправки в GigaChat
        """
        agent = self.get_agent_config(agent_id)
        
        # Если это первая реплика - используем шаблон приветствия
        if is_first_reply:
            first_prompt = self.templates.get("first_reply", "")
            return first_prompt.format(
                name=agent["name"],
                topic=topic
            )
        
        # Подготавливаем переменные для подстановки
        vars_dict = {
            "name": agent["name"],
            "role": agent["role"],
            "specialization": agent["specialization"],
            "description": agent.get("description", ""),
            "style": agent["style"],
            "mood": agent.get("mood", "нейтральное"),  # 👈 ДОБАВЛЕНА СТРОКА
            "speech_patterns": self.format_speech_patterns(agent_id),
            "topics": self.format_topics(agent_id),
            "emotion_list": self.get_emotion_list(agent_id),
            "history": self._format_history(history)
        }
        
        # Берём шаблон из конфига и подставляем переменные
        prompt_template = agent["system_prompt"]
        
        try:
            prompt = prompt_template.format(**vars_dict)
            logger.debug(f"✅ Сформирован промпт для {agent['name']}")
            return prompt
        except KeyError as e:
            logger.error(f"❌ Ошибка форматирования промпта: {e}")
            logger.error(f"   Проверьте переменные в шаблоне для {agent_id}")
            logger.error(f"   Доступные переменные: {list(vars_dict.keys())}")
            raise
    
    def _format_history(self, history: Optional[List[Dict[str, str]]]) -> str:
        """Форматирует историю диалога в читаемый текст"""
        if not history:
            return "Диалог начинается."
        
        formatted = []
        for msg in history[-self.dialog_config.get("max_history", 10):]:
            role = "Собеседник" if msg["role"] == "user" else "Вы"
            formatted.append(f"{role}: {msg['content']}")
        
        return "\n".join(formatted)
    
    def get_agent_name(self, agent_id: str) -> str:
        """Возвращает имя агента"""
        return self.get_agent_config(agent_id)["name"]
    
    def get_agent_voice(self, agent_id: str) -> str:
        """Возвращает голос агента для TTS"""
        return self.get_agent_config(agent_id).get("voice", "aidar")
    
    def get_emotion_animation(self, agent_id: str, emotion_tag: str) -> str:
        """Возвращает название анимации для VTube Studio по тегу эмоции"""
        agent = self.get_agent_config(agent_id)
        for emotion in agent.get("emotions", []):
            if emotion["tag"] == emotion_tag:
                return emotion.get("animation", "Idle")
        return "Idle"
    
    def get_temperature(self, agent_id: str) -> float:
        """Возвращает температуру генерации для агента"""
        return self.get_agent_config(agent_id).get("temperature", 0.7)
    
    def get_max_tokens(self, agent_id: str) -> int:
        """Возвращает максимальное количество токенов"""
        return self.get_agent_config(agent_id).get("max_tokens", 350)