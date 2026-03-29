"""
API通用装饰器 - 验证、日志、性能监控
"""
import time
from typing import Optional, Dict, Any
from fastapi import Request

from app.models.response import create_error_response
from app.services.process_service import process_service
from app.services.config_service import config_service
from app.services.log_service import log_service


def verify_request_common(request_data, client_ip: str) -> Optional[Dict[str, Any]]:
    """
    通用验证逻辑 - 验证窗口、进程并记录开始时间

    Args:
        request_data: 请求数据对象（ClickRequest, SwipeRequest等）
        client_ip: 客户端IP地址

    Returns:
        验证成功时返回包含 process_info, start_time, client_ip 的字典
        窗口不存在时返回 {"error": "WINDOW_NOT_FOUND"}
        进程被禁止时返回 {"error": "PROCESS_BLOCKED"}

    注意：
    1. 窗口不存在时会自动记录日志并返回错误信息
    2. 进程被禁止时返回错误信息（不记录日志，由调用方处理）
    """
    start_time = time.time()

    # 获取窗口信息
    process_info = process_service.get_process_by_window_id(request_data.window_id)
    if not process_info:
        log_service.log(
            ai_app_type=request_data.ai_app_type,
            session_id=request_data.session_id,
            window_id=request_data.window_id,
            process_name="",
            instruction=request_data.__class__.__name__,
            params=request_data.model_dump(),
            result={"success": False, "message": "窗口不存在"},
            client_ip=client_ip
        )
        return {"error": "WINDOW_NOT_FOUND"}

    # 检查进程是否被禁止
    if config_service.is_process_blocked(process_info.process_name):
        return {"error": "PROCESS_BLOCKED"}

    return {
        "process_info": process_info,
        "start_time": start_time,
        "client_ip": client_ip
    }


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
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


def _get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
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
