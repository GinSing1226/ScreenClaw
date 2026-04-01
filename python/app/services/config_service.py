"""
配置管理服务
"""
import os
import sys
import json
import secrets
import socket
from pathlib import Path
from typing import Optional

from app.models.config import AppConfig


def get_project_root() -> Path:
    """获取项目根目录

    便携包环境：exe 和 data/ 同级，返回 exe 所在目录
    开发环境：向上3级找到项目根目录
    """
    # 优先从环境变量获取（开发模式）
    if os.environ.get('SCREENCLAW_ROOT'):
        return Path(os.environ['SCREENCLAW_ROOT'])

    if getattr(sys, 'frozen', False):
        # 打包后的exe
        exe_dir = Path(sys.executable).parent

        # 检查 exe 同级目录是否有 data/config.json（便携包环境）
        data_in_exe_dir = exe_dir / "data" / "config.json"
        if data_in_exe_dir.exists():
            return exe_dir

        # 开发环境：exe 在 src-tauri/target/debug/ 或 release/ 目录下
        # 项目根目录是 exe 的父目录的父目录的父目录
        return exe_dir.parent.parent.parent
    else:
        # 开发模式：python/main.py 所在目录的父目录
        return Path(__file__).parent.parent.parent.parent


def get_data_dir() -> Path:
    """获取data目录路径"""
    return get_project_root() / "data"


class ConfigService:
    """配置服务"""

    _instance: Optional['ConfigService'] = None

    def __new__(cls, config_path: str = None):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: str = None):
        if self._initialized:
            return
        self._initialized = True

        # 如果未指定路径，使用data目录
        if config_path is None:
            data_dir = get_data_dir()
            self.config_path = str(data_dir / "config.json")
        else:
            self.config_path = config_path

        # 初始化缓存
        self._blocked_processes_cache: set = set()

        self.config: AppConfig = self._load_or_create()

    def _load_or_create(self) -> AppConfig:
        """加载或创建配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                config = AppConfig(**data)
                # 确保host不为空
                if not config.server.host:
                    config.server.host = "0.0.0.0"
                # 构建缓存
                self._build_cache(config)
                return config
            except Exception as e:
                print(f"加载配置失败: {e}，使用默认配置")

        # 确保data目录存在
        data_dir = os.path.dirname(self.config_path)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)

        # 创建默认配置
        config = AppConfig()
        config.server.token = self._generate_token()
        config.server.local_ip = self._get_local_ip()
        self._save(config)
        # 构建缓存
        self._build_cache(config)
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

    def _build_cache(self, config: AppConfig):
        """构建缓存：将阻止进程列表转换为小写集合，实现O(1)查找"""
        self._blocked_processes_cache = {p.lower() for p in config.security.blocked_processes}

    def save(self):
        """保存当前配置"""
        self._save(self.config)
        # 保存配置后需要重建缓存
        self._build_cache(self.config)

    def reload(self):
        """重新加载配置"""
        self.config = self._load_or_create()
        # 重新加载配置后需要重建缓存
        self._build_cache(self.config)

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
        return process_name.lower() in self._blocked_processes_cache

    def verify_token(self, token: str) -> bool:
        """验证Token"""
        return token == self.config.server.token

    def regenerate_token(self) -> str:
        """重新生成Token"""
        new_token = self._generate_token()
        self.config.server.token = new_token
        self.save()
        return new_token


# 全局配置服务实例
config_service = ConfigService()
