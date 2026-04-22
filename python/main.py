"""
ScreenClaw Python Backend
主入口文件
"""
import os
import sys

# 修复 PyInstaller console=False 时 sys.stderr/stdout 为 None 的问题
# 必须在所有 import 之前执行
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.api.router import api_router
from app.services.config_service import config_service
from app.models.response import BaseResponse, create_error_response

# 创建 FastAPI 应用
app = FastAPI(
    title="ScreenClaw API",
    description="AI应用的可视化操作必备伴侣",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS - 仅允许局域网和本机访问
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(127\.0\.0\.1|localhost|192\.168\.\d{1,3}\.\d{1,3})(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Token 验证中间件
@app.middleware("http")
async def verify_token(request: Request, call_next):
    """验证 Token"""
    # 跳过健康检查
    if request.url.path == "/api/health":
        return await call_next(request)

    # 跳过文档
    if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)

    # 获取 Token
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

    # 验证 Token
    if not token:
        return JSONResponse(
            status_code=401,
            content=BaseResponse(
                success=False,
                message="Authentication required",
                error_code="AUTH_FAILED"
            ).model_dump()
        )

    if not config_service.verify_token(token):
        return JSONResponse(
            status_code=401,
            content=BaseResponse(
                success=False,
                message="Authentication failed",
                error_code="AUTH_FAILED"
            ).model_dump()
        )

    return await call_next(request)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    # 记录详细错误到日志
    print(f"Error: {type(exc).__name__}: {str(exc)}")

    # 返回通用错误信息，不暴露内部细节
    return JSONResponse(
        status_code=500,
        content=BaseResponse(
            success=False,
            message="Internal server error. Refer to skill.md for troubleshooting.",
            error_code="INTERNAL_ERROR"
        ).model_dump()
    )


# 422 校验错误字段描述映射
FIELD_DESCRIPTIONS = {
    # 百分比坐标（0-100）
    "x": "x (percentage 0-100)",
    "y": "y (percentage 0-100)",
    "start_x": "start_x (percentage 0-100)",
    "start_y": "start_y (percentage 0-100)",
    "end_x": "end_x (percentage 0-100)",
    "end_y": "end_y (percentage 0-100)",
    "center_x": "center_x (percentage 0-100)",
    "center_y": "center_y (percentage 0-100)",
    # 裁剪区域（百分比）
    "crop_width": "crop_width (percentage 0-100)",
    "crop_height": "crop_height (percentage 0-100)",
    # 网格密度
    "density_x": "density_x (0.1-100)",
    "density_y": "density_y (0.1-100)",
    # 放大倍数
    "zoom_scale": "zoom_scale (1.0-10.0)",
}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """422 参数校验错误处理"""
    errors = exc.errors()
    parts = []
    for e in errors:
        field = e["loc"][-1] if e.get("loc") else "unknown"
        desc = FIELD_DESCRIPTIONS.get(field, field)
        parts.append(f"{desc}: {e['msg']}")
    details = "; ".join(parts)
    return JSONResponse(
        status_code=422,
        content=BaseResponse(
            success=False,
            message=f"Invalid request parameters: {details}. Refer to skill.md for parameter details.",
            error_code="INVALID_PARAMS"
        ).model_dump()
    )


# 注册路由
app.include_router(api_router)


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "ScreenClaw API",
        "version": "1.0.0",
        "docs": "/docs"
    }


def find_available_port(start_port: int, max_attempts: int = 100) -> int:
    """查找可用端口"""
    import socket

    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return port
        except OSError:
            continue

    return start_port


def main():
    """主函数"""
    # 修复 PyInstaller console=False 时 sys.stderr 为 None 的问题
    import sys
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')

    # 更新本机 IP
    config_service.update_local_ip()

    # 查找可用端口
    config = config_service.get()
    port = find_available_port(config.server.port)

    if port != config.server.port:
        print(f"端口 {config.server.port} 被占用，使用端口 {port}")
        config_service.update_port(port)

    print(f"\n{'='*50}")
    print(f"  ScreenClaw Python Backend")
    print(f"{'='*50}")
    print(f"  Local:   http://127.0.0.1:{port}")
    print(f"  Network: http://{config.server.local_ip}:{port}")
    # 只显示Token的首尾各4个字符
    token_display = f"{config.server.token[:4]}...{config.server.token[-4:]}" if len(config.server.token) > 8 else "***"
    print(f"  Token:   {token_display}")
    print(f"{'='*50}\n")

    # 启动服务（单进程模式，避免产生多个进程）
    uvicorn.run(
        app,
        host=config.server.host,
        port=port,
        log_level="info",
        workers=1,  # 强制单 worker
        access_log=False,  # 禁用访问日志减少开销
        reload=False  # 禁用热重载避免进程倍增
    )


if __name__ == "__main__":
    main()
