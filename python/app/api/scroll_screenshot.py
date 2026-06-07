"""
滚动长截图API
"""
import time
import os
import ctypes
from datetime import datetime
from fastapi import APIRouter, Header, Request

from app.models.request import ScrollScreenshotRequest
from app.models.response import (
    ScrollScreenshotResponse,
    ScrollScreenshotData,
    create_error_response
)
from app.services.config_service import config_service
from app.services.process_service import process_service
from app.services.log_service import log_service
from app.services.scroll_screenshot_service import ScrollScreenshotService, ScrollScreenshotResult
from app.utils.image import (
    image_to_base64,
    save_image,
    generate_data_dir,
    generate_scroll_screenshot_filename
)
from app.api.decorators import get_client_ip, with_verification, with_hijack_confirm, log_and_format

router = APIRouter()


def is_local_request(client_ip: str) -> bool:
    """判断是否为本地请求"""
    local_ips = {"127.0.0.1", "::1", "localhost"}
    return client_ip in local_ips


@router.post("/scroll_screenshot")
@with_verification
@with_hijack_confirm("Scroll screenshot", lambda r: f"Max scrolls: {r.max_scrolls}, Scroll percent: {r.scroll_percent * 100:.0f}%")
@log_and_format
async def scroll_screenshot(
    request: ScrollScreenshotRequest,
    req: Request = None,
    authorization: str = Header(None)
):
    """滚动长截图"""
    # 装饰器已注入：request.process_info, request.start_time, request.client_ip
    # 内部硬编码使用 hijack 模式

    # 1. 获取窗口信息
    process_info = process_service.get_process_by_window_id(request.window_id)
    if not process_info:
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            window_id=request.window_id,
            process_name="",
            instruction="scroll_screenshot",
            params={"window_id": request.window_id},
            result={"success": False, "message": "Window not found"},
        )
        return create_error_response("WINDOW_NOT_FOUND")

    # 3. 检查进程是否被禁止
    if config_service.is_process_blocked(process_info.process_name):
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            window_id=request.window_id,
            process_name=process_info.process_name,
            instruction="scroll_screenshot",
            params={"window_id": request.window_id},
            result={"success": False, "message": "Process is blocked"},
        )
        return create_error_response("PROCESS_BLOCKED")

    # 4. 恢复窗口（如果需要）
    if request.main_window_id:
        import win32gui
        import win32con
        import ctypes

        is_minimized = win32gui.IsIconic(request.main_window_id)
        is_visible = win32gui.IsWindowVisible(request.main_window_id)
        was_restored = False

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
            main_hwnd = request.main_window_id
            main_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
            current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
            ctypes.windll.user32.AttachThreadInput(current_tid, main_tid, True)
            win32gui.SetForegroundWindow(main_hwnd)
            ctypes.windll.user32.AttachThreadInput(current_tid, main_tid, False)
            ctypes.windll.user32.InvalidateRect(main_hwnd, None, True)
            win32gui.UpdateWindow(main_hwnd)
            time.sleep(0.5)  # 等待窗口稳定渲染

    # 5. 计算滚动坐标（不恢复窗口，前面已经恢复了）
    scroll_x = request.x or 50
    scroll_y = request.y or 50

    # 获取窗口矩形并计算虚拟坐标
    window_rect = process_service.get_window_rect(request.window_id)
    if not window_rect:
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            window_id=request.window_id,
            process_name=process_info.process_name if process_info else "",
            instruction="scroll_screenshot",
            params={"window_id": request.window_id},
            result={"success": False, "message": "Cannot get window rect"},
            client_ip=request.client_ip
        )
        return create_error_response("INTERNAL_ERROR", "Cannot get window rect")

    virtual_width = window_rect[2] - window_rect[0]
    virtual_height = window_rect[3] - window_rect[1]
    scroll_virtual_x = int(virtual_width * scroll_x / 100)
    scroll_virtual_y = int(virtual_height * scroll_y / 100)

    # 5. 获取配置并执行滚动截图
    config = config_service.get()
    service = ScrollScreenshotService(config.scroll_screenshot)

    # 用 config.json 的默认值填充请求中缺失的参数
    from pydantic import BaseModel
    request_data = request.model_dump()

    # 填充缺失的参数（None 或缺失时使用 config 值）
    if request_data.get('max_scrolls') is None:
        request_data['max_scrolls'] = config.scroll_screenshot.max_scrolls
    if request_data.get('scroll_percent') is None:
        request_data['scroll_percent'] = config.scroll_screenshot.default_scroll_percent
    if request_data.get('scroll_wait') is None:
        request_data['scroll_wait'] = config.scroll_screenshot.default_scroll_wait
    if request_data.get('max_adjust_retries') is None:
        request_data['max_adjust_retries'] = config.scroll_screenshot.max_adjust_retries
    if request_data.get('target_overlap_min') is None:
        request_data['target_overlap_min'] = config.scroll_screenshot.target_overlap_min
    if request_data.get('target_overlap_max') is None:
        request_data['target_overlap_max'] = config.scroll_screenshot.target_overlap_max
    if request_data.get('stop_threshold') is None:
        request_data['stop_threshold'] = config.scroll_screenshot.stop_threshold

    # 重新构建请求对象（使用填充后的值）
    filled_request = ScrollScreenshotRequest(**request_data)

    result = service.execute(filled_request, request.window_id, scroll_virtual_x, scroll_virtual_y)

    # 6. 处理结果
    duration_ms = int((time.time() - request.start_time) * 1000)

    if result.success and result.image:
        result_image = result.image

        # 保存图片
        data_dir = generate_data_dir("data", request.ai_app_type, request.session_id)
        filename = generate_scroll_screenshot_filename()
        image_path = os.path.join(data_dir, filename)

        save_image(result_image, image_path, config.scroll_screenshot.image_quality)

        # 本地请求只返回路径，远程请求只返回 base64
        is_local = is_local_request(request.client_ip)

        if is_local:
            response_data = ScrollScreenshotData(
                image_path=os.path.abspath(image_path),
                image_base64=None,
                scroll_count=result.scroll_count,
                actual_scroll_percent=result.actual_scroll_percent,
                fixed_header=result.fixed_header,
                fixed_footer=result.fixed_footer
            )
        else:
            image_base64 = image_to_base64(result_image)
            response_data = ScrollScreenshotData(
                image_path=None,
                image_base64=image_base64,
                scroll_count=result.scroll_count,
                actual_scroll_percent=result.actual_scroll_percent,
                fixed_header=result.fixed_header,
                fixed_footer=result.fixed_footer
            )

        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            window_id=request.window_id,
            process_name=process_info.process_name,
            instruction="scroll_screenshot",
            params={
                "max_scrolls": request.max_scrolls,
                "scroll_percent": request.scroll_percent,
                "scroll_wait": request.scroll_wait
            },
            result={
                "success": True,
                "scroll_count": result.scroll_count,
                "image_path": image_path
            },
            duration_ms=duration_ms,
        )

        return ScrollScreenshotResponse(
            success=True,
            message=result.message,
            data=response_data
        )
    else:
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            window_id=request.window_id,
            process_name=process_info.process_name,
            instruction="scroll_screenshot",
            params={
                "max_scrolls": request.max_scrolls,
                "scroll_percent": request.scroll_percent,
                "scroll_wait": request.scroll_wait
            },
            result={"success": False, "message": result.message},
            duration_ms=duration_ms,
        )

        return ScrollScreenshotResponse(
            success=False,
            message=result.message,
            data=None
        )
