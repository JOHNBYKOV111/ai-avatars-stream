"""Тест наличия всех необходимых зависимостей"""
import pytest
import importlib

def test_required_packages():
    """Проверка наличия всех необходимых пакетов"""
    required_packages = [
        'yaml', 'requests', 'dotenv', 'sounddevice',
        'soundfile', 'numpy', 'scipy', 'torch', 'obsws_python'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    assert not missing_packages, f"Отсутствуют: {missing_packages}"