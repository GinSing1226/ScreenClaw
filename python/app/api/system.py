"""
系统API - 健康检查、组合指令
"""
import time
from fastapi import APIRouter, Header

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

router = APIRouter()

# 服务启动时间
START_TIME = time.time()


@router.get("/health")
async def health_check():
    """健康检查"""
    uptime = int(time.time() - START_TIME)

    return HealthResponse(
        success=True,
        message="服务正常",
        data=HealthData(
            version="1.0.0",
            uptime_seconds=uptime
        )
    )


@router.post("/batch")
async def batch_execute(request: BatchRequest, authorization: str = Header(None)):
    """组合指令"""
    start_time = time.time()
    results = []
    executed_count = 0
    failed_index = None

    for i, instruction in enumerate(request.instructions):
        # 执行单条指令
        result = await _execute_single_instruction(
            request.ai_app_type,
            request.session_id,
            request.process_id,
            instruction
        )

        results.append(InstructionResult(
            success=result["success"],
            message=result["message"]
        ))

        if result["success"]:
            executed_count += 1
        else:
            # 失败时中断
            failed_index = i
            break

    duration_ms = int((time.time() - start_time) * 1000)

    # 记录日志
    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        process_id=request.process_id,
        process_name="",
        instruction="batch",
        params={"count": len(request.instructions)},
        result={
            "success": failed_index is None,
            "executed_count": executed_count,
            "failed_index": failed_index
        },
        duration_ms=duration_ms
    )

    if failed_index is not None:
        return BatchResponse(
            success=False,
            message=f"执行中断：第{failed_index + 1}条指令失败",
            data=BatchData(
                executed_count=executed_count,
                failed_index=failed_index,
                results=results
            )
        )

    return BatchResponse(
        success=True,
        message="执行完成",
        data=BatchData(
            executed_count=executed_count,
            failed_index=None,
            results=results
        )
    )


async def _execute_single_instruction(
    ai_app_type: str,
    session_id: str,
    process_id: int,
    instruction
) -> dict:
    """执行单条指令"""
    from app.services.process_service import process_service
    from app.services.config_service import config_service
    from app.platform.windows.input import windows_input
    from app.platform.windows.capture import windows_capture
    from app.core.grid import GridRenderer
    from app.utils.coordinate import percent_to_absolute
    from app.utils.image import compress_image, image_to_base64, save_image

    action = instruction.action
    params = instruction.params

    try:
        if action == "click":
            hwnd = process_service.get_hwnd_by_process_id(process_id)
            if not hwnd:
                return {"success": False, "message": "无法获取窗口句柄"}

            window_rect = process_service.get_window_rect(hwnd)
            abs_x, abs_y = percent_to_absolute(params["x"], params["y"], window_rect)
            result = windows_input.click(hwnd, abs_x, abs_y)

            return {"success": result.success, "message": result.error or "点击成功"}

        elif action == "long_press":
            hwnd = process_service.get_hwnd_by_process_id(process_id)
            if not hwnd:
                return {"success": False, "message": "无法获取窗口句柄"}

            window_rect = process_service.get_window_rect(hwnd)
            abs_x, abs_y = percent_to_absolute(params["x"], params["y"], window_rect)
            duration_ms = params.get("duration_ms", 500)
            result = windows_input.long_press(hwnd, abs_x, abs_y, duration_ms)

            return {"success": result.success, "message": result.error or "长按成功"}

        elif action == "swipe":
            hwnd = process_service.get_hwnd_by_process_id(process_id)
            if not hwnd:
                return {"success": False, "message": "无法获取窗口句柄"}

            window_rect = process_service.get_window_rect(hwnd)
            abs_start_x, abs_start_y = percent_to_absolute(
                params["start_x"], params["start_y"], window_rect
            )
            abs_end_x, abs_end_y = percent_to_absolute(
                params["end_x"], params["end_y"], window_rect
            )
            result = windows_input.swipe(
                hwnd, abs_start_x, abs_start_y, abs_end_x, abs_end_y
            )

            return {"success": result.success, "message": result.error or "滑动成功"}

        elif action == "right_click":
            hwnd = process_service.get_hwnd_by_process_id(process_id)
            if not hwnd:
                return {"success": False, "message": "无法获取窗口句柄"}

            window_rect = process_service.get_window_rect(hwnd)
            abs_x, abs_y = percent_to_absolute(params["x"], params["y"], window_rect)
            result = windows_input.right_click(hwnd, abs_x, abs_y)

            return {"success": result.success, "message": result.error or "右键成功"}

        elif action == "input_text":
            hwnd = process_service.get_hwnd_by_process_id(process_id)
            if not hwnd:
                return {"success": False, "message": "无法获取窗口句柄"}

            window_rect = process_service.get_window_rect(hwnd)
            abs_x, abs_y = percent_to_absolute(params["x"], params["y"], window_rect)
            result = windows_input.input_text(hwnd, abs_x, abs_y, params["text"])

            return {"success": result.success, "message": result.error or "输入成功"}

        elif action == "press_key":
            hwnd = process_service.get_hwnd_by_process_id(process_id)
            if not hwnd:
                return {"success": False, "message": "无法获取窗口句柄"}

            result = windows_input.key_press(hwnd, params["key"])

            return {"success": result.success, "message": result.error or "按键成功"}

        elif action == "wait":
            duration_ms = params.get("duration_ms", 1000)
            time.sleep(duration_ms / 1000)

            return {"success": True, "message": "等待完成"}

        else:
            return {"success": False, "message": f"未知指令类型: {action}"}

    except Exception as e:
        return {"success": False, "message": str(e)}
