"""
操作API - 点击、长按、滑动、右键、等待
"""
import time
from fastapi import APIRouter, Header

from app.models.request import (
    ClickRequest,
    LongPressRequest,
    SwipeRequest,
    RightClickRequest,
    WaitRequest
)
from app.models.response import (
    BaseResponse,
    create_error_response
)
from app.services.config_service import config_service
from app.services.process_service import process_service
from app.services.log_service import log_service
from app.platform.windows.input import windows_input
from app.utils.coordinate import percent_to_absolute

router = APIRouter()


@router.post("/click")
async def click(request: ClickRequest, authorization: str = Header(None)):
    """点击"""
    start_time = time.time()

    # 获取进程信息
    process_info = process_service.get_process_by_id(request.process_id)
    if not process_info:
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            process_id=request.process_id,
            process_name="",
            instruction="click",
            params={"x": request.x, "y": request.y},
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

    # 执行点击
    inject_result = windows_input.click(hwnd, abs_x, abs_y)

    duration_ms = int((time.time() - start_time) * 1000)

    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        process_id=request.process_id,
        process_name=process_info.process_name,
        instruction="click",
        params={"x": request.x, "y": request.y, "abs_x": abs_x, "abs_y": abs_y},
        result={"success": inject_result.success, "message": inject_result.error},
        duration_ms=duration_ms
    )

    if inject_result.success:
        return BaseResponse(success=True, message="点击成功")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


@router.post("/long_press")
async def long_press(request: LongPressRequest, authorization: str = Header(None)):
    """长按"""
    start_time = time.time()

    process_info = process_service.get_process_by_id(request.process_id)
    if not process_info:
        return create_error_response("PROCESS_NOT_FOUND")

    if config_service.is_process_blocked(process_info.process_name):
        return create_error_response("PROCESS_BLOCKED")

    hwnd = process_service.get_hwnd_by_process_id(request.process_id)
    if not hwnd:
        return create_error_response("INTERNAL_ERROR", "无法获取窗口句柄")

    window_rect = process_service.get_window_rect(hwnd)
    if not window_rect:
        return create_error_response("INTERNAL_ERROR", "无法获取窗口矩形")

    abs_x, abs_y = percent_to_absolute(request.x, request.y, window_rect)

    inject_result = windows_input.long_press(hwnd, abs_x, abs_y, request.duration_ms)

    duration_ms = int((time.time() - start_time) * 1000)

    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        process_id=request.process_id,
        process_name=process_info.process_name,
        instruction="long_press",
        params={"x": request.x, "y": request.y, "duration_ms": request.duration_ms},
        result={"success": inject_result.success, "message": inject_result.error},
        duration_ms=duration_ms
    )

    if inject_result.success:
        return BaseResponse(success=True, message="长按成功")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


@router.post("/swipe")
async def swipe(request: SwipeRequest, authorization: str = Header(None)):
    """滑动"""
    start_time = time.time()

    process_info = process_service.get_process_by_id(request.process_id)
    if not process_info:
        return create_error_response("PROCESS_NOT_FOUND")

    if config_service.is_process_blocked(process_info.process_name):
        return create_error_response("PROCESS_BLOCKED")

    hwnd = process_service.get_hwnd_by_process_id(request.process_id)
    if not hwnd:
        return create_error_response("INTERNAL_ERROR", "无法获取窗口句柄")

    window_rect = process_service.get_window_rect(hwnd)
    if not window_rect:
        return create_error_response("INTERNAL_ERROR", "无法获取窗口矩形")

    abs_start_x, abs_start_y = percent_to_absolute(request.start_x, request.start_y, window_rect)
    abs_end_x, abs_end_y = percent_to_absolute(request.end_x, request.end_y, window_rect)

    inject_result = windows_input.swipe(hwnd, abs_start_x, abs_start_y, abs_end_x, abs_end_y)

    duration_ms = int((time.time() - start_time) * 1000)

    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        process_id=request.process_id,
        process_name=process_info.process_name,
        instruction="swipe",
        params={
            "start": (request.start_x, request.start_y),
            "end": (request.end_x, request.end_y)
        },
        result={"success": inject_result.success, "message": inject_result.error},
        duration_ms=duration_ms
    )

    if inject_result.success:
        return BaseResponse(success=True, message="滑动成功")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


@router.post("/right_click")
async def right_click(request: RightClickRequest, authorization: str = Header(None)):
    """右键点击"""
    start_time = time.time()

    process_info = process_service.get_process_by_id(request.process_id)
    if not process_info:
        return create_error_response("PROCESS_NOT_FOUND")

    if config_service.is_process_blocked(process_info.process_name):
        return create_error_response("PROCESS_BLOCKED")

    hwnd = process_service.get_hwnd_by_process_id(request.process_id)
    if not hwnd:
        return create_error_response("INTERNAL_ERROR", "无法获取窗口句柄")

    window_rect = process_service.get_window_rect(hwnd)
    if not window_rect:
        return create_error_response("INTERNAL_ERROR", "无法获取窗口矩形")

    abs_x, abs_y = percent_to_absolute(request.x, request.y, window_rect)

    inject_result = windows_input.right_click(hwnd, abs_x, abs_y)

    duration_ms = int((time.time() - start_time) * 1000)

    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        process_id=request.process_id,
        process_name=process_info.process_name,
        instruction="right_click",
        params={"x": request.x, "y": request.y},
        result={"success": inject_result.success, "message": inject_result.error},
        duration_ms=duration_ms
    )

    if inject_result.success:
        return BaseResponse(success=True, message="右键成功")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


@router.post("/wait")
async def wait(request: WaitRequest, authorization: str = Header(None)):
    """等待"""
    start_time = time.time()

    time.sleep(request.duration_ms / 1000)

    duration_ms = int((time.time() - start_time) * 1000)

    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        process_id=request.process_id,
        process_name="",
        instruction="wait",
        params={"duration_ms": request.duration_ms},
        result={"success": True},
        duration_ms=duration_ms
    )

    return BaseResponse(success=True, message="等待完成")
