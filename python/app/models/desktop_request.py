"""
桌面级操作请求数据模型

与窗口级操作并列，绑定 monitor_index 而非 window_id。
所有操作固定 hijack 模式，不提供 action_method 参数。
"""
from pydantic import BaseModel, Field, model_validator, field_validator
from typing import Optional, List, Union


# ============ 公共基类 ============

class DesktopBaseRequest(BaseModel):
    """桌面操作请求基类"""
    ai_app_type: str = Field(..., description="AI应用类型")
    session_id: str = Field(..., description="会话ID")
    monitor_index: int = Field(..., ge=0, description="目标显示器索引（从 0 开始）")


# ============ 截图 ============

class DesktopScreenshotRequest(DesktopBaseRequest):
    """桌面截图请求"""
    coordinate_type: str = Field(default="grid", description="坐标类型: no/grid")
    color_mode: Optional[str] = Field(default=None, description="颜色模式: grayscale/color")
    grid: Optional["GridParams"] = Field(default=None, description="网格参数")
    coordinate: Optional["CoordinateParams"] = Field(default=None, description="坐标参数")
    marker: Optional[Union["MarkerParams", List["MarkerParams"]]] = Field(default=None, description="标记参数")
    self_check: Optional[str] = Field(default=None, description="轮数自检内容")

    @field_validator('marker', mode='before')
    @classmethod
    def normalize_marker(cls, v):
        if v is None:
            return None
        if isinstance(v, list):
            return v
        return [v]


# ============ 复用网格/坐标/标记参数 ============

class GridParams(BaseModel):
    """网格参数"""
    density_x: float = Field(default=5.0, ge=0.1, le=100, description="水平网格密度百分比")
    density_y: float = Field(default=5.0, ge=0.1, le=100, description="垂直网格密度百分比")
    opacity: int = Field(default=50, ge=0, le=100, description="网格透明度")
    color: str = Field(default="#ff0000", description="网格颜色")


class CoordinateParams(BaseModel):
    """坐标参数"""
    number_density: int = Field(default=2, ge=1, description="数字密度")
    number_decimal: int = Field(default=1, ge=0, le=4, description="小数位")
    number_size: int = Field(default=12, ge=4, le=64, description="字体大小")
    number_color: str = Field(default="#ff0000", description="数字颜色")
    number_opacity: int = Field(default=100, ge=0, le=100, description="数字透明度")
    number_stroke_width: int = Field(default=1, ge=0, le=8, description="数字描边宽度")
    number_stroke_color: str = Field(default="#ffffff", description="数字描边颜色")


class MarkerParams(BaseModel):
    """标记参数"""
    x: float = Field(..., ge=0, le=100, description="标记点横坐标百分比")
    y: float = Field(..., ge=0, le=100, description="标记点纵坐标百分比")
    ring_radius: int = Field(default=12, ge=4, le=64, description="外圈半径")
    ring_line_width: int = Field(default=2, ge=1, le=8, description="外圈线宽")
    ring_color: str = Field(default="#FF0000", description="外圈颜色")
    dot_radius: int = Field(default=3, ge=1, le=16, description="中心圆半径")
    dot_color: str = Field(default="#FF0000", description="中心圆颜色")


# ============ 操作 ============

class DesktopClickRequest(DesktopBaseRequest):
    """桌面点击请求"""
    x: float = Field(..., ge=0, le=100, description="横坐标百分比(0-100)")
    y: float = Field(..., ge=0, le=100, description="纵坐标百分比(0-100)")


class DesktopDoubleClickRequest(DesktopBaseRequest):
    """桌面双击请求"""
    x: float = Field(..., ge=0, le=100, description="横坐标百分比(0-100)")
    y: float = Field(..., ge=0, le=100, description="纵坐标百分比(0-100)")


class DesktopRightClickRequest(DesktopBaseRequest):
    """桌面右键请求"""
    x: float = Field(..., ge=0, le=100, description="横坐标百分比(0-100)")
    y: float = Field(..., ge=0, le=100, description="纵坐标百分比(0-100)")


class DesktopDragRequest(DesktopBaseRequest):
    """桌面拖拽请求"""
    start_x: float = Field(..., ge=0, le=100, description="起点横坐标")
    start_y: float = Field(..., ge=0, le=100, description="起点纵坐标")
    end_monitor_index: int = Field(..., ge=0, description="终点显示器索引")
    end_x: float = Field(..., ge=0, le=100, description="终点横坐标")
    end_y: float = Field(..., ge=0, le=100, description="终点纵坐标")
    duration_ms: int = Field(default=500, ge=50, description="拖拽时长(ms)")


class DesktopScrollRequest(DesktopBaseRequest):
    """桌面滚动请求"""
    x: float = Field(..., ge=0, le=100, description="位置横坐标")
    y: float = Field(..., ge=0, le=100, description="位置纵坐标")
    delta: int = Field(..., description="滚动量(正值向上,负值向下)")


class DesktopInputTextRequest(DesktopBaseRequest):
    """桌面文本输入请求"""
    x: float = Field(..., ge=0, le=100, description="输入位置横坐标")
    y: float = Field(..., ge=0, le=100, description="输入位置纵坐标")
    text: str = Field(..., description="输入文本")


class DesktopPressKeyRequest(DesktopBaseRequest):
    """桌面按键请求"""
    keys: str = Field(..., description="按键组合，空格分隔")
    x: Optional[float] = Field(default=None, ge=0, le=100, description="横坐标百分比(0-100)，传值则先点击定位再按键")
    y: Optional[float] = Field(default=None, ge=0, le=100, description="纵坐标百分比(0-100)，传值则先点击定位再按键")
    duration_ms: int = Field(default=0, ge=0, description="按住时长(ms)")

    @model_validator(mode='after')
    def validate_xy_pair(self):
        """x 和 y 必须同时传或同时不传"""
        if (self.x is None) != (self.y is None):
            raise ValueError('x and y must be provided together or both omitted')
        return self


class DesktopHoverRequest(DesktopBaseRequest):
    """桌面悬浮请求"""
    x: float = Field(..., ge=0, le=100, description="横坐标百分比")
    y: float = Field(..., ge=0, le=100, description="纵坐标百分比")
    duration_ms: int = Field(default=1000, ge=0, description="悬浮时长(ms)")
