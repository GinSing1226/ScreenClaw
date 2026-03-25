"""
进程管理API
"""
from fastapi import APIRouter, Header

from app.models.request import GetProcessListRequest
from app.models.response import (
    GetProcessListResponse,
    ProcessInfo,
    create_error_response
)
from app.services.process_service import process_service
from app.services.log_service import log_service

router = APIRouter()


@router.post("/get_process_list")
async def get_process_list(
    request: GetProcessListRequest,
    authorization: str = Header(None)
):
    """获取进程列表"""
    # 记录日志
    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        process_id=0,
        process_name="",
        instruction="get_process_list",
        params={"keyword": request.keyword},
        result={"success": True}
    )

    # 获取进程列表
    processes = process_service.get_process_list(request.keyword)

    return GetProcessListResponse(
        success=True,
        message="获取成功",
        data={"processes": processes}
    )
