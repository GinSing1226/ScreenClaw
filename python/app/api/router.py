"""
API路由汇总
"""
from fastapi import APIRouter

from app.api import process, screenshot, action, input as input_api, system, delegated, scroll_screenshot, crop_zoom

# 创建主路由
api_router = APIRouter()

# 注册子路由
api_router.include_router(process.router, prefix="/api", tags=["进程管理"])
api_router.include_router(screenshot.router, prefix="/api", tags=["截图"])
api_router.include_router(scroll_screenshot.router, prefix="/api", tags=["滚动长截图"])
api_router.include_router(crop_zoom.router, prefix="/api", tags=["截图"])
api_router.include_router(action.router, prefix="/api", tags=["操作"])
api_router.include_router(input_api.router, prefix="/api", tags=["输入"])
api_router.include_router(system.router, prefix="/api", tags=["系统"])
api_router.include_router(delegated.router, prefix="/api", tags=["托管模式"])
