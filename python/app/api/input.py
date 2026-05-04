"""
输入API - 文本输入、按键
支持 background(无感) / hijack(劫持) / delegated(托管) 三种模式
"""
import time
from fastapi import APIRouter, Header, Request

from app.models.request import InputTextRequest, PressKeyRequest
from app.models.response import (
    OperationResponse,
    create_error_response
)
from app.services.log_service import log_service
from app.platform.windows.input import windows_input
from app.utils.coordinate import restore_window_and_calc_coords
from app.api.decorators import with_verification, with_hijack_confirm

router = APIRouter()


def decode_unicode_escapes(text: str) -> str:
    """解码可能的 unicode 转义字符串 (如 \\u4f60\\u597d) 和常见转义序列 (如 \\n, \\t)"""
    try:
        # 解码常见转义序列
        text = text.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')

        # 如果文本包含字面量 \u 转义序列，尝试解码
        if "\\u" in text:
            # 使用 raw_unicode_escape 处理字面量转义
            return text.encode("raw_unicode_escape").decode("unicode_escape")
        return text
    except (UnicodeDecodeError, UnicodeEncodeError):
        # 解码失败，返回原始文本
        return text


@router.post("/input_text")
@with_verification
@with_hijack_confirm("Input text", lambda r: f"Text: {r.text[:50]}{'...' if len(r.text) > 50 else ''}")
async def input_text(request: InputTextRequest, req: Request = None, authorization: str = Header(None)):
    """输入文本"""
    # 装饰器已注入：request.process_info, request.start_time, request.client_ip
    client_ip = request.client_ip

    # 解码可能的 unicode 转义字符
    decoded_text = decode_unicode_escapes(request.text)

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
            return create_error_response("INTERNAL_ERROR", "Cannot get window rectangle. The window may have been closed or minimized. Refer to skill.md for troubleshooting.")
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

    duration_ms = int((time.time() - request.start_time) * 1000)

    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        window_id=request.window_id,
        process_name=request.process_info.process_name,
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
        return OperationResponse(success=True, message="Command sent.")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


@router.post("/press_key")
@with_verification
@with_hijack_confirm("Press key", lambda r: f"Key: {r.key}")
async def press_key(request: PressKeyRequest, req: Request = None, authorization: str = Header(None)):
    """按键"""
    # 装饰器已注入：request.process_info, request.start_time, request.client_ip
    client_ip = request.client_ip

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
            return create_error_response("INTERNAL_ERROR", "Cannot get window rectangle. The window may have been closed or minimized. Refer to skill.md for troubleshooting.")
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

    duration_ms = int((time.time() - request.start_time) * 1000)

    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        window_id=request.window_id,
        process_name=request.process_info.process_name,
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
        return OperationResponse(success=True, message="Command sent.")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)
