"""
裁剪放大API - 对已有图片进行裁剪并放大
"""
import os
import time
from fastapi import APIRouter, Header, Request

from app.models.request import CropZoomRequest
from app.models.response import (
    ScreenshotResponse,
    ScreenshotData,
    create_error_response
)
from app.services.log_service import log_service
from app.utils.image import (
    image_to_base64,
    save_image,
    generate_crop_zoom_filename,
    generate_data_dir,
    validate_source_image_path,
    crop_and_zoom
)
from app.api.decorators import get_client_ip
from PIL import Image

router = APIRouter()


def is_local_request(client_ip: str) -> bool:
    """判断是否为本地请求（只有本机进程能访问文件路径）"""
    local_ips = {"127.0.0.1", "::1", "localhost"}
    return client_ip in local_ips


@router.post("/crop_zoom_screenshot")
async def crop_zoom_screenshot(
    request: CropZoomRequest,
    req: Request = None,
    authorization: str = Header(None)
):
    """对已有图片进行裁剪并放大"""
    client_ip = get_client_ip(req) if req else "unknown"
    start_time = time.time()

    # 1. 路径校验
    path_error = validate_source_image_path(request.source_image_path)
    if path_error:
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            window_id=0,
            process_name="",
            instruction="crop_zoom_screenshot",
            params=request.model_dump(),
            result={"success": False, "message": path_error},
            client_ip=client_ip
        )
        return create_error_response("INVALID_PARAMS", path_error)

    # 2. 校验源图片是否存在
    if not os.path.exists(request.source_image_path):
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            window_id=0,
            process_name="",
            instruction="crop_zoom_screenshot",
            params=request.model_dump(),
            result={"success": False, "message": f"Image file not found: {request.source_image_path}"},
            client_ip=client_ip
        )
        return create_error_response(
            "FILE_NOT_FOUND",
            f"Image file not found: {request.source_image_path}. Check if the file exists or the path is correct."
        )

    # 3. 读取并裁剪放大
    try:
        with Image.open(request.source_image_path) as source_image:
            try:
                zoomed = crop_and_zoom(
                    source_image,
                    center_x=request.center_x,
                    center_y=request.center_y,
                    crop_width=request.crop_width,
                    crop_height=request.crop_height,
                    zoom_scale=request.zoom_scale
                )
            except ValueError as e:
                log_service.log(
                    ai_app_type=request.ai_app_type,
                    session_id=request.session_id,
                    window_id=0,
                    process_name="",
                    instruction="crop_zoom_screenshot",
                    params=request.model_dump(),
                    result={"success": False, "message": str(e)},
                    client_ip=client_ip
                )
                return create_error_response("INVALID_PARAMS", str(e))
    except Exception as e:
        log_service.log(
            ai_app_type=request.ai_app_type,
            session_id=request.session_id,
            window_id=0,
            process_name="",
            instruction="crop_zoom_screenshot",
            params=request.model_dump(),
            result={"success": False, "message": f"Failed to read image: {request.source_image_path}"},
            client_ip=client_ip
        )
        return create_error_response(
            "INVALID_PARAMS",
            f"Failed to read image: {request.source_image_path}. Unsupported format or corrupted file."
        )

    # 4. 保存
    data_dir = generate_data_dir("data", request.ai_app_type, request.session_id)
    filename = generate_crop_zoom_filename()
    image_path = os.path.join(data_dir, filename)
    save_image(zoomed, image_path)

    # 5. 返回
    image_base64 = image_to_base64(zoomed)

    duration_ms = int((time.time() - start_time) * 1000)

    log_service.log(
        ai_app_type=request.ai_app_type,
        session_id=request.session_id,
        window_id=0,
        process_name="",
        instruction="crop_zoom_screenshot",
        params=request.model_dump(),
        result={"success": True, "image_path": image_path},
        duration_ms=duration_ms,
        client_ip=client_ip
    )

    is_local = is_local_request(client_ip)
    if is_local:
        screenshot_data = ScreenshotData(image_path=os.path.abspath(image_path))
    else:
        screenshot_data = ScreenshotData(image_base64=image_base64)

    return ScreenshotResponse(
        success=True,
        message="Crop zoom successful. If details are still unclear, adjust parameters and process the same source image again.",
        data=screenshot_data
    )
