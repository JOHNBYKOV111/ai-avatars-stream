"""Тесты конфигурационных файлов"""
import pytest
import yaml
from pathlib import Path

def test_agents_config_exists():
    """Проверка существования файла конфигурации"""
    config_path = Path("config/agents_config.yaml")
    assert config_path.exists(), "Файл конфигурации не найден"

def test_agents_config_valid_yaml():
    """Проверка валидности YAML"""
    with open("config/agents_config.yaml", 'r', encoding='utf-8') as f:
        try:
            config = yaml.safe_load(f)
            assert config is not None, "Пустой файл конфигурации"
        except yaml.YAMLError as e:
            pytest.fail(f"Невалидный YAML: {e}")

def test_agents_config_structure():
    """Проверка структуры конфигурации"""
    with open("config/agents_config.yaml", 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    assert "agents" in config
    assert "agent_1" in config["agents"]
    assert "agent_2" in config["agents"]
    assert "gender" in config["agents"]["agent_1"]
    assert "gender" in config["agents"]["agent_2"]