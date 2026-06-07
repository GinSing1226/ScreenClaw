"""
响应数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# ============ 通用响应 ============

class BaseResponse(BaseModel):
    """响应基类"""
    success: bool = Field(default=True, description="是否成功")
    message: str = Field(default="Operation completed successfully", description="消息")
    error_code: Optional[str] = Field(default=None, description="错误码")
    data: Optional[Dict[str, Any]] = Field(default=None, description="响应数据")


# ============ 进程相关 ============

class ChildWindow(BaseModel):
    """子窗口信息"""
    window_id: int = Field(..., description="子窗口句柄")
    window_title: str = Field(default="", description="窗口标题")
    class_name: str = Field(default="", description="窗口类名")


class ProcessInfo(BaseModel):
    """进程信息"""
    process_id: int = Field(..., description="进程ID（保留，用于识别同一进程）")
    process_name: str = Field(..., description="进程名称")
    window_id: int = Field(..., description="主窗口句柄")
    window_title: str = Field(default="", description="窗口标题")
    child_windows: List[ChildWindow] = Field(default_factory=list, description="子窗口列表")


class GetWindowListResponse(BaseResponse):
    """获取窗口列表响应"""
    data: Optional[Dict[str, List[ProcessInfo]]] = Field(default=None, description="窗口列表")


# ============ 截图相关 ============

class ScreenshotData(BaseModel):
    """截图数据"""
    image_path: Optional[str] = Field(None, description="图片本地路径")
    image_base64: Optional[str] = Field(None, description="图片base64编码")


class ScreenshotResponse(BaseResponse):
    """截图响应"""
    data: Optional[ScreenshotData] = Field(default=None, description="截图数据")


# ============ 操作相关 ============

class OperationResponse(BaseResponse):
    """操作响应"""
    pass


# ============ 健康检查 ============

class HealthData(BaseModel):
    """健康检查数据"""
    version: str = Field(default="1.0.0", description="版本号")
    uptime_seconds: int = Field(default=0, description="运行时长(秒)")


class HealthResponse(BaseResponse):
    """健康检查响应"""
    data: Optional[HealthData] = Field(default=None, description="健康数据")


# ============ 组合指令 ============

class InstructionResult(BaseModel):
    """单条指令结果"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    data: Optional[Dict[str, Any]] = Field(default=None, description="额外数据（如截图）")


class BatchData(BaseModel):
    """组合指令数据"""
    executed_count: int = Field(..., description="已执行数量")
    failed_index: Optional[int] = Field(default=None, description="失败索引")
    results: List[InstructionResult] = Field(default_factory=list, description="结果列表")


class BatchResponse(BaseResponse):
    """组合指令响应"""
    data: Optional[BatchData] = Field(default=None, description="组合指令数据")


# ============ 滚动长截图相关 ============

class ScrollScreenshotData(BaseModel):
    """滚动长截图数据"""
    image_path: Optional[str] = Field(None, description="拼接后图片本地路径")
    image_base64: Optional[str] = Field(None, description="拼接后图片base64")
    scroll_count: int = Field(..., description="实际截图数量")
    actual_scroll_percent: float = Field(..., description="实际滚动幅度")
    fixed_header: int = Field(..., description="检测到的固定头部高度")
    fixed_footer: int = Field(..., description="检测到的固定底部高度")


class ScrollScreenshotResponse(BaseResponse):
    """滚动长截图响应"""
    data: Optional[ScrollScreenshotData] = Field(None, description="滚动长截图数据")


# ============ 错误码定义 ============

ERROR_CODES = {
    "WINDOW_NOT_FOUND": {"zh": "窗口不存在", "en": "Window not found"},
    "PROCESS_BLOCKED": {"zh": "进程在禁止清单中", "en": "Process is blocked"},
    "SCREENSHOT_FAILED": {"zh": "截图失败", "en": "Screenshot failed"},
    "OPERATION_FAILED": {"zh": "操作失败", "en": "Operation failed"},
    "USER_DENIED": {"zh": "用户拒绝操作", "en": "User denied"},
    "TIMEOUT": {"zh": "操作超时", "en": "Operation timeout"},
    "AUTH_FAILED": {"zh": "认证失败", "en": "Authentication failed"},
    "INVALID_PARAMS": {"zh": "参数无效", "en": "Invalid parameters"},
    "INTERNAL_ERROR": {"zh": "内部错误", "en": "Internal error"},
    "UNSUPPORTED_MODE": {"zh": "不支持的操作模式", "en": "Unsupported operation mode"},
}


def create_error_response(error_code: str, message: str = None) -> BaseResponse:
    """创建错误响应"""
    error_info = ERROR_CODES.get(error_code, {})
    if message is None:
        message = error_info.get("zh", "Unknown error")
    return BaseResponse(
        success=False,
        message=message,
        error_code=error_code
    )
