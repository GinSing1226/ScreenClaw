"""
请求数据模型
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any


# ============ 通用字段 ============

class BaseRequest(BaseModel):
    """请求基类"""
    ai_app_type: str = Field(..., description="AI应用类型")
    session_id: str = Field(..., description="会话ID")
    window_id: int = Field(..., description="窗口句柄")
    main_window_id: Optional[int] = Field(default=None, description="主窗口ID（可选，用于恢复最小化/隐藏的窗口）")


# ============ 截图相关 ============

class GridParams(BaseModel):
    """网格参数"""
    density: float = Field(default=5.0, ge=0, le=100, description="网格密度")
    opacity: int = Field(default=50, ge=0, le=100, description="网格透明度")
    color: str = Field(default="#ff0000", description="网格颜色")


class CoordinateParams(BaseModel):
    """坐标参数"""
    number_density: int = Field(default=2, ge=1, description="数字密度")
    number_decimal: int = Field(default=0, ge=0, le=4, description="小数位")
    number_size: int = Field(default=12, ge=4, le=64, description="字体大小")
    number_color: str = Field(default="#ff0000", description="数字颜色")
    number_opacity: int = Field(default=100, ge=0, le=100, description="数字透明度")


class ScreenshotRequest(BaseRequest):
    """截图请求"""
    coordinate_type: str = Field(default="grid", description="坐标类型: no/grid")
    color_mode: str = Field(default=None, description="颜色模式: grayscale(灰度)/color(原色)")
    grid: Optional[GridParams] = Field(default=None, description="网格参数")
    coordinate: Optional[CoordinateParams] = Field(default=None, description="坐标参数")


# ============ 操作相关 ============

class ClickRequest(BaseRequest):
    """点击请求"""
    x: float = Field(..., ge=0, le=100, description="横坐标(0-100)")
    y: float = Field(..., ge=0, le=100, description="纵坐标(0-100)")
    action_method: str = Field(
        default="background",
        description="操作方式: background(无感,不抢鼠标) / hijack(劫持,短暂接管,需确认)"
    )


class LongPressRequest(ClickRequest):
    """长按请求"""
    duration_ms: int = Field(default=500, ge=1, description="长按时长(毫秒)")


class SwipeRequest(BaseRequest):
    """滑动请求"""
    start_x: float = Field(..., ge=0, le=100, description="起始横坐标")
    start_y: float = Field(..., ge=0, le=100, description="起始纵坐标")
    end_x: float = Field(..., ge=0, le=100, description="结束横坐标")
    end_y: float = Field(..., ge=0, le=100, description="结束纵坐标")
    action_method: str = Field(
        default="background",
        description="操作方式: background(无感) / hijack(劫持,需确认)"
    )


class DragRequest(BaseRequest):
    """拖拽请求"""
    start_x: float = Field(..., ge=0, le=100, description="起始横坐标")
    start_y: float = Field(..., ge=0, le=100, description="起始纵坐标")
    end_x: float = Field(..., ge=0, le=100, description="结束横坐标")
    end_y: float = Field(..., ge=0, le=100, description="结束纵坐标")
    duration_ms: int = Field(default=500, ge=50, description="拖拽时长(毫秒)，控制移动速度")
    action_method: str = Field(
        default="background",
        description="操作方式: background(无感) / hijack(劫持,需确认)"
    )


class MouseMoveRequest(BaseRequest):
    """鼠标移动请求 - 相对位移，用于游戏视角控制"""
    delta_x: int = Field(..., description="水平相对位移(像素)，正值向右，负值向左")
    delta_y: int = Field(..., description="垂直相对位移(像素)，正值向下，负值向上")
    duration_ms: int = Field(default=300, ge=50, description="移动时长(毫秒)，控制移动速度")
    action_method: str = Field(
        default="hijack",
        description="操作方式: hijack(劫持,需确认) — 不支持background模式"
    )


class ScrollRequest(BaseRequest):
    """滚动请求"""
    x: float = Field(..., ge=0, le=100, description="滚动位置横坐标(0-100)")
    y: float = Field(..., ge=0, le=100, description="滚动位置纵坐标(0-100)")
    delta: int = Field(..., description="滚动量(正值向上,负值向下)")
    action_method: str = Field(
        default="background",
        description="操作方式: background(无感,PostMessage) / hijack(劫持,需确认)"
    )


class RightClickRequest(ClickRequest):
    """右键请求"""
    pass


class HoverRequest(ClickRequest):
    """鼠标悬浮请求（移动鼠标到目标位置并停留）"""
    duration_ms: int = Field(default=500, ge=0, description="停留时长(毫秒)，默认500ms")


class InputTextRequest(BaseRequest):
    """输入文本请求"""
    x: Optional[float] = Field(default=None, ge=0, le=100, description="可选，输入位置横坐标(0-100)")
    y: Optional[float] = Field(default=None, ge=0, le=100, description="可选，输入位置纵坐标(0-100)")
    text: str = Field(..., description="输入文本，\\n表示换行")
    newline_key: str = Field(default="shift enter", description="换行键，默认 shift enter（可选：ctrl enter, enter 等）")
    action_method: str = Field(
        default="background",
        description="操作方式: background(无感,SendMessage WM_CHAR) / hijack(劫持,剪贴板+Ctrl+V,需确认)"
    )


class PressKeyRequest(BaseRequest):
    """按键请求"""
    key: str = Field(..., description="按键，空格分隔组合键如 ctrl c（不用+号）")
    x: Optional[float] = Field(default=None, ge=0, le=100, description="可选，先点击此横坐标再按键")
    y: Optional[float] = Field(default=None, ge=0, le=100, description="可选，先点击此纵坐标再按键")
    duration_ms: int = Field(default=0, ge=0, description="按住时长(毫秒)，0=立即释放")
    action_method: str = Field(
        default="background",
        description="操作方式: background(无感,混合方案) / hijack(劫持,闪电劫持,需确认)"
    )


class WaitRequest(BaseModel):
    """等待请求"""
    ai_app_type: str = Field(..., description="AI应用类型")
    session_id: str = Field(..., description="会话ID")
    window_id: Optional[int] = Field(default=None, description="窗口句柄（可选）")
    main_window_id: Optional[int] = Field(default=None, description="主窗口ID（可选）")
    duration_ms: int = Field(..., ge=1, description="等待时长(毫秒)")


# ============ 窗口相关 ============

class GetWindowListRequest(BaseModel):
    """获取窗口列表请求"""
    ai_app_type: str = Field(..., description="AI应用类型")
    session_id: str = Field(..., description="会话ID")
    keyword: Optional[str] = Field(default="", description="搜索关键词")
    include_children: bool = Field(default=False, description="是否返回子窗口")
    children_filter: str = Field(default="titled", description="子窗口过滤策略: all(全部) / titled(仅标题非空)")


# ============ 组合指令 ============

class Instruction(BaseModel):
    """单条指令"""
    action: str = Field(..., description="指令类型")
    params: Dict[str, Any] = Field(default_factory=dict, description="指令参数")


class BatchRequest(BaseRequest):
    """组合指令请求"""
    instructions: List[Instruction] = Field(..., description="指令列表")


# ============ 托管模式 ============

class DelegatedRequest(BaseModel):
    """托管模式请求"""
    action: str = Field(..., description="enter: 进入托管 / exit: 退出托管 / status: 查询状态")


# ============ 滚动长截图相关 ============

class ScrollScreenshotRequest(BaseRequest):
    """滚动长截图请求"""
    # 操作模式（固定为 hijack，用于触发确认弹窗）
    action_method: str = Field(default="hijack", description="操作方式（固定hijack）")

    # 基础参数（默认 None，由服务端从 config.json 填充）
    max_scrolls: Optional[int] = Field(default=None, ge=1, le=100, description="最大滚动次数")
    scroll_percent: Optional[float] = Field(default=None, ge=0.1, le=0.95, description="初始滚动幅度")
    scroll_wait: Optional[float] = Field(default=None, ge=0.1, le=60.0, description="滚动等待时间(秒)")

    # 滚动位置（百分比坐标，默认中心点 50,50）
    x: Optional[float] = Field(default=50, ge=0, le=100, description="滚动位置横坐标(0-100)")
    y: Optional[float] = Field(default=50, ge=0, le=100, description="滚动位置纵坐标(0-100)")

    # 高级参数（默认 None，由服务端从 config.json 填充）
    max_adjust_retries: Optional[int] = Field(
        default=None, ge=0, le=10,
        description="自适应滚动最大调整次数"
    )
    target_overlap_min: Optional[float] = Field(
        default=None, ge=0.10, le=0.50,
        description="目标重叠下限(用于自适应调整)"
    )
    target_overlap_max: Optional[float] = Field(
        default=None, ge=0.20, le=0.60,
        description="目标重叠上限(用于自适应调整)"
    )
    stop_threshold: Optional[float] = Field(
        default=None, ge=0.0, le=0.01,
        description="停止阈值: 内容变化率低于此值时停止"
    )

    @model_validator(mode='after')
    def enforce_hijack_mode(self):
        """强制 action_method 为 hijack"""
        if self.action_method != "hijack":
            object.__setattr__(self, 'action_method', 'hijack')
        return self
