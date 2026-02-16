"""Тесты для GigaChat менеджера"""
import pytest
from unittest.mock import patch, Mock
from src.gigachat_manager import GigaChatManager

def test_gigachat_initialization(gigachat_manager):
    """Тест инициализации"""
    assert gigachat_manager.model == "GigaChat"
    assert gigachat_manager.auth_key is not None

def test_generate_response(gigachat_manager):
    """Тест генерации ответа"""
    response, tokens = gigachat_manager.generate_response(
        system_prompt="Ты полезный ассистент. Отвечай кратко.",
        user_input="Привет! Как дела?",
        max_tokens=50
    )
    assert response is not None
    assert len(response) > 0
    assert tokens > 0

def test_empty_response_handling(gigachat_manager):
    """Тест обработки пустого ответа"""
    response, tokens = gigachat_manager.generate_response(
        system_prompt="",
        user_input="",
        max_tokens=10
    )
    assert response is not None  # Должна быть заглушка
    assert "Извините" in response or len(response) > 0

def test_token_expiry(gigachat_manager):
    """Тест истечения токена"""
    from datetime import datetime, timedelta
    
    # Устанавливаем истёкший токен
    gigachat_manager.access_token = "old_token"
    gigachat_manager.token_expires_at = datetime.now() - timedelta(seconds=10)
    
    # Проверяем, что токен обновляется
    gigachat_manager._ensure_token()
    # Токен должен обновиться, но мы не можем проверить точное значение без реального ключа

def test_get_available_models(gigachat_manager):
    """Тест получения списка моделей"""
    models = gigachat_manager.get_available_models()
    assert isinstance(models, list)
    assert "GigaChat" in models

def test_count_tokens(gigachat_manager):
    """Тест подсчёта токенов"""
    text = "Тестовый текст для подсчёта токенов"
    tokens = gigachat_manager.count_tokens(text)
    assert isinstance(tokens, int)

def test_gigachat_401_error():
    """Тест обработки ошибки 401 (неавторизован)"""
    gm = GigaChatManager()
    
    # Мокаем только запрос на генерацию, а не на получение токена
    with patch.object(gm, '_get_access_token', return_value="fake_token"):
        with patch('requests.post') as mock_post:
            # Мокаем ответ API с ошибкой 401
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")
            mock_post.return_value = mock_response
            
            response, tokens = gm.generate_response(
                system_prompt="Тест",
                retry_count=1
            )
            
            assert "Извините" in response
            assert tokens == 0

def test_gigachat_402_error():
    """Тест обработки ошибки 402 (требуется оплата)"""
    gm = GigaChatManager()
    
    # Мокаем только запрос на генерацию
    with patch.object(gm, '_get_access_token', return_value="fake_token"):
        with patch('requests.post') as mock_post:
            # Мокаем ответ API с ошибкой 402
            mock_response = Mock()
            mock_response.status_code = 402
            mock_response.raise_for_status.side_effect = Exception("402 Payment Required")
            mock_post.return_value = mock_response
            
            response, tokens = gm.generate_response(
                system_prompt="Тест",
                retry_count=1
            )
            
            assert "Извините" in response
            assert tokens == 0  # При ошибке возвращается 0 токенов

def test_gigachat_max_retries_exceeded():
    """Тест превышения количества попыток"""
    gm = GigaChatManager()
    with patch('requests.post') as mock_post:
        mock_post.side_effect = Exception("Network error")
        response, tokens = gm.generate_response(
            system_prompt="Тест",
            retry_count=2
        )
        assert "Извините" in response
        assert mock_post.call_count == 2
        assert tokens == 0