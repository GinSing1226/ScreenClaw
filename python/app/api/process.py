"""
窗口管理API
"""
from fastapi import APIRouter, Header

from app.models.request import GetWindowListRequest
from app.models.response import (
    GetWindowListResponse,
    ProcessInfo,
    create_error_response
)
from app.services.process_service import process_service
from app.services.log_service import log_service

router = APIRouter()


@router.post("/get_window_list")
async def get_window_list(
    request: GetWindowListRequest,
    authorization: str = Header(None)
):
    """获取窗口列表"""
    # 记录日志
    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        window_id=0,
        process_name="",
        instruction="get_window_list",
        params={"keyword": request.keyword},
        result={"success": True}
    )

    # 获取窗口列表
    windows = process_service.get_process_list(
        keyword=request.keyword,
        include_children=request.include_children,
        children_filter=request.children_filter
    )

    return GetWindowListResponse(
        success=True,
        message="获取成功",
        data={"windows": windows}
    )
