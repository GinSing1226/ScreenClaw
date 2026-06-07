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
    capture_method: str = "auto"  # "auto" | "printwindow" | "wgc"
    default_coordinate_type: str = "grid"
    default_color_mode: str = "grayscale"  # "grayscale" | "color"
    default_grid_density: float = 5.0
    default_grid_opacity: int = 50
    default_grid_color: str = "#ff0000"
    default_number_density: int = 2
    default_number_decimal: int = 1
    default_number_size: int = 12
    default_number_color: str = "#ff0000"
    default_number_opacity: int = 100
    default_number_stroke_width: int = 1
    default_number_stroke_color: str = "#ffffff"
    image_quality: int = 85
    max_image_width: int = 1920
    default_marker_ring_radius: int = 12
    default_marker_ring_line_width: int = 2
    default_marker_ring_color: str = "#FF0000"
    default_marker_dot_radius: int = 3
    default_marker_dot_color: str = "#FF0000"
    default_crop_zoom_scale: float = 2.0


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


class DelegatedConfig(BaseModel):
    """托管配置"""
    active: bool = False
    exit_hotkey: str = "ctrl+alt+z"


class ScrollScreenshotConfig(BaseModel):
    """滚动长截图配置"""
    max_scrolls: int = 5                    # 最大滚动次数
    max_scroll_wait: float = 30.0          # 最大等待时间(秒)
    max_timeout: int = 180                  # 最大超时时间(秒)
    default_scroll_percent: float = 0.85    # 默认滚动幅度
    default_scroll_wait: float = 1.0        # 默认等待时间
    max_adjust_retries: int = 4             # 自适应滚动最大调整次数
    target_overlap_min: float = 0.35        # 目标重叠下限
    target_overlap_max: float = 0.45        # 目标重叠上限
    stop_threshold: float = 0.0001          # 停止阈值
    image_quality: int = 95                 # 输出图片质量


class SelfCheckConfig(BaseModel):
    """截图轮数自检配置"""
    enabled: bool = True
    interval: int = 10
    min_chars: int = 80
    doc_path: str = "skills/screenclaw/references/self_check.md"
    keywords: List[List[str]] = [
        ["grid intersection", "do not infer coordinates"],
        ["crop zoom", "marker verification"],
        ["screenshot verification", "after operation"],
        ["网格交叉点", "不能推测坐标"],
        ["裁剪放大", "标记点验证"],
        ["截图验证", "操作后"],
    ]


class AppConfig(BaseModel):
    """应用配置"""
    server: ServerConfig = ServerConfig()
    screenshot: ScreenshotConfig = ScreenshotConfig()
    input: InputConfig = InputConfig()
    security: SecurityConfig = SecurityConfig()
    log: LogConfig = LogConfig()
    ui: UIConfig = UIConfig()
    delegated: DelegatedConfig = DelegatedConfig()
    scroll_screenshot: ScrollScreenshotConfig = ScrollScreenshotConfig()
    self_check: SelfCheckConfig = SelfCheckConfig()

    # 操作录制配置（独立导入，避免循环依赖）
    # 允许 config.json 中没有 recording 段时使用默认值
    class Config:
        extra = "allow"

    def __init__(self, **data):
        super().__init__(**data)
        # 延迟导入避免循环依赖
        from app.models.recording import RecordingConfig
        if not hasattr(self, '_recording_config'):
            self._recording_config = RecordingConfig(**data.get('recording', {}))

    @property
    def recording(self):
        if not hasattr(self, '_recording_config'):
            from app.models.recording import RecordingConfig
            self._recording_config = RecordingConfig()
        return self._recording_config
