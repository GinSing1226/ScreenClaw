"""
输入API - 文本输入、按键
"""
import time
from fastapi import APIRouter, Header

from app.models.request import InputTextRequest, PressKeyRequest
from app.models.response import (
    OperationResponse,
    create_error_response
)
from app.services.config_service import config_service
from app.services.process_service import process_service
from app.services.log_service import log_service
from app.platform.windows.input import windows_input
from app.utils.coordinate import percent_to_absolute

router = APIRouter()


@router.post("/input_text")
async def input_text(request: InputTextRequest, authorization: str = Header(None)):
    """输入文本"""
    start_time = time.time()

    # 获取进程信息
    process_info = process_service.get_process_by_id(request.process_id)
    if not process_info:
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            process_id=request.process_id,
            process_name="",
            instruction="input_text",
            params={"x": request.x, "y": request.y, "text": request.text[:50] + "..."},
            result={"success": False, "message": "进程不存在"}
        )
        return create_error_response("PROCESS_NOT_FOUND")

    # 检查进程是否被禁止
    if config_service.is_process_blocked(process_info.process_name):
        return create_error_response("PROCESS_BLOCKED")

    # 获取窗口句柄
    hwnd = process_service.get_hwnd_by_process_id(request.process_id)
    if not hwnd:
        return create_error_response("INTERNAL_ERROR", "无法获取窗口句柄")

    # 获取窗口矩形并转换坐标
    window_rect = process_service.get_window_rect(hwnd)
    if not window_rect:
        return create_error_response("INTERNAL_ERROR", "无法获取窗口矩形")

    abs_x, abs_y = percent_to_absolute(request.x, request.y, window_rect)

    # 执行输入
    inject_result = windows_input.input_text(hwnd, abs_x, abs_y, request.text)

    duration_ms = int((time.time() - start_time) * 1000)

    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        process_id=request.process_id,
        process_name=process_info.process_name,
        instruction="input_text",
        params={"x": request.x, "y": request.y, "text_length": len(request.text)},
        result={"success": inject_result.success, "message": inject_result.error},
        duration_ms=duration_ms
    )

    if inject_result.success:
        return OperationResponse(success=True, message="输入成功")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


@router.post("/press_key")
async def press_key(request: PressKeyRequest, authorization: str = Header(None)):
    """按键"""
    start_time = time.time()

    # 获取进程信息
    process_info = process_service.get_process_by_id(request.process_id)
    if not process_info:
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            process_id=request.process_id,
            process_name="",
            instruction="press_key",
            params={"key": request.key},
            result={"success": False, "message": "进程不存在"}
        )
        return create_error_response("PROCESS_NOT_FOUND")

    # 检查进程是否被禁止
    if config_service.is_process_blocked(process_info.process_name):
        return create_error_response("PROCESS_BLOCKED")

    # 获取窗口句柄
    hwnd = process_service.get_hwnd_by_process_id(request.process_id)
    if not hwnd:
        return create_error_response("INTERNAL_ERROR", "无法获取窗口句柄")

    # 执行按键
    inject_result = windows_input.key_press(hwnd, request.key)

    duration_ms = int((time.time() - start_time) * 1000)

    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        process_id=request.process_id,
        process_name=process_info.process_name,
        instruction="press_key",
        params={"key": request.key},
        result={"success": inject_result.success, "message": inject_result.error},
        duration_ms=duration_ms
    )

    if inject_result.success:
        return OperationResponse(success=True, message="按键成功")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)
