"""
请求数据模型
"""
from pydantic import BaseModel, Field
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
    color: str = Field(default="#00FF00", description="网格颜色")


class CoordinateParams(BaseModel):
    """坐标参数"""
    number_density: int = Field(default=2, ge=1, description="数字密度")
    number_decimal: int = Field(default=0, ge=0, le=4, description="小数位")
    number_size: int = Field(default=8, ge=4, le=32, description="字体大小")
    number_color: str = Field(default="#00FF00", description="数字颜色")
    number_opacity: int = Field(default=100, ge=0, le=100, description="数字透明度")


class ScreenshotRequest(BaseRequest):
    """截图请求"""
    coordinate_type: str = Field(default="grid", description="坐标类型: no/grid")
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


class WaitRequest(BaseRequest):
    """等待请求"""
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
