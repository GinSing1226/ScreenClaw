# tests/test_config_service_cache.py
"""
配置服务缓存功能单元测试
"""
import pytest
from app.services.config_service import ConfigService
import tempfile
import os
import json


@pytest.fixture
def temp_config_path():
    """Temporary config file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_path = f.name
        f.write('''{
            "server": {
                "port": 12261,
                "host": "0.0.0.0",
                "token": "test_token",
                "local_ip": "127.0.0.1"
            },
            "security": {
                "blocked_processes": ["notepad.exe", "calc.exe"]
            }
        }''')
    yield config_path
    os.unlink(config_path)


def test_is_process_blocked_cached(temp_config_path):
    """Test that process blocking uses O(1) cached lookup"""
    ConfigService._instance = None
    config_service = ConfigService(config_path=temp_config_path)

    # First call should cache the result
    assert config_service.is_process_blocked("notepad.exe") == True
    assert config_service.is_process_blocked("calc.exe") == True
    assert config_service.is_process_blocked("explorer.exe") == False

    # Case insensitive
    assert config_service.is_process_blocked("NOTEPAD.EXE") == True
    assert config_service.is_process_blocked("NoTePaD.eXe") == True

    # Cleanup
    ConfigService._instance = None


def test_config_reload_invalidates_cache(temp_config_path):
    """Test that reloading config updates the cache"""
    ConfigService._instance = None
    config_service = ConfigService(config_path=temp_config_path)

    # Initial state
    assert config_service.is_process_blocked("notepad.exe") == True
    assert config_service.is_process_blocked("explorer.exe") == False

    # Modify config file
    with open(temp_config_path, 'r') as f:
        config = json.load(f)

    config["security"]["blocked_processes"] = ["explorer.exe"]

    with open(temp_config_path, 'w') as f:
        json.dump(config, f)

    # Reload should update cache
    config_service.reload()

    assert config_service.is_process_blocked("notepad.exe") == False
    assert config_service.is_process_blocked("explorer.exe") == True

    # Cleanup
    ConfigService._instance = None


def test_multiple_config_services_isolated(temp_config_path):
    """Test that multiple config services have independent caches"""
    ConfigService._instance = None
    config1 = ConfigService(config_path=temp_config_path)

    ConfigService._instance = None
    config2 = ConfigService(config_path=temp_config_path)

    # Both should work independently
    assert config1.is_process_blocked("notepad.exe") == True
    assert config2.is_process_blocked("notepad.exe") == True

    # Cleanup
    ConfigService._instance = None


def test_cache_attribute_exists(temp_config_path):
    """Test that the cache attribute exists and is a set"""
    ConfigService._instance = None
    config_service = ConfigService(config_path=temp_config_path)

    # Verify cache exists
    assert hasattr(config_service, '_blocked_processes_cache')
    assert isinstance(config_service._blocked_processes_cache, set)

    # Verify cache is populated
    assert len(config_service._blocked_processes_cache) == 2
    assert "notepad.exe" in config_service._blocked_processes_cache
    assert "calc.exe" in config_service._blocked_processes_cache

    # Cleanup
    ConfigService._instance = None
