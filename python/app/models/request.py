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
    process_id: int = Field(..., description="进程ID")


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


class LongPressRequest(ClickRequest):
    """长按请求"""
    duration_ms: int = Field(default=500, ge=1, description="长按时长(毫秒)")


class SwipeRequest(BaseRequest):
    """滑动请求"""
    target_type: str = Field(default="pc", description="目标类型: pc/mobile")
    start_x: float = Field(..., ge=0, le=100, description="起始横坐标")
    start_y: float = Field(..., ge=0, le=100, description="起始纵坐标")
    end_x: float = Field(..., ge=0, le=100, description="结束横坐标")
    end_y: float = Field(..., ge=0, le=100, description="结束纵坐标")


class RightClickRequest(ClickRequest):
    """右键请求"""
    pass


class InputTextRequest(ClickRequest):
    """输入文本请求"""
    target_type: str = Field(default="pc", description="目标类型: pc/mobile")
    text: str = Field(..., description="输入文本")


class PressKeyRequest(BaseRequest):
    """按键请求"""
    target_type: str = Field(default="pc", description="目标类型: pc/mobile")
    key: str = Field(..., description="按键，支持组合键如Ctrl+C")


class WaitRequest(BaseRequest):
    """等待请求"""
    duration_ms: int = Field(..., ge=1, description="等待时长(毫秒)")


# ============ 进程相关 ============

class GetProcessListRequest(BaseModel):
    """获取进程列表请求"""
    ai_app_type: str = Field(..., description="AI应用类型")
    session_id: str = Field(..., description="会话ID")
    keyword: Optional[str] = Field(default="", description="搜索关键词")


# ============ 组合指令 ============

class Instruction(BaseModel):
    """单条指令"""
    action: str = Field(..., description="指令类型")
    params: Dict[str, Any] = Field(default_factory=dict, description="指令参数")


class BatchRequest(BaseRequest):
    """组合指令请求"""
    instructions: List[Instruction] = Field(..., description="指令列表")
