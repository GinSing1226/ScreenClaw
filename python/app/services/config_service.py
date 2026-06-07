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

        # 托管状态缓存（避免高频文件 I/O）
        self._delegated_cache: dict = {"active": False, "ts": 0.0}
        self._delegated_cache_ttl: float = 1.0  # 秒

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
        """获取配置（每次重新加载以获取最新值）"""
        self.config = self._load_or_create()
        self._build_cache(self.config)
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

    def is_delegated_active(self) -> bool:
        """检查托管模式是否激活（TTL 缓存，默认 1 秒）"""
        import time as _time
        now = _time.time()
        if now - self._delegated_cache["ts"] < self._delegated_cache_ttl:
            return self._delegated_cache["active"]
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            active = data.get("delegated", {}).get("active", False)
            self._delegated_cache["active"] = active
            self._delegated_cache["ts"] = now
            return active
        except Exception:
            return False

    def update_delegated(self, active: bool):
        """更新托管状态（原子写入，确保与Rust侧同步）"""
        import time as _time
        import tempfile
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {}

        if "delegated" not in data:
            data["delegated"] = {"active": False, "exit_hotkey": "ctrl+alt+z"}
        data["delegated"]["active"] = active

        # 原子写入：先写临时文件，再 rename
        dir_name = os.path.dirname(self.config_path)
        try:
            with tempfile.NamedTemporaryFile(
                'w', dir=dir_name, suffix='.tmp',
                encoding='utf-8', delete=False
            ) as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                tmp_path = f.name
            os.replace(tmp_path, self.config_path)
        except Exception:
            # 回退：直接写入
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        # 同步更新内存缓存
        self.config.delegated.active = active
        self._delegated_cache["active"] = active
        self._delegated_cache["ts"] = _time.time()

        # 通知 Rust (Tauri) 托管状态已变更
        self._notify_rust_delegated_changed()

    def _notify_rust_delegated_changed(self):
        """通过 PostThreadMessageW 通知 Rust 热键线程托管状态变更"""
        try:
            import ctypes
            user32 = ctypes.windll.user32

            # 读取热键线程 ID
            tid_path = os.path.join(os.path.dirname(self.config_path), ".hotkey_tid")
            if not os.path.exists(tid_path):
                return
            with open(tid_path, 'r') as f:
                tid = int(f.read().strip())
            if tid == 0:
                return

            # WM_DELEGATED_SYNC = WM_USER + 2 = 0x0402
            user32.PostThreadMessageW(tid, 0x0402, 0, 0)
        except Exception:
            pass


# 全局配置服务实例
config_service = ConfigService()
