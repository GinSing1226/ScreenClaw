"""
系统API - 健康检查、组合指令
"""
import random
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


@router.get("/health")
async def health_check():
    """健康检查"""
    server_time = time.strftime("%Y-%m-%d %H:%M:%S")

    return HealthResponse(
        success=True,
        message="Service OK",
        data=HealthData(
            server_time=server_time
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
        params={
            "instructions": [
                {"action": inst.action, "params": inst.params}
                for inst in request.instructions
            ]
        },
        result={
            "success": failed_index is None,
            "executed_count": executed_count,
            "failed_index": failed_index
        },
        duration_ms=duration_ms,
        client_ip=client_ip
    )

    if failed_index is not None:
        failed_action = request.instructions[failed_index].action
        failed_msg = results[failed_index].message
        return BatchResponse(
            success=False,
            message=f"Execution interrupted at instruction {failed_index + 1} ({failed_action}) failed: {failed_msg}",
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

    # 托管模式下强制转为物理操作，跳过确认
    delegated_active = config_service.is_delegated_active()
    if delegated_active:
        action_method = "delegated"

    # 成功消息：最后一步提示可截图验证
    _success_msg = "Command sent. Take a screenshot to verify. If result is unsatisfactory, refer to skill.md for parameter tuning." if is_last else "Command sent"

    # 获取进程信息（所有模式都需要，用于禁止检查）
    process_info = process_service.get_process_by_window_id(window_id)
    if not process_info:
        return {"success": False, "message": "Window not found. The window may have been closed. Use get_window_list to get a valid window_id. Refer to skill.md for troubleshooting."}

    # 检查进程是否被禁止（所有模式都生效）
    if config_service.is_process_blocked(process_info.process_name):
        return {"success": False, "message": "Process is blocked. This process is in the blocked list and operations are not allowed. Refer to skill.md for troubleshooting."}

    # hijack 模式需要用户确认（托管模式下跳过）
    if action_method == "hijack":
        try:
            window_title = win32gui.GetWindowText(window_id) or "Unknown window"
        except Exception:
            window_title = "Unknown window"

        # 生成操作描述
        operation_map = {
            "click": "Click",
            "long_press": "Long press",
            "swipe": "Swipe",
            "drag": "Drag",
            "mouse_move": "Mouse move",
            "scroll": "Scroll",
            "right_click": "Right-click",
            "hover": "Hover",
            "input_text": "Input text",
            "press_key": "Press key"
        }
        operation = operation_map.get(action, action)

        # 生成操作详情
        detail_parts = []
        if action in ["click", "right_click"]:
            detail_parts.append(f"Coordinates: ({params.get('x', 0)}, {params.get('y', 0)})")
        elif action == "long_press":
            detail_parts.append(f"Coordinates: ({params.get('x', 0)}, {params.get('y', 0)})")
            detail_parts.append(f"Duration: {params.get('duration_ms', 500)}ms")
        elif action == "hover":
            detail_parts.append(f"Coordinates: ({params.get('x', 0)}, {params.get('y', 0)})")
            detail_parts.append(f"Stay: {params.get('duration_ms', 500)}ms")
        elif action == "swipe":
            detail_parts.append(f"From ({params.get('start_x', 0)}, {params.get('start_y', 0)}) to ({params.get('end_x', 0)}, {params.get('end_y', 0)})")
        elif action == "drag":
            detail_parts.append(f"From ({params.get('start_x', 0)}, {params.get('start_y', 0)}) to ({params.get('end_x', 0)}, {params.get('end_y', 0)})")
            detail_parts.append(f"Duration: {params.get('duration_ms', 500)}ms")
            target_wid = params.get("target_window_id")
            if target_wid and target_wid != window_id:
                detail_parts.append(f"[CROSS-PROCESS: window {window_id} -> {target_wid}]")
        elif action == "mouse_move":
            detail_parts.append(f"Delta: ({params.get('delta_x', 0)}, {params.get('delta_y', 0)})")
            detail_parts.append(f"Duration: {params.get('duration_ms', 300)}ms")
        elif action == "scroll":
            detail_parts.append(f"Delta: {params.get('delta', 0)}")
        elif action == "input_text":
            text = params.get("text", "")
            text_preview = text[:50] + "..." if len(text) > 50 else text
            detail_parts.append(f"Text: {text_preview}")
        elif action == "press_key":
            detail_parts.append(f"Key: {params.get('key', '')}")

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
                return {"success": False, "message": "Cannot get window rectangle. The window may have been closed or minimized. Refer to skill.md for troubleshooting."}
            r = windows_input.click(window_id, c[0], c[1], c[2], c[3], action_method)
            return {"success": r.success, "message": r.error or _success_msg}

        elif action == "long_press":
            c = _calc(params["x"], params["y"], main_window_id)
            if not c:
                return {"success": False, "message": "Cannot get window rectangle. The window may have been closed or minimized. Refer to skill.md for troubleshooting."}
            dur = params.get("duration_ms", 500)
            r = windows_input.long_press(window_id, c[0], c[1], c[2], c[3], dur, action_method)
            return {"success": r.success, "message": r.error or _success_msg}

        elif action == "swipe":
            cs = _calc(params["start_x"], params["start_y"], main_window_id)
            ce = _calc(params["end_x"], params["end_y"], main_window_id)
            if not cs or not ce:
                return {"success": False, "message": "Cannot get window rectangle. The window may have been closed or minimized. Refer to skill.md for troubleshooting."}
            r = windows_input.swipe(window_id, cs[0], cs[1], ce[0], ce[1],
                                    cs[2], cs[3], ce[2], ce[3], action_method)
            return {"success": r.success, "message": r.error or _success_msg}

        elif action == "drag":
            target_window_id = params.get("target_window_id")
            target_main_window_id = params.get("target_main_window_id")
            is_cross_process = (target_window_id is not None and target_window_id != window_id)

            cs = _calc(params["start_x"], params["start_y"], main_window_id)
            if not cs:
                return {"success": False, "message": "Cannot get source window rectangle. The window may have been closed or minimized. Refer to skill.md for troubleshooting."}

            if is_cross_process:
                ce = restore_window_and_calc_coords(
                    target_window_id, params["end_x"], params["end_y"], target_main_window_id
                )
                action_method = "hijack"
            else:
                ce = _calc(params["end_x"], params["end_y"], main_window_id)

            if not ce:
                return {"success": False, "message": "Cannot get target window rectangle. The window may have been closed or minimized. Refer to skill.md for troubleshooting."}

            dur = params.get("duration_ms", 500)
            r = windows_input.drag(
                window_id, cs[0], cs[1], ce[0], ce[1],
                cs[2], cs[3], ce[2], ce[3], dur, action_method,
                target_hwnd=target_window_id if is_cross_process else None
            )
            return {"success": r.success, "message": r.error or _success_msg}

        elif action == "mouse_move":
            dur = params.get("duration_ms", 300)
            am = params.get("action_method", "hijack")
            r = windows_input.mouse_move(window_id, params["delta_x"], params["delta_y"], dur, am)
            return {"success": r.success, "message": r.error or _success_msg}

        elif action == "scroll":
            c = _calc(params["x"], params["y"], main_window_id)
            if not c:
                return {"success": False, "message": "Cannot get window rectangle. The window may have been closed or minimized. Refer to skill.md for troubleshooting."}
            r = windows_input.scroll(window_id, c[0], c[1], c[2], c[3],
                                     params["delta"], action_method)
            return {"success": r.success, "message": r.error or _success_msg}

        elif action == "right_click":
            c = _calc(params["x"], params["y"], main_window_id)
            if not c:
                return {"success": False, "message": "Cannot get window rectangle. The window may have been closed or minimized. Refer to skill.md for troubleshooting."}
            r = windows_input.right_click(window_id, c[0], c[1], c[2], c[3], action_method)
            return {"success": r.success, "message": r.error or _success_msg}

        elif action == "hover":
            c = _calc(params["x"], params["y"], main_window_id)
            if not c:
                return {"success": False, "message": "Cannot get window rectangle. The window may have been closed or minimized. Refer to skill.md for troubleshooting."}
            dur = params.get("duration_ms", 500)
            r = windows_input.hover(window_id, c[0], c[1], c[2], c[3], dur, action_method)
            return {"success": r.success, "message": r.error or _success_msg}

        elif action == "input_text":
            from app.api.input import decode_unicode_escapes

            x_pct = params.get("x")
            y_pct = params.get("y")

            px = py = vx = vy = None
            if x_pct is not None and y_pct is not None:
                c = _calc(x_pct, y_pct, main_window_id)
                if c:
                    px, py, vx, vy = c

            raw_newline_key = params.get("newline_key")
            final_newline_key = raw_newline_key or "shift enter"

            decoded_text = decode_unicode_escapes(params["text"])

            r = windows_input.input_text(
                window_id, px, py, vx, vy,
                decoded_text,
                newline_key=final_newline_key,
                action_method=action_method
            )
            return {"success": r.success, "message": r.error or _success_msg}

        elif action == "press_key":
            x_pct = params.get("x")
            y_pct = params.get("y")
            dur = params.get("duration_ms", 0)

            px = py = vx = vy = None
            if x_pct is not None and y_pct is not None:
                c = _calc(x_pct, y_pct, main_window_id)
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
            rr = params.get("random_range", 0)
            if rr > 0:
                low = max(1, dur - rr)
                high = dur + rr
                actual = random.randint(low, high)
            else:
                actual = dur
            time.sleep(actual / 1000)
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
                grid_density_x = grid_params.get("density_x", config.screenshot.default_grid_density)
                grid_density_y = grid_params.get("density_y", config.screenshot.default_grid_density)
                grid_opacity = grid_params.get("opacity", config.screenshot.default_grid_opacity)
                grid_color = grid_params.get("color", config.screenshot.default_grid_color)

                coord_params = params.get("coordinate", {})
                number_density = coord_params.get("number_density", config.screenshot.default_number_density)
                number_decimal = coord_params.get("number_decimal", config.screenshot.default_number_decimal)
                number_size = coord_params.get("number_size", config.screenshot.default_number_size)
                number_color = coord_params.get("number_color", config.screenshot.default_number_color)
                number_opacity = coord_params.get("number_opacity", config.screenshot.default_number_opacity)

                # color_mode: 请求参数 > 配置默认值
                color_mode = params.get("color_mode") or config.screenshot.default_color_mode

                renderer = GridRenderer(
                    density_x=grid_density_x,
                    density_y=grid_density_y,
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

            # 绘制标记（根据指令参数）
            marker_params = params.get("marker")
            if marker_params:
                # 支持单个对象或数组
                marker_list = marker_params if isinstance(marker_params, list) else [marker_params]
                for mp in marker_list:
                    if "x" not in mp or "y" not in mp:
                        return {"success": False, "message": "Marker requires both x and y"}
                config = config_service.get()
                # 确保有 renderer 实例（如果没画网格则创建一个最小实例）
                if coord_type == "no":
                    renderer = GridRenderer()
                for mp in marker_list:
                    image = renderer.draw_marker(
                        image,
                        x=mp["x"],
                        y=mp["y"],
                        ring_radius=mp.get("ring_radius", config.screenshot.default_marker_ring_radius),
                        ring_line_width=mp.get("ring_line_width", config.screenshot.default_marker_ring_line_width),
                        ring_color=mp.get("ring_color", config.screenshot.default_marker_ring_color),
                        dot_radius=mp.get("dot_radius", config.screenshot.default_marker_dot_radius),
                        dot_color=mp.get("dot_color", config.screenshot.default_marker_dot_color)
                    )

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

            if marker_params:
                screenshot_msg = "Screenshot successful. Marker indicates the position of your input coordinates on the image. If result is unsatisfactory, refer to skill.md for parameter tuning."
            else:
                screenshot_msg = "Screenshot successful. If result is unsatisfactory, refer to skill.md for parameter tuning."

            return {
                "success": True,
                "message": screenshot_msg,
                "data": result_data
            }

        elif action == "crop_zoom_screenshot":
            from app.utils.image import image_to_base64, save_image
            from app.utils.image import generate_crop_zoom_filename, generate_data_dir
            from app.utils.image import validate_source_image_path, crop_and_zoom
            from PIL import Image

            required_fields = ["source_image_path", "center_x", "center_y", "crop_width", "crop_height"]
            for field in required_fields:
                if field not in params:
                    return {"success": False, "message": f"Missing required parameter: {field}"}

            config = config_service.get()
            source_path = params["source_image_path"]
            center_x = params["center_x"]
            center_y = params["center_y"]
            crop_w = params["crop_width"]
            crop_h = params["crop_height"]
            zoom_scale = params.get("zoom_scale", config.screenshot.default_crop_zoom_scale)

            # 路径校验
            path_error = validate_source_image_path(source_path)
            if path_error:
                log_service.log(
                    ai_app_type=ai_app_type, session_id=session_id, window_id=0,
                    process_name="", instruction="crop_zoom_screenshot",
                    params=params, result={"success": False, "message": path_error},
                    client_ip=client_ip
                )
                return {"success": False, "message": path_error}

            if not source_path or not os.path.exists(source_path):
                log_service.log(
                    ai_app_type=ai_app_type, session_id=session_id, window_id=0,
                    process_name="", instruction="crop_zoom_screenshot",
                    params=params, result={"success": False, "message": f"Image file not found: {source_path}"},
                    client_ip=client_ip
                )
                return {"success": False, "message": f"Image file not found: {source_path}. Check if the file exists or the path is correct."}

            try:
                with Image.open(source_path) as source_image:
                    try:
                        zoomed = crop_and_zoom(
                            source_image, center_x, center_y, crop_w, crop_h, zoom_scale
                        )
                    except ValueError as e:
                        log_service.log(
                            ai_app_type=ai_app_type, session_id=session_id, window_id=0,
                            process_name="", instruction="crop_zoom_screenshot",
                            params=params, result={"success": False, "message": str(e)},
                            client_ip=client_ip
                        )
                        return {"success": False, "message": str(e)}
            except Exception as e:
                log_service.log(
                    ai_app_type=ai_app_type, session_id=session_id, window_id=0,
                    process_name="", instruction="crop_zoom_screenshot",
                    params=params, result={"success": False, "message": f"Failed to read image: {source_path}"},
                    client_ip=client_ip
                )
                return {"success": False, "message": f"Failed to read image: {source_path}. Unsupported format or corrupted file."}

            data_dir = generate_data_dir("data", ai_app_type, session_id)
            filename = generate_crop_zoom_filename()
            image_path = os.path.join(data_dir, filename)
            save_image(zoomed, image_path)

            image_base64 = image_to_base64(zoomed)
            is_local = is_local_request(client_ip)
            if is_local:
                result_data = {"image_path": os.path.abspath(image_path)}
            else:
                result_data = {"image_base64": image_base64}

            log_service.log(
                ai_app_type=ai_app_type, session_id=session_id, window_id=0,
                process_name="", instruction="crop_zoom_screenshot",
                params=params, result={"success": True, "image_path": image_path},
                client_ip=client_ip
            )

            return {
                "success": True,
                "message": "Crop zoom successful. If details are still unclear, adjust parameters and process the same source image again.",
                "data": result_data
            }

        else:
            return {"success": False, "message": f"Unknown instruction type: {action}"}

    except Exception as e:
        return {"success": False, "message": str(e)}
