"""
配置数据模型
"""
from pydantic import BaseModel
from typing import List, Dict


class ServerConfig(BaseModel):
    """服务配置"""
    port: int = 12261
    host: str = "0.0.0.0"
    token: str = ""
    local_ip: str = ""
    auto_start: bool = True
    service_enabled: bool = True


class ScreenshotConfig(BaseModel):
    """截图配置"""
    default_coordinate_type: str = "grid"
    default_grid_density: float = 5.0
    default_grid_opacity: int = 50
    default_grid_color: str = "#00FF00"
    default_number_density: int = 2
    default_number_decimal: int = 0
    default_number_size: int = 8
    default_number_color: str = "#00FF00"
    default_number_opacity: int = 100
    image_quality: int = 85
    max_image_width: int = 1920


class InputConfig(BaseModel):
    """输入配置"""
    newline_mapping: Dict[str, str] = {
        "pc": "shift+enter",
        "mobile": "enter"
    }


class SecurityConfig(BaseModel):
    """安全配置"""
    blocked_processes: List[str] = []  # 禁止操作的进程
    auto_confirm_processes: List[str] = []  # 自动同意键盘鼠标操作的进程


class LogConfig(BaseModel):
    """日志配置"""
    retention_days: int = 30


class UIConfig(BaseModel):
    """界面配置"""
    language: str = "zh_CN"


class AppConfig(BaseModel):
    """应用配置"""
    server: ServerConfig = ServerConfig()
    screenshot: ScreenshotConfig = ScreenshotConfig()
    input: InputConfig = InputConfig()
    security: SecurityConfig = SecurityConfig()
    log: LogConfig = LogConfig()
    ui: UIConfig = UIConfig()
