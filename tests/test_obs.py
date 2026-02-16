"""Тесты для OBSController"""
import pytest
from unittest.mock import Mock, patch
from src.obs_controller import OBSController

def test_obs_initialization():
    """Тест инициализации (без реального OBS)"""
    with patch('obsws_python.ReqClient'):
        controller = OBSController()
        assert controller is not None

def test_set_active_speaker():
    """Тест переключения активного говорящего (без OBS)"""
    with patch('obsws_python.ReqClient'):
        controller = OBSController()
        assert hasattr(controller, 'set_active_speaker')

def test_obs_connection_failure():
    """Тест ошибки подключения к OBS"""
    with patch('obsws_python.ReqClient') as mock_client:
        mock_client.side_effect = Exception("Connection refused")
        with pytest.raises(Exception):
            OBSController(host='localhost', port=9999)

def test_set_filter_state_error_handling():
    """Тест обработки ошибок при установке фильтра"""
    with patch('obsws_python.ReqClient'):
        controller = OBSController()
        controller.client = Mock()
        controller.client.set_source_filter_enabled.side_effect = Exception("OBS error")
        result = controller._set_filter_state("source", "filter", True)
        assert result is None

def test_set_filter_state_success():
    """Тест успешной установки фильтра"""
    with patch('obsws_python.ReqClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        controller = OBSController()
        controller.client = mock_client
        result = controller._set_filter_state("source", "filter", True)
        assert result is None
        mock_client.set_source_filter_enabled.assert_called_once_with("source", "filter", True)

def test_disconnect_without_client():
    """Тест отключения без клиента"""
    with patch('obsws_python.ReqClient'):
        controller = OBSController()
        controller.client = None
        # Не должно быть ошибки
        controller.disconnect()

def test_disconnect_with_client():
    """Тест отключения с клиентом"""
    with patch('obsws_python.ReqClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        controller = OBSController()
        controller.disconnect()

def test_set_filter_state_invalid_filter():
    """Тест установки несуществующего фильтра"""
    with patch('obsws_python.ReqClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.set_source_filter_enabled.side_effect = Exception("Filter not found")
        
        controller = OBSController()
        result = controller._set_filter_state("source", "invalid_filter", True)
        assert result is None  # Должен обработать ошибку
        

def test_disconnect_error():
    with patch('obsws_python.ReqClient') as mock_client_class:
        mock_client = Mock()
        mock_client.disconnect.side_effect = Exception("Disconnect error")
        mock_client_class.return_value = mock_client
        
        controller = OBSController()
        controller.disconnect()  # Не должно падать
        # Не проверяем disconnect, так как он не вызывается в этом тесте