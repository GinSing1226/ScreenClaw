"""
录制 API 端点 — 供 Tauri 内部调用
无需 @with_verification / @with_hijack_confirm
"""
from fastapi import APIRouter

from app.models.response import BaseResponse
from app.services.recording_service import recording_service

router = APIRouter()


@router.post("/recording/start")
async def start_recording():
    """开始录制"""
    result = recording_service.start()
    if result["success"]:
        return BaseResponse(success=True, message=result["message"])
    return BaseResponse(success=False, message=result["message"])


@router.post("/recording/stop")
async def stop_recording():
    """停止录制并保存产物"""
    result = recording_service.stop()
    if result["success"]:
        return BaseResponse(
            success=True,
            message="Recording saved.",
            data={
                "record_dir": result["record_dir"],
                "total_steps": result["total_steps"],
                "duration_ms": result["duration_ms"],
            },
        )
    return BaseResponse(success=False, message=result["message"])


@router.get("/recording/status")
async def recording_status():
    """查询录制状态"""
    status = recording_service.get_status()
    return BaseResponse(success=True, message="OK", data=status)
