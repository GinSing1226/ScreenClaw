"""
操作API - 点击、长按、滑动、滚动、右键、等待
"""
import time
from ctypes import windll
import win32gui
from fastapi import APIRouter, Header, Request

from app.models.request import (
    ClickRequest,
    LongPressRequest,
    SwipeRequest,
    ScrollRequest,
    RightClickRequest,
    HoverRequest,
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
from app.utils.coordinate import restore_window_and_calc_coords
from app.api.decorators import with_verification, log_and_format

router = APIRouter()


def _calc_coords(hwnd: int, x: float, y: float, main_window_id: int = None):
    """计算物理坐标和虚拟坐标（简单封装，调用公共函数）

    Args:
        hwnd: 窗口ID
        x, y: 百分比坐标
        main_window_id: 主窗口ID（可选，用于恢复主窗口）

    Returns:
        (physical_x, physical_y, virtual_x, virtual_y) 或 None
    """
    return restore_window_and_calc_coords(hwnd, x, y, main_window_id)


def _check_hijack_confirm(request, process_info, operation: str, detail: str) -> BaseResponse | None:
    """检查 hijack 模式是否需要用户确认

    Returns:
        None = 通过（background 模式或用户已确认）
        BaseResponse = 错误响应（窗口未找到/进程被禁止/用户拒绝）
    """
    if request.action_method != "hijack":
        return None

    try:
        window_title = win32gui.GetWindowText(request.window_id) or "未知窗口"
    except Exception:
        window_title = "未知窗口"
    from app.services.confirm_service import ConfirmService
    confirm_result = ConfirmService.request_confirm(
        ai_app_type=request.ai_app_type,
        window_title=window_title,
        process_name=process_info.process_name,
        operation=operation,
        operation_detail=detail
    )

    print(f"[ConfirmCheck] → 确认结果: confirmed={confirm_result.confirmed}")
    if not confirm_result.confirmed:
        return create_error_response("USER_DENIED", "用户拒绝操作")
    return None


@router.post("/click")
@with_verification
@log_and_format
async def click(request: ClickRequest, req: Request = None, authorization: str = Header(None)):
    """点击"""
    # 装饰器已注入：request.process_info, request.start_time, request.client_ip

    # hijack 模式需要用户确认
    confirm_error = _check_hijack_confirm(
        request, request.process_info, "点击", f"坐标: ({request.x}, {request.y})"
    )
    if confirm_error:
        return confirm_error

    # 计算坐标
    coords = _calc_coords(request.window_id, request.x, request.y, request.main_window_id)
    if not coords:
        return create_error_response("INTERNAL_ERROR", "无法获取窗口矩形")
    physical_x, physical_y, virtual_x, virtual_y = coords

    # 调试日志：坐标计算
    print(f"[CoordCalc] window_id={request.window_id}, main_window_id={request.main_window_id}")
    print(f"[CoordCalc] physical=({physical_x}, {physical_y})")
    print(f"[CoordCalc] virtual=({virtual_x}, {virtual_y})")

    # 执行点击
    inject_result = windows_input.click(
        request.window_id,
        physical_x, physical_y,
        virtual_x, virtual_y,
        request.action_method
    )

    if inject_result.success:
        return BaseResponse(success=True, message="指令已发送，可截图验证结果")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


@router.post("/long_press")
async def long_press(request: LongPressRequest, authorization: str = Header(None)):
    """长按"""
    start_time = time.time()

    process_info = process_service.get_process_by_window_id(request.window_id)
    if not process_info:
        return create_error_response("WINDOW_NOT_FOUND")

    if config_service.is_process_blocked(process_info.process_name):
        return create_error_response("PROCESS_BLOCKED")

    # hijack 模式需要用户确认
    confirm_error = _check_hijack_confirm(
        request, process_info, "长按",
        f"坐标: ({request.x}, {request.y}), 时长: {request.duration_ms}ms"
    )
    if confirm_error:
        return confirm_error

    # 计算坐标
    coords = _calc_coords(request.window_id, request.x, request.y, request.main_window_id)
    if not coords:
        return create_error_response("INTERNAL_ERROR", "无法获取窗口矩形")
    physical_x, physical_y, virtual_x, virtual_y = coords

    # 执行长按
    inject_result = windows_input.long_press(
        request.window_id,
        physical_x, physical_y,
        virtual_x, virtual_y,
        request.duration_ms,
        request.action_method
    )

    duration_ms = int((time.time() - start_time) * 1000)

    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        window_id=request.window_id,
        process_name=process_info.process_name,
        instruction="long_press",
        params={"x": request.x, "y": request.y, "duration_ms": request.duration_ms, "action_method": request.action_method},
        result={"success": inject_result.success, "message": inject_result.error},
        duration_ms=duration_ms
    )

    if inject_result.success:
        return BaseResponse(success=True, message="指令已发送，可截图验证结果")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


@router.post("/swipe")
async def swipe(request: SwipeRequest, authorization: str = Header(None)):
    """滑动"""
    start_time = time.time()

    process_info = process_service.get_process_by_window_id(request.window_id)
    if not process_info:
        return create_error_response("WINDOW_NOT_FOUND")

    if config_service.is_process_blocked(process_info.process_name):
        return create_error_response("PROCESS_BLOCKED")

    # hijack 模式需要用户确认
    confirm_error = _check_hijack_confirm(
        request, process_info, "滑动",
        f"({request.start_x}, {request.start_y}) → ({request.end_x}, {request.end_y})"
    )
    if confirm_error:
        return confirm_error

    # 计算起点坐标
    start_coords = _calc_coords(request.window_id, request.start_x, request.start_y, request.main_window_id)
    if not start_coords:
        return create_error_response("INTERNAL_ERROR", "无法获取窗口矩形")
    physical_start_x, physical_start_y, virtual_start_x, virtual_start_y = start_coords

    # 计算终点坐标
    end_coords = _calc_coords(request.window_id, request.end_x, request.end_y, request.main_window_id)
    if not end_coords:
        return create_error_response("INTERNAL_ERROR", "无法获取窗口矩形")
    physical_end_x, physical_end_y, virtual_end_x, virtual_end_y = end_coords

    inject_result = windows_input.swipe(
        request.window_id,
        physical_start_x, physical_start_y, physical_end_x, physical_end_y,
        virtual_start_x, virtual_start_y, virtual_end_x, virtual_end_y,
        request.action_method
    )

    duration_ms = int((time.time() - start_time) * 1000)

    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        window_id=request.window_id,
        process_name=process_info.process_name,
        instruction="swipe",
        params={
            "start": (request.start_x, request.start_y),
            "end": (request.end_x, request.end_y),
            "action_method": request.action_method
        },
        result={"success": inject_result.success, "message": inject_result.error},
        duration_ms=duration_ms
    )

    if inject_result.success:
        return BaseResponse(success=True, message="指令已发送，可截图验证结果")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


@router.post("/scroll")
async def scroll(request: ScrollRequest, authorization: str = Header(None)):
    """滚动"""
    start_time = time.time()

    process_info = process_service.get_process_by_window_id(request.window_id)
    if not process_info:
        return create_error_response("WINDOW_NOT_FOUND")

    if config_service.is_process_blocked(process_info.process_name):
        return create_error_response("PROCESS_BLOCKED")

    # hijack 模式需要用户确认
    confirm_error = _check_hijack_confirm(
        request, process_info, "滚动", f"滚动量: {request.delta}"
    )
    if confirm_error:
        return confirm_error

    # 计算坐标
    coords = _calc_coords(request.window_id, request.x, request.y, request.main_window_id)
    if not coords:
        return create_error_response("INTERNAL_ERROR", "无法获取窗口矩形")
    physical_x, physical_y, virtual_x, virtual_y = coords

    inject_result = windows_input.scroll(
        request.window_id,
        physical_x, physical_y,
        virtual_x, virtual_y,
        request.delta,
        request.action_method
    )

    duration_ms = int((time.time() - start_time) * 1000)

    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        window_id=request.window_id,
        process_name=process_info.process_name,
        instruction="scroll",
        params={"x": request.x, "y": request.y, "delta": request.delta, "action_method": request.action_method},
        result={"success": inject_result.success, "message": inject_result.error},
        duration_ms=duration_ms
    )

    if inject_result.success:
        return BaseResponse(success=True, message="指令已发送，可截图验证结果")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


@router.post("/hover")
async def hover(request: HoverRequest, authorization: str = Header(None)):
    """鼠标悬浮 - 移动到目标位置并停留"""
    start_time = time.time()

    process_info = process_service.get_process_by_window_id(request.window_id)
    if not process_info:
        return create_error_response("WINDOW_NOT_FOUND")

    if config_service.is_process_blocked(process_info.process_name):
        return create_error_response("PROCESS_BLOCKED")

    # hijack 模式需要用户确认
    confirm_error = _check_hijack_confirm(
        request, process_info, "鼠标悬浮",
        f"坐标: ({request.x}, {request.y}), 停留: {request.duration_ms}ms"
    )
    if confirm_error:
        return confirm_error

    # 计算坐标
    coords = _calc_coords(request.window_id, request.x, request.y, request.main_window_id)
    if not coords:
        return create_error_response("INTERNAL_ERROR", "无法获取窗口矩形")
    physical_x, physical_y, virtual_x, virtual_y = coords

    inject_result = windows_input.hover(
        request.window_id,
        physical_x, physical_y,
        virtual_x, virtual_y,
        request.duration_ms,
        request.action_method
    )

    duration_ms = int((time.time() - start_time) * 1000)

    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        window_id=request.window_id,
        process_name=process_info.process_name,
        instruction="hover",
        params={"x": request.x, "y": request.y, "duration_ms": request.duration_ms, "action_method": request.action_method},
        result={"success": inject_result.success, "message": inject_result.error},
        duration_ms=duration_ms
    )

    if inject_result.success:
        return BaseResponse(success=True, message="指令已发送，可截图验证结果")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


@router.post("/right_click")
async def right_click(request: RightClickRequest, authorization: str = Header(None)):
    """右键点击"""
    start_time = time.time()

    process_info = process_service.get_process_by_window_id(request.window_id)
    if not process_info:
        return create_error_response("WINDOW_NOT_FOUND")

    if config_service.is_process_blocked(process_info.process_name):
        return create_error_response("PROCESS_BLOCKED")

    # hijack 模式需要用户确认
    confirm_error = _check_hijack_confirm(
        request, process_info, "右键点击", f"坐标: ({request.x}, {request.y})"
    )
    if confirm_error:
        return confirm_error

    # 计算坐标
    coords = _calc_coords(request.window_id, request.x, request.y, request.main_window_id)
    if not coords:
        return create_error_response("INTERNAL_ERROR", "无法获取窗口矩形")
    physical_x, physical_y, virtual_x, virtual_y = coords

    inject_result = windows_input.right_click(
        request.window_id,
        physical_x, physical_y,
        virtual_x, virtual_y,
        request.action_method
    )

    duration_ms = int((time.time() - start_time) * 1000)

    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        window_id=request.window_id,
        process_name=process_info.process_name,
        instruction="right_click",
        params={"x": request.x, "y": request.y, "action_method": request.action_method},
        result={"success": inject_result.success, "message": inject_result.error},
        duration_ms=duration_ms
    )

    if inject_result.success:
        return BaseResponse(success=True, message="指令已发送，可截图验证结果")
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
        window_id=request.window_id,
        process_name="",
        instruction="wait",
        params={"duration_ms": request.duration_ms},
        result={"success": True},
        duration_ms=duration_ms
    )

    return BaseResponse(success=True, message="等待完成")
