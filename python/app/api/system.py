"""
系统API - 健康检查、组合指令
"""
import time
from fastapi import APIRouter, Header, Request

from app.models.request import BatchRequest
from app.models.response import (
    HealthResponse,
    HealthData,
    BatchResponse,
    BatchData,
    InstructionResult,
    create_error_response
)
from app.services.log_service import log_service
from app.utils.coordinate import restore_window_and_calc_coords

router = APIRouter()

# 服务启动时间
START_TIME = time.time()


@router.get("/health")
async def health_check():
    """健康检查"""
    uptime = int(time.time() - START_TIME)

    return HealthResponse(
        success=True,
        message="Service OK",
        data=HealthData(
            version="1.0.0",
            uptime_seconds=uptime
        )
    )


@router.post("/batch")
async def batch_execute(request: BatchRequest, req: Request = None, authorization: str = Header(None)):
    """组合指令"""
    from app.services.process_service import process_service

    client_ip = req.client.host if req and req.client else "unknown"

    start_time = time.time()
    results = []
    executed_count = 0
    failed_index = None

    for i, instruction in enumerate(request.instructions):
        # 执行单条指令
        is_last = (i == len(request.instructions) - 1)
        result = await _execute_single_instruction(
            request.ai_app_type,
            request.session_id,
            request.window_id,
            instruction,
            request.main_window_id,
            is_last,
            client_ip
        )

        results.append(InstructionResult(
            success=result["success"],
            message=result["message"],
            data=result.get("data")
        ))

        if result["success"]:
            executed_count += 1
        else:
            # 失败时中断
            failed_index = i
            break

    duration_ms = int((time.time() - start_time) * 1000)

    # 获取进程名（用于日志显示）
    process_info = process_service.get_process_by_window_id(request.window_id)
    process_name = process_info.process_name if process_info else ""

    # 记录日志
    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        window_id=request.window_id,
        process_name=process_name,
        instruction="batch",
        params={"count": len(request.instructions)},
        result={
            "success": failed_index is None,
            "executed_count": executed_count,
            "failed_index": failed_index
        },
        duration_ms=duration_ms,
        client_ip=client_ip
    )

    if failed_index is not None:
        return BatchResponse(
            success=False,
            message=f"Execution interrupted at instruction{failed_index + 1}  failed",
            data=BatchData(
                executed_count=executed_count,
                failed_index=failed_index,
                results=results
            )
        )

    return BatchResponse(
        success=True,
        message="Execution completed",
        data=BatchData(
            executed_count=executed_count,
            failed_index=None,
            results=results
        )
    )


async def _execute_single_instruction(
    ai_app_type: str,
    session_id: str,
    window_id: int,
    instruction,
    main_window_id: int = None,
    is_last: bool = False,
    client_ip: str = "unknown"
) -> dict:
    """执行单条指令"""
    from app.services.process_service import process_service
    from app.platform.windows.input import windows_input
    from app.services.config_service import config_service
    from app.services.confirm_service import ConfirmService
    from ctypes import windll
    import win32gui

    action = instruction.action
    params = instruction.params
    action_method = params.get("action_method", "background")

    # 成功消息：最后一步提示可截图验证
    _success_msg = "指令已发送，可截图验证结果" if is_last else "指令已发送"

    # 获取进程信息（所有模式都需要，用于禁止检查）
    process_info = process_service.get_process_by_window_id(window_id)
    if not process_info:
        return {"success": False, "message": "Window not found"}

    # 检查进程是否被禁止（所有模式都生效）
    if config_service.is_process_blocked(process_info.process_name):
        return {"success": False, "message": "Process is blocked"}

    # hijack 模式需要用户确认
    if action_method == "hijack":
        try:
            window_title = win32gui.GetWindowText(window_id) or "未知窗口"
        except Exception:
            window_title = "未知窗口"

        # 生成操作描述
        operation_map = {
            "click": "点击",
            "long_press": "长按",
            "swipe": "滑动",
            "scroll": "滚动",
            "right_click": "右键点击",
            "hover": "鼠标悬浮",
            "input_text": "输入文本",
            "press_key": "按键"
        }
        operation = operation_map.get(action, action)

        # 生成操作详情
        detail_parts = []
        if action in ["click", "right_click"]:
            detail_parts.append(f"坐标: ({params.get('x', 0)}, {params.get('y', 0)})")
        elif action == "long_press":
            detail_parts.append(f"坐标: ({params.get('x', 0)}, {params.get('y', 0)})")
            detail_parts.append(f"时长: {params.get('duration_ms', 500)}ms")
        elif action == "hover":
            detail_parts.append(f"坐标: ({params.get('x', 0)}, {params.get('y', 0)})")
            detail_parts.append(f"停留: {params.get('duration_ms', 500)}ms")
        elif action == "swipe":
            detail_parts.append(f"从 ({params.get('start_x', 0)}, {params.get('start_y', 0)}) 到 ({params.get('end_x', 0)}, {params.get('end_y', 0)})")
        elif action == "scroll":
            detail_parts.append(f"滚动量: {params.get('delta', 0)}")
        elif action == "input_text":
            text = params.get("text", "")
            text_preview = text[:50] + "..." if len(text) > 50 else text
            detail_parts.append(f"输入: {text_preview}")
        elif action == "press_key":
            detail_parts.append(f"按键: {params.get('key', '')}")

        operation_detail = ", ".join(detail_parts) if detail_parts else operation

        # 请求用户确认
        print(f"[BatchConfirm] Requesting confirm for operation={operation}, detail={operation_detail}")
        confirm_result = ConfirmService.request_confirm(
            ai_app_type=ai_app_type,
            window_title=window_title,
            process_name=process_info.process_name,
            operation=operation,
            operation_detail=operation_detail
        )
        print(f"[BatchConfirm] Confirm result: confirmed={confirm_result.confirmed}, remember={confirm_result.remember}")

        if not confirm_result.confirmed:
            return {"success": False, "message": "User denied"}

    def _calc(x_pct, y_pct, main_window_id=None):
        """DPI感知坐标计算（调用公共函数）"""
        return restore_window_and_calc_coords(window_id, x_pct, y_pct, main_window_id)

    try:
        if action == "click":
            c = _calc(params["x"], params["y"], main_window_id)
            if not c:
                return {"success": False, "message": "Cannot get window rectangle"}
            r = windows_input.click(window_id, c[0], c[1], c[2], c[3], action_method)
            return {"success": r.success, "message": r.error or _success_msg}

        elif action == "long_press":
            c = _calc(params["x"], params["y"], main_window_id)
            if not c:
                return {"success": False, "message": "Cannot get window rectangle"}
            dur = params.get("duration_ms", 500)
            r = windows_input.long_press(window_id, c[0], c[1], c[2], c[3], dur, action_method)
            return {"success": r.success, "message": r.error or _success_msg}

        elif action == "swipe":
            cs = _calc(params["start_x"], params["start_y"])
            ce = _calc(params["end_x"], params["end_y"])
            if not cs or not ce:
                return {"success": False, "message": "Cannot get window rectangle"}
            r = windows_input.swipe(window_id, cs[0], cs[1], ce[0], ce[1],
                                    cs[2], cs[3], ce[2], ce[3], action_method)
            return {"success": r.success, "message": r.error or _success_msg}

        elif action == "scroll":
            c = _calc(params["x"], params["y"], main_window_id)
            if not c:
                return {"success": False, "message": "Cannot get window rectangle"}
            r = windows_input.scroll(window_id, c[0], c[1], c[2], c[3],
                                     params["delta"], action_method)
            return {"success": r.success, "message": r.error or _success_msg}

        elif action == "right_click":
            c = _calc(params["x"], params["y"], main_window_id)
            if not c:
                return {"success": False, "message": "Cannot get window rectangle"}
            r = windows_input.right_click(window_id, c[0], c[1], c[2], c[3], action_method)
            return {"success": r.success, "message": r.error or _success_msg}

        elif action == "hover":
            c = _calc(params["x"], params["y"], main_window_id)
            if not c:
                return {"success": False, "message": "Cannot get window rectangle"}
            dur = params.get("duration_ms", 500)
            r = windows_input.hover(window_id, c[0], c[1], c[2], c[3], dur, action_method)
            return {"success": r.success, "message": r.error or _success_msg}

        elif action == "input_text":
            x_pct = params.get("x")
            y_pct = params.get("y")

            px = py = vx = vy = None
            if x_pct is not None and y_pct is not None:
                c = _calc(x_pct, y_pct)
                if c:
                    px, py, vx, vy = c

            r = windows_input.input_text(window_id, px, py, vx, vy,
                                          params["text"], action_method)
            return {"success": r.success, "message": r.error or _success_msg}

        elif action == "press_key":
            x_pct = params.get("x")
            y_pct = params.get("y")
            dur = params.get("duration_ms", 0)

            px = py = vx = vy = None
            if x_pct is not None and y_pct is not None:
                c = _calc(x_pct, y_pct)
                if c:
                    px, py, vx, vy = c

            # duration_ms > 0: 非阻塞，按下后立即继续下一条指令
            non_blocking = dur > 0

            r = windows_input.key_press(
                window_id, params["key"],
                physical_x=px, physical_y=py,
                virtual_x=vx, virtual_y=vy,
                duration_ms=dur,
                action_method=action_method,
                non_blocking=non_blocking
            )

            if non_blocking:
                return {"success": True, "message": _success_msg}
            return {"success": r.success, "message": r.error or _success_msg}

        elif action == "wait":
            dur = params.get("duration_ms", 1000)
            time.sleep(dur / 1000)
            return {"success": True, "message": "Wait completed"}

        elif action == "screenshot":
            from app.platform.windows.capture import windows_capture
            from app.core.grid import GridRenderer
            from app.utils.image import compress_image, image_to_base64, save_image
            from app.utils.image import generate_screenshot_filename, generate_data_dir
            from app.services.config_service import config_service
            import os

            # 判断是否为本地请求（只有本机进程能访问文件路径）
            def is_local_request(ip: str) -> bool:
                local_ips = {"127.0.0.1", "::1", "localhost"}
                return ip in local_ips

            # 截图
            result = windows_capture.capture(window_id)
            if not result.success or result.image is None:
                return {"success": False, "message": result.error}

            image = result.image

            # 绘制网格（根据指令参数）
            coord_type = params.get("coordinate_type", "grid")
            if coord_type != "no":
                config = config_service.get()

                grid_params = params.get("grid", {})
                grid_density = grid_params.get("density", config.screenshot.default_grid_density)
                grid_opacity = grid_params.get("opacity", config.screenshot.default_grid_opacity)
                grid_color = grid_params.get("color", config.screenshot.default_grid_color)

                coord_params = params.get("coordinate", {})
                number_density = coord_params.get("number_density", config.screenshot.default_number_density)
                number_decimal = coord_params.get("number_decimal", config.screenshot.default_number_decimal)
                number_size = coord_params.get("number_size", config.screenshot.default_number_size)
                number_color = coord_params.get("number_color", config.screenshot.default_number_color)
                number_opacity = coord_params.get("number_opacity", config.screenshot.default_number_opacity)

                renderer = GridRenderer(
                    density=grid_density,
                    grid_opacity=grid_opacity,
                    grid_color=grid_color,
                    number_density=number_density,
                    number_decimal=number_decimal,
                    number_size=number_size,
                    number_color=number_color,
                    number_opacity=number_opacity
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
            data_dir = generate_data_dir("data", ai_app_type, session_id)
            filename = generate_screenshot_filename()
            image_path = os.path.join(data_dir, filename)
            save_image(image, image_path, config.screenshot.image_quality)

            # 转换为base64
            image_base64 = image_to_base64(image)

            # 本地请求只返回路径，远程请求只返回base64
            is_local = is_local_request(client_ip)
            if is_local:
                result_data = {"image_path": os.path.abspath(image_path)}
            else:
                result_data = {"image_base64": image_base64}

            return {
                "success": True,
                "message": "Screenshot completed",
                "data": result_data
            }

        else:
            return {"success": False, "message": f"Unknown instruction type: {action}"}

    except Exception as e:
        return {"success": False, "message": str(e)}
