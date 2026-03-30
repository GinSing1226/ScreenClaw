"""
输入API - 文本输入、按键
支持 background(无感) / hijack(劫持) 两种模式
"""
import time
import win32gui
from fastapi import APIRouter, Header, Request

from app.models.request import InputTextRequest, PressKeyRequest
from app.models.response import (
    OperationResponse,
    create_error_response
)
from app.services.config_service import config_service
from app.services.process_service import process_service
from app.services.log_service import log_service
from app.platform.windows.input import windows_input
from app.utils.coordinate import restore_window_and_calc_coords

router = APIRouter()


def decode_unicode_escapes(text: str) -> str:
    """解码可能的 unicode 转义字符串 (如 \\u4f60\\u597d)"""
    try:
        # 如果文本包含字面量 \u 转义序列，尝试解码
        if "\\u" in text:
            # 使用 raw_unicode_escape 处理字面量转义
            return text.encode("raw_unicode_escape").decode("unicode_escape")
        return text
    except (UnicodeDecodeError, UnicodeEncodeError):
        # 解码失败，返回原始文本
        return text


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    if request.client:
        return request.client.host
    return "unknown"


@router.post("/input_text")
async def input_text(request: InputTextRequest, req: Request = None, authorization: str = Header(None)):
    """输入文本"""
    client_ip = get_client_ip(req) if req else "unknown"
    start_time = time.time()

    # 获取窗口信息
    process_info = process_service.get_process_by_window_id(request.window_id)
    if not process_info:
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            window_id=request.window_id,
            process_name="",
            instruction="input_text",
            params={"x": request.x, "y": request.y, "text": request.text[:50] + "..."},
            result={"success": False, "message": "Window not found"},
            client_ip=client_ip
        )
        return create_error_response("WINDOW_NOT_FOUND")

    # 检查进程是否被禁止
    if config_service.is_process_blocked(process_info.process_name):
        return create_error_response("PROCESS_BLOCKED")

    # 解码可能的 unicode 转义字符（需要在确认之前，因为确认时需要显示文本）
    decoded_text = decode_unicode_escapes(request.text)

    # hijack 模式需要用户确认
    if request.action_method == "hijack":
        try:
            window_title = win32gui.GetWindowText(request.window_id) or "未知窗口"
        except Exception:
            window_title = "未知窗口"

        from app.services.confirm_service import ConfirmService
        confirm_result = ConfirmService.request_confirm(
            ai_app_type=request.ai_app_type,
            window_title=window_title,
            process_name=process_info.process_name,
            operation="输入文本",
            operation_detail=f"输入：{decoded_text[:50]}{'...' if len(decoded_text) > 50 else ''}"
        )

        if not confirm_result.confirmed:
            return create_error_response("USER_DENIED", "用户拒绝操作")

    # 坐标计算（如果传了坐标）- 包含窗口恢复逻辑
    physical_x = None
    physical_y = None
    virtual_x = None
    virtual_y = None

    if request.x is not None and request.y is not None:
        coords = restore_window_and_calc_coords(
            request.window_id, request.x, request.y, request.main_window_id
        )
        if not coords:
            return create_error_response("INTERNAL_ERROR", "Cannot get window rectangle")
        physical_x, physical_y, virtual_x, virtual_y = coords

    # 执行输入
    inject_result = windows_input.input_text(
        request.window_id,
        physical_x, physical_y,
        virtual_x, virtual_y,
        decoded_text,
        request.newline_key,
        request.action_method
    )

    duration_ms = int((time.time() - start_time) * 1000)

    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        window_id=request.window_id,
        process_name=process_info.process_name,
        instruction="input_text",
        params={
            "x": request.x, "y": request.y,
            "text_length": len(decoded_text),
            "action_method": request.action_method
        },
        result={"success": inject_result.success, "message": inject_result.error},
        duration_ms=duration_ms,
        client_ip=client_ip
    )

    if inject_result.success:
        return OperationResponse(success=True, message="Command sent, verify with screenshot")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


@router.post("/press_key")
async def press_key(request: PressKeyRequest, req: Request = None, authorization: str = Header(None)):
    """按键"""
    client_ip = get_client_ip(req) if req else "unknown"
    start_time = time.time()

    # 获取窗口信息
    process_info = process_service.get_process_by_window_id(request.window_id)
    if not process_info:
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            window_id=request.window_id,
            process_name="",
            instruction="press_key",
            params={"key": request.key},
            result={"success": False, "message": "Window not found"},
            client_ip=client_ip
        )
        return create_error_response("WINDOW_NOT_FOUND")

    # 检查进程是否被禁止
    if config_service.is_process_blocked(process_info.process_name):
        return create_error_response("PROCESS_BLOCKED")

    # hijack 模式需要用户确认
    if request.action_method == "hijack":
        try:
            window_title = win32gui.GetWindowText(request.window_id) or "未知窗口"
        except Exception:
            window_title = "未知窗口"

        from app.services.confirm_service import ConfirmService
        confirm_result = ConfirmService.request_confirm(
            ai_app_type=request.ai_app_type,
            window_title=window_title,
            process_name=process_info.process_name,
            operation="按键",
            operation_detail=f"按键：{request.key}"
        )

        if not confirm_result.confirmed:
            return create_error_response("USER_DENIED", "用户拒绝操作")

    # 可选的坐标计算（如果传了 x, y）- 包含窗口恢复逻辑
    physical_x = None
    physical_y = None
    virtual_x = None
    virtual_y = None

    if request.x is not None and request.y is not None:
        coords = restore_window_and_calc_coords(
            request.window_id, request.x, request.y, request.main_window_id
        )
        if not coords:
            return create_error_response("INTERNAL_ERROR", "Cannot get window rectangle")
        physical_x, physical_y, virtual_x, virtual_y = coords

    # 执行按键
    inject_result = windows_input.key_press(
        request.window_id,
        request.key,
        physical_x=physical_x,
        physical_y=physical_y,
        virtual_x=virtual_x,
        virtual_y=virtual_y,
        duration_ms=request.duration_ms,
        action_method=request.action_method,
        non_blocking=False  # 单独指令阻塞等待
    )

    duration_ms = int((time.time() - start_time) * 1000)

    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        window_id=request.window_id,
        process_name=process_info.process_name,
        instruction="press_key",
        params={
            "key": request.key,
            "x": request.x,
            "y": request.y,
            "duration_ms": request.duration_ms,
            "action_method": request.action_method
        },
        result={"success": inject_result.success, "message": inject_result.error},
        duration_ms=duration_ms,
        client_ip=client_ip
    )

    if inject_result.success:
        return OperationResponse(success=True, message="Command sent, verify with screenshot")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)
