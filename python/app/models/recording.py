"""
操作录制数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from enum import Enum


# ---- 配置模型 ----

class RecordingConfig(BaseModel):
    """录制功能配置"""
    hotkey: str = "ctrl+alt+\\"
    scroll_merge_interval_ms: int = Field(default=1000, ge=100, le=5000)


# ---- Hook 原始事件 ----

class HookEventType(str, Enum):
    """Hook 原始事件类型"""
    MOUSE_MOVE = "mouse_move"
    LBUTTONDOWN = "lbutton_down"
    LBUTTONUP = "lbutton_up"
    RBUTTONDOWN = "rbutton_down"
    RBUTTONUP = "rbutton_up"
    MOUSEWHEEL = "mouse_wheel"
    KEYDOWN = "key_down"
    KEYUP = "key_up"
    CHAR = "char"
    IME_CHAR = "ime_char"


class RawHookEvent:
    """Hook 原始事件（不使用 Pydantic，避免回调中序列化开销）"""

    __slots__ = (
        'event_type', 'screen_x', 'screen_y',
        'vk_code', 'scan_code', 'delta', 'char_code',
        'timestamp_us', 'flags',
    )

    def __init__(
        self,
        event_type: HookEventType,
        screen_x: int = 0,
        screen_y: int = 0,
        vk_code: int = 0,
        scan_code: int = 0,
        delta: int = 0,
        char_code: int = 0,
        timestamp_us: int = 0,
        flags: int = 0,
    ):
        self.event_type = event_type
        self.screen_x = screen_x
        self.screen_y = screen_y
        self.vk_code = vk_code
        self.scan_code = scan_code
        self.delta = delta
        self.char_code = char_code
        self.timestamp_us = timestamp_us
        self.flags = flags


# ---- 录制步骤模型 ----

class StepProcessInfo(BaseModel):
    """步骤中的进程/窗口信息"""
    process_id: int
    process_name: str
    window_id: int
    window_title: str = ""
    main_window_id: int
    main_window_title: str = ""


class RecordStep:
    """单步录制记录（内部使用，不直接序列化）"""

    __slots__ = (
        'step_index', 'timestamp', 'action',
        'process', 'target_process', 'params', 'screenshot', 'window_info',
        '_image', '_start_image', '_end_image',
    )

    def __init__(
        self,
        action: str,
        params: Dict[str, Any],
        process: Optional[Dict] = None,
        target_process: Optional[Dict] = None,
    ):
        self.step_index: int = 0
        self.timestamp: str = ""
        self.action = action
        self.process = process
        self.target_process = target_process
        self.params = params
        self.screenshot: Optional[Union[str, Dict[str, str]]] = None
        self.window_info: Optional[Dict] = None  # {source_width, source_height, scale_factor}
        # 瞬态字段：截图 PIL Image，不序列化
        self._image: Any = None
        self._start_image: Any = None  # drag/swipe 起点截图
        self._end_image: Any = None    # drag/swipe 终点截图

    def to_dict(self) -> Dict[str, Any]:
        """序列化为 step.json 中的步骤字典"""
        d: Dict[str, Any] = {
            "step_index": self.step_index,
            "timestamp": self.timestamp,
            "action": self.action,
            "process": self.process,
            "params": self.params,
            "screenshot": self.screenshot,
        }
        if self.target_process is not None:
            d["target_process"] = self.target_process
        if self.window_info is not None:
            d["window_info"] = self.window_info
        return d


class RecordingMeta(BaseModel):
    """step.json 根结构"""
    start_time: str
    end_time: Optional[str] = None
    duration_ms: int = 0
    total_steps: int = 0
    hotkey: str = ""
    steps: List[Dict[str, Any]] = []


# ---- API 请求/响应模型 ----

class RecordingStartRequest(BaseModel):
    """录制开始请求"""
    pass


class RecordingStatusResponse(BaseModel):
    """录制状态响应"""
    is_recording: bool
    duration_ms: int = 0
    step_count: int = 0
