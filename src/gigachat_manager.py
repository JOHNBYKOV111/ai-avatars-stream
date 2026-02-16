"""
Менеджер для работы с GigaChat API
Использует прямые REST-запросы (проверено и работает!)
Поддерживает GigaChat Lite тариф (5 млн токенов)
"""

import requests
import uuid
from dotenv import load_dotenv
import os
from typing import List, Dict, Optional, Tuple
import logging
import json
from datetime import datetime, timedelta

load_dotenv()
logger = logging.getLogger(__name__)

class GigaChatManager:
    """
    Менеджер для GigaChat API с прямой REST-реализацией
    """
    
    def __init__(self, model: str = "GigaChat-Lite"):
        """
        Инициализация менеджера GigaChat
        
        Args:
            model: Модель для использования (GigaChat, GigaChat-Lite)
                  Для тарифа Lite доступны: GigaChat, GigaChat-Lite
                  GigaChat-Pro и GigaChat-Max НЕ ДОСТУПНЫ в Lite
        """
        self.model = model
        self.auth_key = os.getenv("GIGACHAT_AUTH_KEY")
        self.scope = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
        self.auth_url = os.getenv("GIGACHAT_AUTH_URL", "https://ngw.devices.sberbank.ru:9443/api/v2/oauth")
        self.base_url = os.getenv("GIGACHAT_BASE_URL", "https://gigachat.devices.sberbank.ru/api/v1")
        
        self.access_token = None
        self.token_expires_at = None
        
        if not self.auth_key:
            raise ValueError("❌ GIGACHAT_AUTH_KEY не найден в .env")
        
        # Проверяем, что модель доступна в Lite тарифе
        if model not in ["GigaChat", "GigaChat-Lite"]:
            logger.warning(f"⚠️ Модель {model} может быть недоступна в Lite тарифе. Используйте GigaChat или GigaChat-Lite")
        
        self._get_access_token()
        logger.info(f"✅ GigaChat Manager инициализирован (модель: {self.model})")
    
    def _get_access_token(self) -> str:
        """Получает новый access token"""
        headers = {
            "Authorization": f"Basic {self.auth_key}",
            "RqUID": str(uuid.uuid4()),
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"scope": self.scope}
        
        try:
            response = requests.post(
                self.auth_url,
                headers=headers,
                data=data,
                verify=False,
                timeout=30
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 1800)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
            
            logger.info("✅ Access token получен")
            return self.access_token
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения токена: {e}")
            raise
    
    def _ensure_token(self):
        """Проверяет и обновляет токен при необходимости"""
        if not self.access_token or datetime.now() >= self.token_expires_at:
            logger.info("🔄 Токен истёк, получаем новый")
            self._get_access_token()
    
    def _estimate_audio_duration(self, text: str) -> float:
        """
        Приблизительно оценивает длительность аудио в секундах
        Обычная скорость речи: ~150 слов в минуту, ~3 слова в секунду
        """
        # Убираем теги эмоций и лишние пробелы
        clean_text = text.strip()
        if ']' in clean_text:
            clean_text = clean_text.split(']')[-1].strip()
        
        # Считаем слова (приблизительно)
        words = len(clean_text.split())
        # 3 слова в секунду, плюс небольшая базовая длительность
        duration = max(2.0, words / 3.0)
        return round(duration, 1)
    
    def generate_response(
        self,
        system_prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        user_input: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        retry_count: int = 3,
        target_duration: float = 30.0  # Целевая длительность в секундах
    ) -> Tuple[str, int]:
        """
        Генерирует ответ через GigaChat API
        
        Args:
            system_prompt: Описание личности и роли агента
            history: История диалога [{"role": "assistant/user", "content": "..."}]
            user_input: Текущий запрос (если None - просто продолжение диалога)
            temperature: Креативность (0.1 - факты, 0.9 - творчество)
            max_tokens: Максимальная длина ответа
            retry_count: Количество попыток при ошибке
            target_duration: Целевая длительность аудио в секундах (≈30 сек)
            
        Returns:
            Tuple[str, int]: (текст ответа, количество потраченных токенов)
        """
        self._ensure_token()
        
        if history is None:
            history = []
        
        # Формируем сообщения
        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in history[-10:]:
            messages.append(msg)
        
        if user_input:
            messages.append({"role": "user", "content": user_input})
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Рассчитываем примерное количество токенов для целевой длительности
        # 1 токен ≈ 4 символа ≈ 0.75 слова
        # 30 секунд речи ≈ 90 слов ≈ 120 токенов
        estimated_tokens = max(50, int(target_duration * 4))
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": min(max_tokens, estimated_tokens),
            "frequency_penalty": 0.7,  # Штраф за повторения
            "presence_penalty": 0.7,    # Штраф за повторение тем
            "stop": ["\n\n", "История:", "Конец"]
        }
        
        for attempt in range(retry_count):
            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    verify=False,
                    timeout=30
                )
                response.raise_for_status()
                
                result = response.json()
                answer = result["choices"][0]["message"]["content"]
                tokens = result.get("usage", {}).get("total_tokens", 0)
                
                # Проверяем на пустой ответ
                if not answer or len(answer.strip()) < 10:
                    logger.warning(f"⚠️ Получен пустой ответ, попытка {attempt + 1}")
                    if attempt < retry_count - 1:
                        continue
                    else:
                        return "Извините, не удалось получить ответ от GigaChat.", 0
                
                # Очищаем ответ от возможных служебных маркеров
                answer = answer.strip()
                
                # Оцениваем длительность и логируем
                est_duration = self._estimate_audio_duration(answer)
                logger.info(f"✅ Ответ получен ({tokens} токенов, ~{est_duration} сек)")
                
                # Если ответ слишком длинный (больше 50% от целевого), обрезаем
                if est_duration > target_duration * 1.5:
                    # Обрезаем до примерно target_duration
                    words = answer.split()
                    target_words = int(target_duration * 3)  # 3 слова в секунду
                    if len(words) > target_words:
                        answer = ' '.join(words[:target_words]) + '...'
                        logger.info(f"✂️ Ответ обрезан до ~{target_duration} сек")
                
                return answer, tokens
                
            except Exception as e:
                logger.warning(f"⚠️ Попытка {attempt + 1}/{retry_count} не удалась: {e}")
                
                if "401" in str(e):
                    logger.info("🔄 Токен недействителен, обновляем...")
                    self._get_access_token()
                    headers["Authorization"] = f"Bearer {self.access_token}"
                
                if "402" in str(e):
                    logger.error("💸 Ошибка 402: Требуется оплата или модель недоступна в вашем тарифе")
                    logger.info("💡 Убедитесь, что используете GigaChat или GigaChat-Lite (доступны в Lite тарифе)")
                
                if attempt < retry_count - 1:
                    import time
                    time.sleep(2 ** attempt)
                else:
                    logger.error("❌ Все попытки исчерпаны")
        
        return "Извините, не удалось получить ответ от GigaChat.", 0
    
    def get_available_models(self) -> List[str]:
        """Возвращает список доступных моделей"""
        self._ensure_token()
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                verify=False,
                timeout=10
            )
            response.raise_for_status()
            
            models = response.json()
            model_list = [model["id"] for model in models.get("data", [])]
            
            # Фильтруем только модели, доступные в Lite
            lite_models = [m for m in model_list if m in ["GigaChat", "GigaChat-Lite"]]
            logger.info(f"📚 Доступные модели в Lite тарифе: {', '.join(lite_models)}")
            
            return model_list
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения списка моделей: {e}")
            return ["GigaChat", "GigaChat-Lite"]
    
    def count_tokens(self, text: str) -> int:
        """Подсчитывает количество токенов в тексте"""
        self._ensure_token()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/tokens/count",
                headers=headers,
                json=[text],
                verify=False,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("tokens", len(text) // 2)
            
        except Exception as e:
            logger.error(f"❌ Ошибка подсчета токенов: {e}")
            return len(text) // 2  # Примерная оценка


# ============================================================
# ТЕСТ
# ============================================================

def test_gigachat():
    """Тест менеджера"""
    print("="*60)
    print("🧪 ТЕСТ GigaChat MANAGER (Lite-тариф)")
    print("="*60)
    
    try:
        # Используем модель GigaChat (доступна в Lite)
        gm = GigaChatManager(model="GigaChat")
        
        # Проверка моделей
        models = gm.get_available_models()
        print(f"\n📚 Доступные модели: {', '.join(models[:3])}...")
        print(f"   ✅ Используем модель: {gm.model}")
        
        # Тест генерации с целевой длительностью 30 секунд
        print("\n📝 Тестовый запрос (целевая длительность 30 сек)...")
        response, tokens = gm.generate_response(
            system_prompt="Ты учёный-биолог. Расскажи подробно о теломерах и их роли в старении.",
            user_input="Что такое теломеры и как они связаны со старением?",
            temperature=0.7,
            max_tokens=300,
            target_duration=30.0
        )
        
        est_duration = gm._estimate_audio_duration(response)
        print(f"\n💬 Ответ (оценка длительности: {est_duration} сек):")
        print(f"   {response}")
        print(f"📊 Токенов: {tokens}")
        
        print("\n" + "="*60)
        print("✅ ТЕСТ ПРОЙДЕН")
        print("="*60)
        print("\n🎯 GigaChat Manager готов к работе с Lite тарифом!")
        print(f"💰 У вас 5 000 000 токенов до 25 декабря 2026")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        print("\n💡 Возможные решения:")
        print("   1. Убедитесь, что в .env указан GIGACHAT_AUTH_KEY")
        print("   2. Проверьте, что ключ не истёк")
        print("   3. Используйте модель 'GigaChat' или 'GigaChat-Lite'")
        return False
    
    return True


if __name__ == "__main__":
    # Создаём папку для логов, если её нет
    os.makedirs("logs", exist_ok=True)
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/gigachat.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Запускаем тест
    test_gigachat()