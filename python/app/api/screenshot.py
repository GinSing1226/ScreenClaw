"""
截图API
"""
import time
import os
from fastapi import APIRouter, Header, Request

from app.models.request import ScreenshotRequest
from app.models.response import (
    ScreenshotResponse,
    ScreenshotData,
    create_error_response
)
from app.services.config_service import config_service
from app.services.process_service import process_service
from app.services.log_service import log_service
from app.services.screenshot_params_service import screenshot_params_service
from app.services.self_check_service import self_check_service
from app.platform.windows.capture import windows_capture
from app.core.grid import GridRenderer
from app.utils.image import (
    compress_image,
    image_to_base64,
    save_image,
    generate_screenshot_filename,
    generate_data_dir
)
from app.api.decorators import get_client_ip
import win32gui
import win32con
import time

router = APIRouter()


def is_local_request(client_ip: str) -> bool:
    """判断是否为本地请求（只有本机进程能访问文件路径）"""
    local_ips = {"127.0.0.1", "::1", "localhost"}
    return client_ip in local_ips


def _marker_dump(marker):
    if not marker:
        return None
    return [m.model_dump() for m in marker]


def _requested_screenshot_params(request: ScreenshotRequest, config) -> dict:
    params = request.model_dump(exclude={"self_check"}, exclude_none=True)
    params["image_quality"] = config.screenshot.image_quality
    params["max_image_width"] = config.screenshot.max_image_width
    return params


def _effective_screenshot_params(
    request: ScreenshotRequest,
    config,
    image_size,
    color_mode,
    effective_grid,
    effective_coordinate,
    effective_marker,
) -> dict:
    params = {
        "ai_app_type": request.ai_app_type,
        "session_id": request.session_id,
        "window_id": request.window_id,
        "main_window_id": request.main_window_id,
        "coordinate_type": request.coordinate_type,
        "color_mode": color_mode or request.color_mode or config.screenshot.default_color_mode,
        "image_quality": config.screenshot.image_quality,
        "max_image_width": config.screenshot.max_image_width,
        "output_size": {"width": image_size[0], "height": image_size[1]},
    }
    if effective_grid:
        params["grid"] = effective_grid
    if effective_coordinate:
        params["coordinate"] = effective_coordinate
    if effective_marker:
        params["marker"] = effective_marker
    return params


@router.post("/screenshot")
async def take_screenshot(
    request: ScreenshotRequest,
    req: Request = None,
    authorization: str = Header(None)
):
    """截图"""
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
            instruction="screenshot",
            params=request.model_dump(exclude={"self_check"}),
            result={"success": False, "message": "Window not found"},
            client_ip=client_ip
        )
        return create_error_response("WINDOW_NOT_FOUND")

    # 检查进程是否被禁止
    if config_service.is_process_blocked(process_info.process_name):
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            window_id=request.window_id,
            process_name=process_info.process_name,
            instruction="screenshot",
            params=request.model_dump(exclude={"self_check"}),
            result={"success": False, "message": "Process is blocked"},
            client_ip=client_ip
        )
        return create_error_response("PROCESS_BLOCKED")

    config = config_service.get()
    self_check_result = self_check_service.validate_before_screenshot(
        request.session_id,
        request.self_check,
        config.self_check
    )
    if not self_check_result.ok:
        return self_check_result.response

    # 恢复窗口（如果需要）
    if request.main_window_id:
        is_minimized = win32gui.IsIconic(request.main_window_id)
        is_visible = win32gui.IsWindowVisible(request.main_window_id)
        was_restored = False  # 标记是否做了恢复操作

        if is_minimized:
            win32gui.ShowWindow(request.main_window_id, win32con.SW_RESTORE)
            # 等待恢复完成
            start = time.time()
            while time.time() - start < 2.0:
                if win32gui.IsWindowVisible(request.main_window_id) and not win32gui.IsIconic(request.main_window_id):
                    was_restored = True
                    break
                time.sleep(0.01)

        elif not is_visible:
            win32gui.ShowWindow(request.main_window_id, win32con.SW_SHOW)
            was_restored = True

        # 仅在窗口从最小化/隐藏恢复时，强制激活+重绘
        if was_restored:
            import ctypes
            main_hwnd = request.main_window_id
            main_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
            current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
            ctypes.windll.user32.AttachThreadInput(current_tid, main_tid, True)
            win32gui.SetForegroundWindow(main_hwnd)
            ctypes.windll.user32.AttachThreadInput(current_tid, main_tid, False)
            ctypes.windll.user32.InvalidateRect(main_hwnd, None, True)
            win32gui.UpdateWindow(main_hwnd)
            time.sleep(0.5)  # 等待窗口稳定渲染

    # 截图
    result = windows_capture.capture(request.window_id)
    if not result.success or result.image is None:
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            window_id=request.window_id,
            process_name=process_info.process_name,
            instruction="screenshot",
            params=request.model_dump(exclude={"self_check"}),
            result={"success": False, "message": result.error},
            client_ip=client_ip
        )
        return create_error_response("SCREENSHOT_FAILED", result.error)

    image = result.image

    # 压缩图片（先压缩到最终输出尺寸，再绘制网格/标记）
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

    # 绘制标记（独立于网格，任何 coordinate_type 下都可绘制）
    if request.marker:
        renderer = GridRenderer() if renderer is None else renderer
        for m in request.marker:
            image = renderer.draw_marker(
                image,
                x=m.x,
                y=m.y,
                ring_radius=m.ring_radius,
                ring_line_width=m.ring_line_width,
                ring_color=m.ring_color,
                dot_radius=m.dot_radius,
                dot_color=m.dot_color
            )

    # 保存图片（使用 session_id 组织目录，不区分窗口）
    data_dir = generate_data_dir("data", request.ai_app_type, request.session_id)
    filename = generate_screenshot_filename()
    image_path = os.path.join(data_dir, filename)
    save_image(image, image_path, config.screenshot.image_quality)

    # 转换为base64
    image_base64 = image_to_base64(image)

    # 计算耗时
    duration_ms = int((time.time() - start_time) * 1000)

    notice = self_check_service.record_screenshot_success(
        request.session_id,
        config.self_check,
        units=1
    )
    _ = notice

    # 本地请求只返回路径，远程请求只返回base64
    is_local = is_local_request(client_ip)
    requested_params = _requested_screenshot_params(request, config)
    effective_marker = _marker_dump(request.marker)
    effective_params = _effective_screenshot_params(
        request,
        config,
        image.size,
        effective_color_mode,
        effective_grid,
        effective_coordinate,
        effective_marker,
    )
    if is_local:
        # 本地：只返回路径，减少上下文
        screenshot_data = ScreenshotData(
            image_path=os.path.abspath(image_path),
            requested_params=requested_params,
            effective_params=effective_params,
            effective_grid=effective_grid,
            effective_coordinate=effective_coordinate,
            effective_marker=effective_marker,
            adaptive_adjustments=adaptive_adjustments
        )
    else:
        # 远程：只返回base64
        screenshot_data = ScreenshotData(
            image_base64=image_base64,
            requested_params=requested_params,
            effective_params=effective_params,
            effective_grid=effective_grid,
            effective_coordinate=effective_coordinate,
            effective_marker=effective_marker,
            adaptive_adjustments=adaptive_adjustments
        )

    # 成功消息
    success_message = "Screenshot successful."
    if request.marker:
        success_message += " Marker drawn."

    # 记录日志
    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        window_id=request.window_id,
        process_name=process_info.process_name,
        instruction="screenshot",
        params=request.model_dump(exclude={"self_check"}),
        result={
            "success": True,
            "message": success_message,
            "data": screenshot_data.model_dump(exclude={"image_base64"})
        },
        duration_ms=duration_ms,
        client_ip=client_ip
    )

    return ScreenshotResponse(
        success=True,
        message=success_message,
        data=screenshot_data
    )
