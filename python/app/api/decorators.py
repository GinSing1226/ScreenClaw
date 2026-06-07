"""
API通用装饰器 - 验证、日志、性能监控、hijack确认

装饰器使用示例：
    @router.post("/click")
    @with_verification
    @with_hijack_confirm(operation="Click", detail_fn=lambda r: f"Coordinates: ({r.x}, {r.y})")
    @log_and_format
    async def click(request: ClickRequest, req: Request = None, authorization: str = Header(None)):
        # 业务逻辑，直接使用 request 和注入的变量
        process_info = request.process_info
        start_time = request.start_time
        client_ip = request.client_ip
        ...
"""
import time
import functools
import win32gui
from typing import Optional, Callable
from fastapi import Request
from pydantic import BaseModel

from app.models.response import create_error_response
from app.services.process_service import process_service
from app.services.config_service import config_service
from app.services.log_service import log_service


def with_hijack_confirm(operation: str, detail_fn: Callable = None):
    """Hijack 确认装饰器 - 统一处理 delegated 路由和 hijack 确认

    逻辑：
    1. delegated 激活 → 跳过确认，设置 action_method="delegated"
    2. hijack → 弹确认弹窗
    3. background → 直接放行

    必须在 @with_verification 之后使用（依赖 request.process_info）

    Args:
        operation: 操作名称，如 "Click", "Press key"
        detail_fn: 可选，从 request 提取详情的函数，如 lambda r: f"Key: {r.key}"
                   不传则使用默认详情
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 查找请求数据模型（支持多种位置）
            request_data = None

            # 检查位置参数
            for arg in args:
                if hasattr(arg, 'window_id') and hasattr(arg, 'ai_app_type'):
                    request_data = arg
                    break

            # 检查关键字参数
            if not request_data:
                for key, value in kwargs.items():
                    if hasattr(value, 'window_id') and hasattr(value, 'ai_app_type'):
                        request_data = value
                        break

            # 如果还是找不到，尝试直接使用第一个位置参数
            if not request_data and len(args) > 0:
                request_data = args[0]

            if not request_data or not hasattr(request_data, 'action_method'):
                return await func(*args, **kwargs)

            # 1. delegated 激活 → 跳过确认，强制转为物理操作
            if config_service.is_delegated_active():
                object.__setattr__(request_data, 'action_method', 'delegated')
                return await func(*args, **kwargs)

            # 2. background → 直接放行
            if request_data.action_method != "hijack":
                return await func(*args, **kwargs)

            # 3. hijack → 弹确认弹窗
            process_info = getattr(request_data, 'process_info', None)
            if not process_info:
                # 没有 process_info（未经过 @with_verification），直接放行
                return await func(*args, **kwargs)

            try:
                window_title = win32gui.GetWindowText(request_data.window_id) or "Unknown window"
            except Exception:
                window_title = "Unknown window"

            detail = detail_fn(request_data) if detail_fn else ""
            from app.services.confirm_service import ConfirmService
            confirm_result = ConfirmService.request_confirm(
                ai_app_type=request_data.ai_app_type,
                window_title=window_title,
                process_name=process_info.process_name,
                operation=operation,
                operation_detail=detail
            )

            print(f"[ConfirmCheck] → Confirmed: {confirm_result.confirmed}")
            if not confirm_result.confirmed:
                return create_error_response("USER_DENIED", "User denied the operation")

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def with_verification(func: Callable) -> Callable:
    """
    验证装饰器 - 验证窗口、Process并注入上下文变量

    功能：
    1. 验证窗口是否存在
    2. 验证Process是否被禁止
    3. 注入 process_info, start_time, client_ip 到请求对象

    错误处理：
    - Window not found：记录日志并返回错误响应
    - Process被禁止：返回错误响应

    使用方式：
        @with_verification
        async def my_endpoint(request: RequestModel, req: Request = None, ...):
            # 此时 request 对象已被注入以下属性：
            # - request.process_info: Process信息对象
            # - request.start_time: 请求开始时间戳
            # - request.client_ip: 客户端IP地址
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # 从参数中提取请求数据和 Request 对象
        request_data = None
        fastapi_request = None

        # 查找请求数据模型（支持多种位置）
        for arg in args:
            if hasattr(arg, 'window_id') and hasattr(arg, 'ai_app_type'):
                request_data = arg
                break

        # 检查关键字参数
        if not request_data:
            for key, value in kwargs.items():
                if hasattr(value, 'window_id') and hasattr(value, 'ai_app_type'):
                    request_data = value
                    break

        # 如果还是找不到，尝试直接使用第一个位置参数
        if not request_data and len(args) > 0:
            request_data = args[0]

        # 查找 FastAPI Request 对象（可能在 args 或 kwargs 中）
        for arg in args:
            if isinstance(arg, Request):
                fastapi_request = arg
                break

        # 如果在位置参数中没找到 Request，从关键字参数中查找
        if not fastapi_request:
            for value in kwargs.values():
                if isinstance(value, Request):
                    fastapi_request = value
                    break

        # 获取客户端IP
        client_ip = get_client_ip(fastapi_request) if fastapi_request else "unknown"
        start_time = time.time()

        # 验证 request_data 是否有效
        if not request_data or not hasattr(request_data, 'window_id'):
            return await func(*args, **kwargs)

        # 验证窗口是否存在
        process_info = process_service.get_process_by_window_id(request_data.window_id)
        if not process_info:
            # 记录日志
            log_service.log(
                ai_app_type=request_data.ai_app_type,
                session_id=request_data.session_id,
                window_id=request_data.window_id,
                process_name="",
                instruction=request_data.__class__.__name__,
                params=request_data.model_dump(),
                result={"success": False, "message": "Window not found"},
                client_ip=client_ip
            )
            return create_error_response("WINDOW_NOT_FOUND", "Window not found")

        # 检查Process是否被禁止
        if config_service.is_process_blocked(process_info.process_name):
            return create_error_response("PROCESS_BLOCKED", f"Process {process_info.process_name} is blocked")

        # 使用 Pydantic 的 model_dump() 和 model_construct() 来创建包含额外字段的副本
        # 或者直接使用 object.__setattr__ 绕过 Pydantic 的验证
        object.__setattr__(request_data, 'process_info', process_info)
        object.__setattr__(request_data, 'start_time', start_time)
        object.__setattr__(request_data, 'client_ip', client_ip)

        # 继续执行原函数
        return await func(*args, **kwargs)

    return wrapper


def log_and_format(func: Callable) -> Callable:
    """
    日志和格式化装饰器 - 自动记录操作日志和格式化响应

    功能：
    1. 自动记录操作日志（无论成功或失败）
    2. 计算操作耗时
    3. 格式化响应为统一的 BaseResponse 格式

    使用方式：
        @log_and_format
        async def my_endpoint(...) -> BaseResponse:
            # 返回 BaseResponse 或字典即可，装饰器会自动处理
            return {"success": True, "message": "Operation successful"}

    注意：
        - 需要在 @with_verification 之后使用，以便访问注入的上下文变量
        - 原函数应该返回 BaseResponse 对象或包含 success 字段的字典
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # 查找请求数据模型
        request_data = None
        for arg in args:
            if hasattr(arg, 'process_info') and hasattr(arg, 'start_time'):
                request_data = arg
                break

        if not request_data:
            for key, value in kwargs.items():
                if hasattr(value, 'process_info') and hasattr(value, 'start_time'):
                    request_data = value
                    break

        # 执行原函数
        result = await func(*args, **kwargs)

        # 如果没有请求数据（如 wait 接口），跳过日志记录
        if not request_data:
            return result

        # 计算耗时
        duration_ms = int((time.time() - request_data.start_time) * 1000)

        # 提取结果信息
        if isinstance(result, dict):
            success = result.get('success', False)
            message = result.get('message', '')
            error_code = result.get('error_code', None)
        else:
            success = getattr(result, 'success', False)
            message = getattr(result, 'message', '')
            error_code = getattr(result, 'error_code', None)

        # 构建日志参数
        log_params = {
            "ai_app_type": request_data.ai_app_type,
            "session_id": request_data.session_id,
            "window_id": request_data.window_id,
            "process_name": request_data.process_info.process_name if request_data.process_info else "",
            "instruction": func.__name__,
            "params": request_data.model_dump() if hasattr(request_data, 'model_dump') else {},
            "result": {
                "success": success,
                "message": message
            },
            "duration_ms": duration_ms,
            "client_ip": getattr(request_data, 'client_ip', 'unknown')
        }

        # 添加错误码（如果有）
        if error_code:
            log_params["result"]["error_code"] = error_code

        # 记录日志
        log_service.log(**log_params)

        return result

    return wrapper


def get_client_ip(request: Request) -> str:
    """
    获取客户端IP地址

    优先级：
    1. X-Forwarded-For (代理情况)
    2. X-Real-IP
    3. 直接连接的客户端IP

    Args:
        request: FastAPI Request 对象

    Returns:
        客户端IP地址字符串，无法获取时返回 "unknown"
    """
    # 优先从 X-Forwarded-For 获取（代理情况）
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    # 从 X-Real-IP 获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # 直接连接的客户端IP
    if request.client:
        return request.client.host

    return "unknown"
