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
            params={
                "window_id": request.window_id,
                "main_window_id": request.main_window_id,
                "coordinate_type": request.coordinate_type,
                "grid": request.grid.model_dump() if request.grid else None,
                "coordinate": request.coordinate.model_dump() if request.coordinate else None
            },
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
            params={
                "window_id": request.window_id,
                "main_window_id": request.main_window_id,
                "coordinate_type": request.coordinate_type,
                "grid": request.grid.model_dump() if request.grid else None,
                "coordinate": request.coordinate.model_dump() if request.coordinate else None
            },
            result={"success": False, "message": "Process is blocked"},
            client_ip=client_ip
        )
        return create_error_response("PROCESS_BLOCKED")

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
            params={
                "window_id": request.window_id,
                "main_window_id": request.main_window_id,
                "coordinate_type": request.coordinate_type,
                "grid": request.grid.model_dump() if request.grid else None,
                "coordinate": request.coordinate.model_dump() if request.coordinate else None
            },
            result={"success": False, "message": result.error},
            client_ip=client_ip
        )
        return create_error_response("SCREENSHOT_FAILED", result.error)

    image = result.image

    # 绘制网格
    if request.coordinate_type != "no":
        config = config_service.get()

        # 使用请求参数或默认值
        grid_density = request.grid.density if request.grid else config.screenshot.default_grid_density
        grid_opacity = request.grid.opacity if request.grid else config.screenshot.default_grid_opacity
        grid_color = request.grid.color if request.grid else config.screenshot.default_grid_color

        coord = request.coordinate
        number_density = coord.number_density if coord else config.screenshot.default_number_density
        number_decimal = coord.number_decimal if coord else config.screenshot.default_number_decimal
        number_size = coord.number_size if coord else config.screenshot.default_number_size
        number_color = coord.number_color if coord else config.screenshot.default_number_color
        number_opacity = coord.number_opacity if coord else config.screenshot.default_number_opacity

        # color_mode: 请求参数 > 配置默认值
        color_mode = request.color_mode or config.screenshot.default_color_mode

        # 调试：打印参数
        print(f"[Screenshot] number_size={number_size} (from request={coord.number_size if coord else None})")
        print(f"[Screenshot] number_density={number_density}, number_decimal={number_decimal}, color_mode={color_mode}")

        renderer = GridRenderer(
            density=grid_density,
            grid_opacity=grid_opacity,
            grid_color=grid_color,
            number_density=number_density,
            number_decimal=number_decimal,
            number_size=number_size,
            number_color=number_color,
            number_opacity=number_opacity,
            color_mode=color_mode
        )
        image = renderer.draw_grid(image)

    # 压缩图片
    config = config_service.get()
    image = compress_image(
        image,
        quality=config.screenshot.image_quality,
        max_width=config.screenshot.max_image_width
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

    # 记录日志
    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        window_id=request.window_id,
        process_name=process_info.process_name,
        instruction="screenshot",
        params={
            "window_id": request.window_id,
            "main_window_id": request.main_window_id,
            "coordinate_type": request.coordinate_type,
            "grid": request.grid.model_dump() if request.grid else None,
            "coordinate": request.coordinate.model_dump() if request.coordinate else None
        },
        result={"success": True, "image_path": image_path},
        duration_ms=duration_ms,
        client_ip=client_ip
    )

    # 本地请求只返回路径，远程请求只返回base64
    is_local = is_local_request(client_ip)
    if is_local:
        # 本地：只返回路径，减少上下文
        screenshot_data = ScreenshotData(image_path=os.path.abspath(image_path))
    else:
        # 远程：只返回base64
        screenshot_data = ScreenshotData(image_base64=image_base64)

    return ScreenshotResponse(
        success=True,
        message="Screenshot successful",
        data=screenshot_data
    )
