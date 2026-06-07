"""
桌面级操作 API

路由: /api/desktop_xxx（动作名前缀 desktop_）
固定 hijack 模式，无 action_method 参数
"""
import time
import os
from fastapi import APIRouter, Header, Request

from app.models.desktop_request import (
    DesktopScreenshotRequest,
    DesktopClickRequest,
    DesktopDoubleClickRequest,
    DesktopRightClickRequest,
    DesktopDragRequest,
    DesktopScrollRequest,
    DesktopInputTextRequest,
    DesktopPressKeyRequest,
    DesktopHoverRequest,
    GridParams,
    CoordinateParams,
    MarkerParams,
)
from app.models.response import (
    BaseResponse,
    ScreenshotResponse,
    ScreenshotData,
    create_error_response,
)
from app.services.config_service import config_service
from app.services.log_service import log_service
from app.services.confirm_service import ConfirmService
from app.services.self_check_service import self_check_service
from app.services.screenshot_params_service import screenshot_params_service, strip_defaults, grid_defaults, coordinate_defaults, marker_defaults
from app.platform.windows.desktop_capture import (
    get_monitors,
    capture_monitor,
    get_monitor_dpi_scale,
    desktop_percent_to_screen,
    desktop_click,
    desktop_double_click,
    desktop_right_click,
    desktop_drag,
    desktop_scroll,
    desktop_input_text,
    desktop_press_key,
    desktop_hover,
)
from app.core.grid import GridRenderer
from app.utils.image import (
    compress_image,
    image_to_base64,
    save_image,
    generate_desktop_screenshot_filename,
    generate_data_dir,
)
from app.api.decorators import get_client_ip

router = APIRouter()


def _is_local_request(client_ip: str) -> bool:
    """判断是否为本地请求"""
    local_ips = {"127.0.0.1", "::1", "localhost"}
    return client_ip in local_ips


def _validate_monitor(monitor_index: int):
    """验证 monitor_index 是否有效"""
    monitors = get_monitors()
    if monitor_index < 0 or monitor_index >= len(monitors):
        return None
    return monitors[monitor_index]


# ============ 显示器枚举 ============

@router.get("/desktop_get_monitors_list")
async def get_monitors_endpoint():
    """枚举所有显示器"""
    monitors = get_monitors()
    return BaseResponse(success=True, message="OK", data={"monitors": monitors})


# ============ 桌面截图 ============

@router.post("/desktop_screenshot", response_model=ScreenshotResponse, response_model_exclude_none=True)
async def desktop_screenshot(
    request: DesktopScreenshotRequest,
    req: Request = None,
    authorization: str = Header(None)
):
    """桌面截图"""
    client_ip = get_client_ip(req) if req else "unknown"
    start_time = time.time()

    # 验证 monitor_index
    monitors = get_monitors()
    if request.monitor_index < 0 or request.monitor_index >= len(monitors):
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            window_id=None,
            process_name=None,
            instruction="desktop_screenshot",
            params=request.model_dump(exclude={"self_check"}),
            result={"success": False, "message": "Monitor not found"},
            client_ip=client_ip,
            monitor_index=request.monitor_index,
        )
        return create_error_response("MONITOR_NOT_FOUND")

    config = config_service.get()

    # 自检验证
    self_check_result = self_check_service.validate_before_screenshot(
        request.session_id,
        request.self_check,
        config.self_check
    )
    if not self_check_result.ok:
        return self_check_result.response

    # 截图
    try:
        image = capture_monitor(request.monitor_index)
    except (IndexError, Exception) as e:
        return create_error_response("SCREENSHOT_FAILED", str(e))

    # 窗口原始信息（压缩前记录）
    window_info = {
        "source_width": image.size[0],
        "source_height": image.size[1],
        "scale_factor": get_monitor_dpi_scale(request.monitor_index),
    }

    # 压缩
    image = compress_image(
        image,
        quality=config.screenshot.image_quality,
        max_width=config.screenshot.max_image_width
    )

    effective_grid = None
    effective_coordinate = None
    effective_color_mode = request.color_mode or config.screenshot.default_color_mode
    adaptive_adjustments = []
    renderer = None

    # 绘制网格
    if request.coordinate_type != "no":
        params_result = screenshot_params_service.build_from_request(
            request,
            config,
            image.size
        )
        effective_grid = params_result.grid
        effective_coordinate = params_result.coordinate
        effective_color_mode = params_result.color_mode
        adaptive_adjustments = params_result.adaptive_adjustments

        renderer = GridRenderer(
            density_x=effective_grid["density_x"],
            density_y=effective_grid["density_y"],
            grid_opacity=effective_grid["opacity"],
            grid_color=effective_grid["color"],
            number_density=effective_coordinate["number_density"],
            number_decimal=effective_coordinate["number_decimal"],
            number_size=effective_coordinate["number_size"],
            number_color=effective_coordinate["number_color"],
            number_opacity=effective_coordinate["number_opacity"],
            number_stroke_width=effective_coordinate["number_stroke_width"],
            number_stroke_color=effective_coordinate["number_stroke_color"],
            color_mode=params_result.color_mode
        )
        image = renderer.draw_grid(image)

    # 绘制标记
    if request.marker:
        renderer = GridRenderer() if renderer is None else renderer
        for m in request.marker:
            image = renderer.draw_marker(
                image,
                x=m.x, y=m.y,
                ring_radius=m.ring_radius,
                ring_line_width=m.ring_line_width,
                ring_color=m.ring_color,
                dot_radius=m.dot_radius,
                dot_color=m.dot_color
            )

    # 保存图片（desktop- 前缀）
    data_dir = generate_data_dir("data", request.ai_app_type, request.session_id)
    filename = generate_desktop_screenshot_filename()
    image_path = os.path.join(data_dir, filename)
    save_image(image, image_path, config.screenshot.image_quality)

    image_base64 = image_to_base64(image)
    duration_ms = int((time.time() - start_time) * 1000)

    # 自检计数
    self_check_service.record_screenshot_success(request.session_id, config.self_check, units=1)

    is_local = _is_local_request(client_ip)
    effective_marker = [m.model_dump() for m in request.marker] if request.marker else None

    # 过滤与 config 默认值相同的字段，减少响应 token
    grid_def = grid_defaults(config)
    coord_def = coordinate_defaults(config)
    marker_def = marker_defaults(config)
    filtered_grid = strip_defaults(effective_grid, grid_def)
    filtered_coordinate = strip_defaults(effective_coordinate, coord_def)
    filtered_marker = (
        [strip_defaults(m, marker_def) for m in effective_marker]
        if effective_marker else None
    )
    filtered_adjustments = adaptive_adjustments if adaptive_adjustments else None

    if is_local:
        screenshot_data = ScreenshotData(
            image_path=os.path.abspath(image_path),
            window_info=window_info,
            effective_grid=filtered_grid,
            effective_coordinate=filtered_coordinate,
            effective_marker=filtered_marker,
            adaptive_adjustments=filtered_adjustments
        )
    else:
        screenshot_data = ScreenshotData(
            image_base64=image_base64,
            window_info=window_info,
            effective_grid=filtered_grid,
            effective_coordinate=filtered_coordinate,
            effective_marker=filtered_marker,
            adaptive_adjustments=filtered_adjustments
        )

    success_message = "Desktop screenshot successful."
    if request.marker:
        success_message += " Marker drawn."

    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        window_id=None,
        process_name=None,
        instruction="desktop_screenshot",
        params=request.model_dump(exclude={"self_check"}),
        result={"success": True, "message": success_message},
        duration_ms=duration_ms,
        client_ip=client_ip,
        monitor_index=request.monitor_index,
    )

    return ScreenshotResponse(success=True, message=success_message, data=screenshot_data)


# ============ 桌面操作公共逻辑 ============

def _desktop_hijack_confirm(request, operation: str, detail: str = "") -> bool:
    """桌面级 hijack 确认

    与窗口级的 with_hijack_confirm 类似，但桌面级没有窗口白名单机制。
    - delegated 模式激活 → 跳过确认
    - 否则 → 弹出确认弹窗，用户可拒绝

    Returns:
        True 表示允许操作，False 表示用户拒绝
    """
    # delegated 模式 → 直接放行
    if config_service.is_delegated_active():
        return True

    # 构造桌面级上下文信息
    window_title = f"Desktop (Monitor {request.monitor_index})"
    process_name = ""  # 桌面级无进程名，不设白名单

    confirm_result = ConfirmService.request_confirm(
        ai_app_type=request.ai_app_type,
        window_title=window_title,
        process_name=process_name,
        operation=operation,
        operation_detail=detail,
        show_remember=False,  # 桌面级无白名单，不显示"记住选择"
    )
    return confirm_result.confirmed


def _build_detail(request, instruction: str) -> str:
    """根据操作类型构建详情文本"""
    parts = [f"Monitor {request.monitor_index}"]
    if hasattr(request, 'x') and request.x is not None:
        parts.append(f"({request.x}, {request.y})")
    elif hasattr(request, 'start_x') and request.start_x is not None:
        parts.append(f"({request.start_x},{request.start_y})->({request.end_x},{request.end_y})")
    if instruction == "desktop_input_text" and hasattr(request, 'text'):
        parts.append(f"Text: {request.text}")
    elif instruction == "desktop_press_key" and hasattr(request, 'keys'):
        parts.append(f"Keys: {request.keys}")
    elif instruction == "desktop_scroll" and hasattr(request, 'delta'):
        parts.append(f"Delta: {request.delta}")
    elif instruction == "desktop_hover" and hasattr(request, 'duration_ms'):
        parts.append(f"{request.duration_ms}ms")
    elif instruction == "desktop_drag" and hasattr(request, 'duration_ms'):
        parts.append(f"Monitor {request.end_monitor_index}")
    return " ".join(parts)


def _desktop_action(request, instruction: str, action_fn, restore: bool = True, **action_kwargs):
    """桌面操作公共逻辑：hijack确认 + 坐标转换 + 执行 + 日志"""
    client_ip = getattr(request, 'client_ip', 'unknown')
    start_time = getattr(request, 'start_time', time.time())

    # hijack 确认（delegated 模式自动跳过）
    operation_name = instruction.replace("desktop_", "").replace("_", " ").title()
    detail = _build_detail(request, instruction)
    if not _desktop_hijack_confirm(request, operation_name, detail):
        return create_error_response("USER_DENIED", "User denied the operation")

    # 验证 monitor_index
    monitors = get_monitors()
    if request.monitor_index < 0 or request.monitor_index >= len(monitors):
        return create_error_response("MONITOR_NOT_FOUND")

    # 坐标转换
    try:
        screen_x, screen_y = desktop_percent_to_screen(request.monitor_index, request.x, request.y)
    except IndexError:
        return create_error_response("MONITOR_NOT_FOUND")

    # 检查是否在 delegated 模式（已通过 hijack 确认，此处仅控制 restore 行为）
    if config_service.is_delegated_active():
        restore = False

    # 执行操作
    inject_result = action_fn(screen_x, screen_y, restore=restore, **action_kwargs)

    duration_ms = int((time.time() - start_time) * 1000)

    if inject_result.success:
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            window_id=None,
            process_name=None,
            instruction=instruction,
            params=request.model_dump(),
            result={"success": True, "message": f"{instruction} succeeded."},
            duration_ms=duration_ms,
            client_ip=client_ip,
            monitor_index=request.monitor_index,
        )
        return BaseResponse(success=True, message="Command sent.")
    else:
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            window_id=None,
            process_name=None,
            instruction=instruction,
            params=request.model_dump(),
            result={"success": False, "message": inject_result.error},
            duration_ms=duration_ms,
            client_ip=client_ip,
            monitor_index=request.monitor_index,
        )
        return create_error_response("OPERATION_FAILED", inject_result.error)


# ============ 桌面点击 ============

@router.post("/desktop_click")
async def desktop_click_endpoint(
    request: DesktopClickRequest,
    req: Request = None,
    authorization: str = Header(None)
):
    """桌面点击"""
    object.__setattr__(request, 'client_ip', get_client_ip(req) if req else "unknown")
    object.__setattr__(request, 'start_time', time.time())
    return _desktop_action(request, "desktop_click", desktop_click)


@router.post("/desktop_double_click")
async def desktop_double_click_endpoint(
    request: DesktopDoubleClickRequest,
    req: Request = None,
    authorization: str = Header(None)
):
    """桌面双击"""
    object.__setattr__(request, 'client_ip', get_client_ip(req) if req else "unknown")
    object.__setattr__(request, 'start_time', time.time())
    return _desktop_action(request, "desktop_double_click", desktop_double_click)


@router.post("/desktop_right_click")
async def desktop_right_click_endpoint(
    request: DesktopRightClickRequest,
    req: Request = None,
    authorization: str = Header(None)
):
    """桌面右键"""
    object.__setattr__(request, 'client_ip', get_client_ip(req) if req else "unknown")
    object.__setattr__(request, 'start_time', time.time())
    return _desktop_action(request, "desktop_right_click", desktop_right_click)


# ============ 桌面拖拽 ============

@router.post("/desktop_drag")
async def desktop_drag_endpoint(
    request: DesktopDragRequest,
    req: Request = None,
    authorization: str = Header(None)
):
    """桌面拖拽（支持跨屏）"""
    client_ip = get_client_ip(req) if req else "unknown"
    start_time = time.time()

    # hijack 确认
    detail = _build_detail(request, "desktop_drag")
    if not _desktop_hijack_confirm(request, "Drag", detail):
        return create_error_response("USER_DENIED", "User denied the operation")

    monitors = get_monitors()
    if request.monitor_index < 0 or request.monitor_index >= len(monitors):
        return create_error_response("MONITOR_NOT_FOUND")
    if request.end_monitor_index < 0 or request.end_monitor_index >= len(monitors):
        return create_error_response("MONITOR_NOT_FOUND")

    try:
        start_x, start_y = desktop_percent_to_screen(request.monitor_index, request.start_x, request.start_y)
        end_x, end_y = desktop_percent_to_screen(request.end_monitor_index, request.end_x, request.end_y)
    except IndexError:
        return create_error_response("MONITOR_NOT_FOUND")

    restore = not config_service.is_delegated_active()
    inject_result = desktop_drag(start_x, start_y, end_x, end_y, request.duration_ms, restore=restore)

    duration_ms = int((time.time() - start_time) * 1000)

    if inject_result.success:
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            window_id=None, process_name=None,
            instruction="desktop_drag",
            params=request.model_dump(),
            result={"success": True, "message": "Drag succeeded."},
            duration_ms=duration_ms,
            client_ip=client_ip,
            monitor_index=request.monitor_index,
        )
        return BaseResponse(success=True, message="Command sent.")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


# ============ 桌面滚动 ============

@router.post("/desktop_scroll")
async def desktop_scroll_endpoint(
    request: DesktopScrollRequest,
    req: Request = None,
    authorization: str = Header(None)
):
    """桌面滚动"""
    client_ip = get_client_ip(req) if req else "unknown"
    start_time = time.time()

    # hijack 确认
    detail = _build_detail(request, "desktop_scroll")
    if not _desktop_hijack_confirm(request, "Scroll", detail):
        return create_error_response("USER_DENIED", "User denied the operation")

    monitors = get_monitors()
    if request.monitor_index < 0 or request.monitor_index >= len(monitors):
        return create_error_response("MONITOR_NOT_FOUND")

    try:
        screen_x, screen_y = desktop_percent_to_screen(request.monitor_index, request.x, request.y)
    except IndexError:
        return create_error_response("MONITOR_NOT_FOUND")

    restore = not config_service.is_delegated_active()
    inject_result = desktop_scroll(screen_x, screen_y, request.delta, restore=restore)

    duration_ms = int((time.time() - start_time) * 1000)

    if inject_result.success:
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            window_id=None, process_name=None,
            instruction="desktop_scroll",
            params=request.model_dump(),
            result={"success": True, "message": "Scroll succeeded."},
            duration_ms=duration_ms,
            client_ip=client_ip,
            monitor_index=request.monitor_index,
        )
        return BaseResponse(success=True, message="Command sent.")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


# ============ 桌面文本输入 ============

@router.post("/desktop_input_text")
async def desktop_input_text_endpoint(
    request: DesktopInputTextRequest,
    req: Request = None,
    authorization: str = Header(None)
):
    """桌面文本输入"""
    object.__setattr__(request, 'client_ip', get_client_ip(req) if req else "unknown")
    object.__setattr__(request, 'start_time', time.time())

    # hijack 确认
    detail = _build_detail(request, "desktop_input_text")
    if not _desktop_hijack_confirm(request, "Input Text", detail):
        return create_error_response("USER_DENIED", "User denied the operation")

    # input_text 的 action_fn 签名不同，需要传 text
    client_ip = getattr(request, 'client_ip', 'unknown')
    start_time = getattr(request, 'start_time', time.time())

    monitors = get_monitors()
    if request.monitor_index < 0 or request.monitor_index >= len(monitors):
        return create_error_response("MONITOR_NOT_FOUND")

    try:
        screen_x, screen_y = desktop_percent_to_screen(request.monitor_index, request.x, request.y)
    except IndexError:
        return create_error_response("MONITOR_NOT_FOUND")

    restore = not config_service.is_delegated_active()
    inject_result = desktop_input_text(screen_x, screen_y, request.text, restore=restore)

    duration_ms = int((time.time() - start_time) * 1000)

    if inject_result.success:
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            window_id=None, process_name=None,
            instruction="desktop_input_text",
            params=request.model_dump(),
            result={"success": True, "message": "Input text succeeded."},
            duration_ms=duration_ms,
            client_ip=client_ip,
            monitor_index=request.monitor_index,
        )
        return BaseResponse(success=True, message="Command sent.")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


# ============ 桌面按键 ============

@router.post("/desktop_press_key")
async def desktop_press_key_endpoint(
    request: DesktopPressKeyRequest,
    req: Request = None,
    authorization: str = Header(None)
):
    """桌面按键"""
    client_ip = get_client_ip(req) if req else "unknown"
    start_time = time.time()

    # hijack 确认
    detail = _build_detail(request, "desktop_press_key")
    if not _desktop_hijack_confirm(request, "Press Key", detail):
        return create_error_response("USER_DENIED", "User denied the operation")

    # 可选坐标：传了 x/y 则先点击定位再按键
    screen_x, screen_y = None, None
    if request.x is not None and request.y is not None:
        monitors = get_monitors()
        if request.monitor_index < 0 or request.monitor_index >= len(monitors):
            return create_error_response("MONITOR_NOT_FOUND")
        try:
            screen_x, screen_y = desktop_percent_to_screen(request.monitor_index, request.x, request.y)
        except IndexError:
            return create_error_response("MONITOR_NOT_FOUND")

    inject_result = desktop_press_key(request.keys, request.duration_ms, screen_x=screen_x, screen_y=screen_y)

    duration_ms = int((time.time() - start_time) * 1000)

    if inject_result.success:
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            window_id=None, process_name=None,
            instruction="desktop_press_key",
            params=request.model_dump(),
            result={"success": True, "message": "Key press succeeded."},
            duration_ms=duration_ms,
            client_ip=client_ip,
            monitor_index=request.monitor_index,
        )
        return BaseResponse(success=True, message="Command sent.")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)


# ============ 桌面悬浮 ============

@router.post("/desktop_hover")
async def desktop_hover_endpoint(
    request: DesktopHoverRequest,
    req: Request = None,
    authorization: str = Header(None)
):
    """桌面悬浮"""
    client_ip = get_client_ip(req) if req else "unknown"
    start_time = time.time()

    # hijack 确认
    detail = _build_detail(request, "desktop_hover")
    if not _desktop_hijack_confirm(request, "Hover", detail):
        return create_error_response("USER_DENIED", "User denied the operation")

    monitors = get_monitors()
    if request.monitor_index < 0 or request.monitor_index >= len(monitors):
        return create_error_response("MONITOR_NOT_FOUND")

    try:
        screen_x, screen_y = desktop_percent_to_screen(request.monitor_index, request.x, request.y)
    except IndexError:
        return create_error_response("MONITOR_NOT_FOUND")

    restore = not config_service.is_delegated_active()
    inject_result = desktop_hover(screen_x, screen_y, request.duration_ms, restore=restore)

    duration_ms = int((time.time() - start_time) * 1000)

    if inject_result.success:
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            window_id=None, process_name=None,
            instruction="desktop_hover",
            params=request.model_dump(),
            result={"success": True, "message": "Hover succeeded."},
            duration_ms=duration_ms,
            client_ip=client_ip,
            monitor_index=request.monitor_index,
        )
        return BaseResponse(success=True, message="Command sent.")
    else:
        return create_error_response("OPERATION_FAILED", inject_result.error)
