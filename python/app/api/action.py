"""
操作API - 点击、长按、滑动、拖拽、滚动、右键、等待
"""
import time
from fastapi import APIRouter, Header, Request

from app.models.request import (
    ClickRequest,
    LongPressRequest,
    SwipeRequest,
    DragRequest,
    MouseMoveRequest,
    ScrollRequest,
    RightClickRequest,
    HoverRequest,
    WaitRequest
)
from app.models.response import (
    BaseResponse,
    create_error_response
)
from app.services.log_service import log_service
from app.platform.windows.input import windows_input
from app.utils.coordinate import restore_window_and_calc_coords
from app.api.decorators import with_verification, log_and_format, with_hijack_confirm

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


@router.post("/click")
@with_verification
@with_hijack_confirm("Click", lambda r: f"Coordinates: ({r.x}, {r.y})")
@log_and_format
async def click(request: ClickRequest, req: Request = None, authorization: str = Header(None)):
    """点击"""
    # 装饰器已注入：request.process_info, request.start_time, request.client_ip

    # 计算坐标
    coords = _calc_coords(request.window_id, request.x, request.y, request.main_window_id)
    if not coords:
        return create_error_response("INTERNAL_ERROR", "Cannot get window rectangle")
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
        return BaseResponse(success=True, message="Command sent, verify with screenshot")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


@router.post("/long_press")
@with_verification
@with_hijack_confirm("Long press", lambda r: f"Coordinates: ({r.x}, {r.y}), Duration: {r.duration_ms}ms")
@log_and_format
async def long_press(request: LongPressRequest, req: Request = None, authorization: str = Header(None)):
    """长按"""
    # 计算坐标
    coords = _calc_coords(request.window_id, request.x, request.y, request.main_window_id)
    if not coords:
        return create_error_response("INTERNAL_ERROR", "Cannot get window rectangle")
    physical_x, physical_y, virtual_x, virtual_y = coords

    # 执行长按
    inject_result = windows_input.long_press(
        request.window_id,
        physical_x, physical_y,
        virtual_x, virtual_y,
        request.duration_ms,
        request.action_method
    )

    if inject_result.success:
        return BaseResponse(success=True, message="Command sent, verify with screenshot")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


@router.post("/swipe")
@with_verification
@with_hijack_confirm("Swipe", lambda r: f"({r.start_x}, {r.start_y}) → ({r.end_x}, {r.end_y})")
@log_and_format
async def swipe(request: SwipeRequest, req: Request = None, authorization: str = Header(None)):
    """滑动"""
    # 计算起点坐标
    start_coords = _calc_coords(request.window_id, request.start_x, request.start_y, request.main_window_id)
    if not start_coords:
        return create_error_response("INTERNAL_ERROR", "Cannot get window rectangle")
    physical_start_x, physical_start_y, virtual_start_x, virtual_start_y = start_coords

    # 计算终点坐标
    end_coords = _calc_coords(request.window_id, request.end_x, request.end_y, request.main_window_id)
    if not end_coords:
        return create_error_response("INTERNAL_ERROR", "Cannot get window rectangle")
    physical_end_x, physical_end_y, virtual_end_x, virtual_end_y = end_coords

    inject_result = windows_input.swipe(
        request.window_id,
        physical_start_x, physical_start_y, physical_end_x, physical_end_y,
        virtual_start_x, virtual_start_y, virtual_end_x, virtual_end_y,
        request.action_method
    )

    if inject_result.success:
        return BaseResponse(success=True, message="Command sent, verify with screenshot")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


@router.post("/drag")
@with_verification
@with_hijack_confirm("Drag", lambda r: f"({r.start_x}, {r.start_y}) → ({r.end_x}, {r.end_y}), Duration: {r.duration_ms}ms")
@log_and_format
async def drag(request: DragRequest, req: Request = None, authorization: str = Header(None)):
    """拖拽"""
    # 计算起点坐标
    start_coords = _calc_coords(request.window_id, request.start_x, request.start_y, request.main_window_id)
    if not start_coords:
        return create_error_response("INTERNAL_ERROR", "Cannot get window rectangle")
    physical_start_x, physical_start_y, virtual_start_x, virtual_start_y = start_coords

    # 计算终点坐标
    end_coords = _calc_coords(request.window_id, request.end_x, request.end_y, request.main_window_id)
    if not end_coords:
        return create_error_response("INTERNAL_ERROR", "Cannot get window rectangle")
    physical_end_x, physical_end_y, virtual_end_x, virtual_end_y = end_coords

    inject_result = windows_input.drag(
        request.window_id,
        physical_start_x, physical_start_y, physical_end_x, physical_end_y,
        virtual_start_x, virtual_start_y, virtual_end_x, virtual_end_y,
        request.duration_ms,
        request.action_method
    )

    if inject_result.success:
        return BaseResponse(success=True, message="Command sent, verify with screenshot")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


@router.post("/mouse_move")
@with_verification
@with_hijack_confirm("Mouse move", lambda r: f"delta=({r.delta_x}, {r.delta_y}), Duration: {r.duration_ms}ms")
@log_and_format
async def mouse_move(request: MouseMoveRequest, req: Request = None, authorization: str = Header(None)):
    """鼠标移动 - 相对位移，用于游戏视角控制"""
    inject_result = windows_input.mouse_move(
        request.window_id,
        request.delta_x,
        request.delta_y,
        request.duration_ms,
        request.action_method
    )

    if inject_result.success:
        return BaseResponse(success=True, message="Command sent, verify with screenshot")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


@router.post("/scroll")
@with_verification
@with_hijack_confirm("Scroll", lambda r: f"Delta: {r.delta}")
@log_and_format
async def scroll(request: ScrollRequest, req: Request = None, authorization: str = Header(None)):
    """滚动"""
    # 计算坐标
    coords = _calc_coords(request.window_id, request.x, request.y, request.main_window_id)
    if not coords:
        return create_error_response("INTERNAL_ERROR", "Cannot get window rectangle")
    physical_x, physical_y, virtual_x, virtual_y = coords

    inject_result = windows_input.scroll(
        request.window_id,
        physical_x, physical_y,
        virtual_x, virtual_y,
        request.delta,
        request.action_method
    )

    if inject_result.success:
        return BaseResponse(success=True, message="Command sent, verify with screenshot")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


@router.post("/hover")
@with_verification
@with_hijack_confirm("Hover", lambda r: f"Coordinates: ({r.x}, {r.y}), Duration: {r.duration_ms}ms")
@log_and_format
async def hover(request: HoverRequest, req: Request = None, authorization: str = Header(None)):
    """鼠标悬浮 - 移动到目标位置并停留"""
    # 计算坐标
    coords = _calc_coords(request.window_id, request.x, request.y, request.main_window_id)
    if not coords:
        return create_error_response("INTERNAL_ERROR", "Cannot get window rectangle")
    physical_x, physical_y, virtual_x, virtual_y = coords

    inject_result = windows_input.hover(
        request.window_id,
        physical_x, physical_y,
        virtual_x, virtual_y,
        request.duration_ms,
        request.action_method
    )

    if inject_result.success:
        return BaseResponse(success=True, message="Command sent, verify with screenshot")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


@router.post("/right_click")
@with_verification
@with_hijack_confirm("Right-click", lambda r: f"Coordinates: ({r.x}, {r.y})")
@log_and_format
async def right_click(request: RightClickRequest, req: Request = None, authorization: str = Header(None)):
    """右键点击"""
    # 计算坐标
    coords = _calc_coords(request.window_id, request.x, request.y, request.main_window_id)
    if not coords:
        return create_error_response("INTERNAL_ERROR", "Cannot get window rectangle")
    physical_x, physical_y, virtual_x, virtual_y = coords

    inject_result = windows_input.right_click(
        request.window_id,
        physical_x, physical_y,
        virtual_x, virtual_y,
        request.action_method
    )

    if inject_result.success:
        return BaseResponse(success=True, message="Command sent, verify with screenshot")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


@router.post("/wait")
async def wait(request: WaitRequest, req: Request = None, authorization: str = Header(None)):
    """等待"""
    from app.api.decorators import get_client_ip

    start_time = time.time()
    client_ip = get_client_ip(req) if req else "unknown"

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
        duration_ms=duration_ms,
        client_ip=client_ip
    )

    return BaseResponse(success=True, message="Wait completed")
