"""
Управление OBS Studio через WebSocket
Функции:
- set_active_speaker() — переключение яркости/размера котов
"""

import obsws_python as obs
import logging

logger = logging.getLogger(__name__)

class OBSController:
    """Контроллер для управления OBS через WebSocket"""
    
    def __init__(self, host='localhost', port=4455, password='r1lKjTNq0JtSqi69'):
        """Подключение к OBS WebSocket"""
        try:
            self.client = obs.ReqClient(
                host=host,
                port=port,
                password=password,
                timeout=3
            )
            logger.info("✅ OBS WebSocket подключён")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к OBS: {e}")
            raise
    
    def set_active_speaker(self, agent_name):
        """
        Переключает визуальное выделение между котами
        
        Args:
            agent_name: "agent_1" (чёрный кот, источник "Захват окна") 
                       или "agent_2" (белый кот, источник "Захват окна 2")
        """
        try:
            # Включаем фильтры для неактивного кота, выключаем для активного
            if agent_name == "agent_1":
                # Чёрный кот (Захват окна) активен
                self._set_filter_state("Захват окна", "Хромакей", False)
                self._set_filter_state("Захват окна 2", "Хромакей", True)
                logger.info("🎭 Активный: Захват окна (чёрный кот)")
            elif agent_name == "agent_2":
                # Белый кот (Захват окна 2) активен
                self._set_filter_state("Захват окна 2", "Хромакей", False)
                self._set_filter_state("Захват окна", "Хромакей", True)
                logger.info("🎭 Активный: Захват окна 2 (белый кот)")
            else:
                logger.warning(f"⚠️ Неизвестный агент: {agent_name}")
        except Exception as e:
            logger.error(f"❌ Ошибка переключения: {e}")
    
    def _set_filter_state(self, source_name, filter_name, enabled):
        """Включает/выключает фильтр на источнике"""
        try:
            self.client.set_source_filter_enabled(
                source_name, filter_name, enabled
            )
        except Exception as e:
            logger.error(f"❌ Фильтр {filter_name} на {source_name}: {e}")
    
    def disconnect(self):
        """Отключение от OBS"""
        try:
            self.client.disconnect()
            logger.info("🔌 OBS WebSocket отключён")
        except:
            pass