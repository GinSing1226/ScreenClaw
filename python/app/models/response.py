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
    window_info: Optional[Dict[str, Any]] = Field(None, description="窗口原始信息（source_width/source_height/scale_factor）")
    requested_params: Optional[Dict[str, Any]] = Field(None, description="请求参数摘要")
    effective_params: Optional[Dict[str, Any]] = Field(None, description="实际生效完整参数")
    effective_grid: Optional[Dict[str, Any]] = Field(None, description="实际生效网格参数")
    effective_coordinate: Optional[Dict[str, Any]] = Field(None, description="实际生效坐标数字参数")
    effective_marker: Optional[List[Dict[str, Any]]] = Field(None, description="实际生效标记点参数")
    effective_crop: Optional[Dict[str, Any]] = Field(None, description="实际生效裁剪参数")
    source_image_path: Optional[str] = Field(None, description="源图片路径")
    adaptive_adjustments: Optional[List[str]] = Field(default=None, description="自适应参数调整说明")


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
    server_time: str = Field(default="", description="服务器当前时间 (yyyy-mm-dd HH:mm:ss)")


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
    requested_params: Optional[Dict[str, Any]] = Field(None, description="请求参数摘要")
    effective_params: Optional[Dict[str, Any]] = Field(None, description="实际生效完整参数")
    effective_scroll: Optional[Dict[str, Any]] = Field(None, description="实际生效滚动参数")
    scroll_count: int = Field(..., description="实际截图数量")
    actual_scroll_percent: float = Field(..., description="实际滚动幅度")
    fixed_header: int = Field(..., description="检测到的固定头部高度")
    fixed_footer: int = Field(..., description="检测到的固定底部高度")


class ScrollScreenshotResponse(BaseResponse):
    """滚动长截图响应"""
    data: Optional[ScrollScreenshotData] = Field(None, description="滚动长截图数据")


# ============ 错误码定义 ============

ERROR_CODES = {
    "WINDOW_NOT_FOUND": {"zh": "窗口不存在", "en": "Window not found. Next: call get_window_list and use a valid window_id. See references/api/get_window_list.md."},
    "PROCESS_BLOCKED": {"zh": "进程在禁止清单中", "en": "Process is blocked. Reason: the process is in the blocked list. Next: choose another window or update security settings manually. See references/api/get_window_list.md."},
    "SCREENSHOT_FAILED": {"zh": "截图失败", "en": "Screenshot failed. Next: verify window_id/main_window_id, try another capture_method, or call get_window_list again. See references/api/screenshot.md."},
    "OPERATION_FAILED": {"zh": "操作失败", "en": "Operation failed. Next: take a screenshot to verify state, then retry with corrected parameters. See the endpoint reference document."},
    "USER_DENIED": {"zh": "用户拒绝操作", "en": "User denied the operation."},
    "TIMEOUT": {"zh": "操作超时", "en": "Operation timeout. Reason: the target window may not be responding. Next: wait, verify the window, and retry. See references/api/wait.md."},
    "AUTH_FAILED": {"zh": "认证失败", "en": "Authentication failed."},
    "INVALID_PARAMS": {"zh": "参数无效", "en": "Invalid parameters. Next: fix the request fields and retry. See the endpoint reference document."},
    "INTERNAL_ERROR": {"zh": "内部错误", "en": "Internal error. Next: check service logs and retry. See references/api/health.md."},
    "UNSUPPORTED_MODE": {"zh": "不支持的操作模式", "en": "Unsupported operation mode for this action. Next: use a supported action_method for this endpoint. See the endpoint reference document."},
    "MONITOR_NOT_FOUND": {"zh": "显示器不存在", "en": "Monitor not found. Next: call GET /api/desktop_get_monitors_list and use a valid monitor_index."},
    "FILE_NOT_FOUND": {"zh": "图片文件不存在", "en": "Image file not found. Next: use the image_path returned by screenshot or pass source_image_base64. See references/api/crop_zoom_screenshot.md."},
    "SELF_CHECK_REQUIRED": {"zh": "需要截图自检", "en": "Self-check required."},
    "SELF_CHECK_NOT_ALLOWED": {"zh": "当前不应传入自检", "en": "Self-check is not expected now. Next: retry without self_check. See references/api/screenshot.md."},
}


def create_error_response(error_code: str, message: str = None) -> BaseResponse:
    """创建错误响应"""
    error_info = ERROR_CODES.get(error_code, {})
    if message is None:
        message = error_info.get("en", "Unknown error")
    return BaseResponse(
        success=False,
        message=message,
        error_code=error_code
    )
