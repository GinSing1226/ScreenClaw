"""
配置服务单元测试
"""
import pytest
import os
import json
import tempfile
from app.services.config_service import ConfigService
from app.models.config import AppConfig


class TestConfigService:
    """配置服务测试"""

    def test_create_default_config(self, tmp_path):
        """测试创建默认配置"""
        config_path = os.path.join(tmp_path, "new_test_config.json")

        # 确保使用新的ConfigService实例（重置单例）
        ConfigService._instance = None
        service = ConfigService(config_path)

        # 验证配置内容
        config = service.get()
        assert config.server.host == "0.0.0.0"
        # Token应该自动生成
        assert len(config.server.token) == 32  # 16字节hex
        assert config.server.local_ip != ""
        assert config.server.port == 12261  # 默认端口

        # 验证配置文件被创建
        assert os.path.exists(config_path)

        # 清理单例
        ConfigService._instance = None

    def test_save_and_reload(self, tmp_path):
        """测试保存和重新加载配置"""
        config_path = os.path.join(tmp_path, "test_config.json")
        service = ConfigService(config_path)

        # 修改配置
        service.config.server.port = 8080
        service.save()

        # 重新加载
        service.reload()
        assert service.config.server.port == 8080

    def test_is_process_blocked(self, tmp_path):
        """测试进程禁止检查"""
        config_path = os.path.join(tmp_path, "test_config.json")
        service = ConfigService(config_path)

        # 添加禁止进程
        service.config.security.blocked_processes = ["notepad.exe", "calc.exe"]
        service.save()

        # 测试
        assert service.is_process_blocked("notepad.exe") == True
        assert service.is_process_blocked("NOTEPAD.EXE") == True  # 大小写不敏感
        assert service.is_process_blocked("explorer.exe") == False

    def test_verify_token(self, tmp_path):
        """测试Token验证"""
        config_path = os.path.join(tmp_path, "test_config.json")
        service = ConfigService(config_path)

        token = service.config.server.token
        assert service.verify_token(token) == True
        assert service.verify_token("wrong_token") == False

    def test_update_local_ip(self, tmp_path):
        """测试更新本机IP"""
        config_path = os.path.join(tmp_path, "test_config.json")
        service = ConfigService(config_path)

        service.update_local_ip()
        assert service.config.server.local_ip != ""
        # 应该不是默认的127.0.0.1（除非真的没有网络）

    def test_update_port(self, tmp_path):
        """测试更新端口"""
        config_path = os.path.join(tmp_path, "test_config.json")
        service = ConfigService(config_path)

        # 更新端口
        service.update_port(9999)
        assert service.config.server.port == 9999

        # 重新加载验证持久化
        service.reload()
        assert service.config.server.port == 9999

    def test_regenerate_token(self, tmp_path):
        """测试重新生成Token"""
        config_path = os.path.join(tmp_path, "test_config.json")
        service = ConfigService(config_path)

        old_token = service.config.server.token

        # 重新生成
        new_token = service.regenerate_token()
        assert new_token != old_token
        assert service.config.server.token == new_token

        # 验证新Token有效
        assert service.verify_token(new_token) == True
        assert service.verify_token(old_token) == False
