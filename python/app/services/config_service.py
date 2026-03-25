"""
配置管理服务
"""
import os
import json
import secrets
import socket
from pathlib import Path
from typing import Optional

from app.models.config import AppConfig


class ConfigService:
    """配置服务"""

    _instance: Optional['ConfigService'] = None

    def __new__(cls, config_path: str = "config.json"):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: str = "config.json"):
        if self._initialized:
            return
        self._initialized = True
        self.config_path = config_path
        self.config: AppConfig = self._load_or_create()

    def _load_or_create(self) -> AppConfig:
        """加载或创建配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return AppConfig(**data)
            except Exception as e:
                print(f"加载配置失败: {e}，使用默认配置")

        # 创建默认配置
        config = AppConfig()
        config.server.token = self._generate_token()
        config.server.local_ip = self._get_local_ip()
        self._save(config)
        return config

    def _generate_token(self) -> str:
        """生成随机Token"""
        return secrets.token_hex(16)

    def _get_local_ip(self) -> str:
        """获取本机局域网IP"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _save(self, config: AppConfig):
        """保存配置到文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)

    def save(self):
        """保存当前配置"""
        self._save(self.config)

    def reload(self):
        """重新加载配置"""
        self.config = self._load_or_create()

    def get(self) -> AppConfig:
        """获取配置"""
        return self.config

    def update_local_ip(self):
        """更新本机IP"""
        self.config.server.local_ip = self._get_local_ip()
        self.save()

    def update_port(self, port: int):
        """更新端口"""
        self.config.server.port = port
        self.save()

    def is_process_blocked(self, process_name: str) -> bool:
        """检查进程是否在禁止清单中"""
        return process_name.lower() in [p.lower() for p in self.config.security.blocked_processes]

    def verify_token(self, token: str) -> bool:
        """验证Token"""
        return token == self.config.server.token


# 全局配置服务实例
config_service = ConfigService()
