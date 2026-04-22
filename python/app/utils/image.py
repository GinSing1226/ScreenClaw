"""
图片处理工具
"""
import io
import base64
import os
import random
import string
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from PIL import Image


def get_project_root() -> Path:
    """获取项目根目录

    便携包环境：exe 和 data/ 同级，返回 exe 所在目录
    开发环境：向上3级找到项目根目录
    """
    if getattr(sys, 'frozen', False):
        # 打包后的exe
        exe_dir = Path(sys.executable).parent

        # 检查 exe 同级目录是否有 data/config.json（便携包环境）
        data_in_exe_dir = exe_dir / "data" / "config.json"
        if data_in_exe_dir.exists():
            return exe_dir

        # 开发环境：向上3级
        return exe_dir.parent.parent.parent
    else:
        # 开发模式：python/main.py 所在目录的父目录
        return Path(__file__).parent.parent.parent.parent


def get_data_dir() -> Path:
    """获取data目录路径"""
    return get_project_root() / "data"


def validate_source_image_path(source_image_path: str) -> Optional[str]:
    """校验源图片路径是否在 data 目录内

    Returns:
        None 表示校验通过，否则返回错误消息
    """
    data_root = get_data_dir().resolve()
    source = Path(source_image_path).resolve()
    if not str(source).startswith(str(data_root)):
        return f"Access denied: path must be within data directory"
    return None


def crop_and_zoom(
    image: Image.Image,
    center_x: float,
    center_y: float,
    crop_width: float,
    crop_height: float,
    zoom_scale: float
) -> Image.Image:
    """对图片进行裁剪并放大

    Args:
        image: 原始图片
        center_x: 裁剪区域中心点横坐标百分比 (0-100)
        center_y: 裁剪区域中心点纵坐标百分比 (0-100)
        crop_width: 裁剪区域总宽度百分比 (0-100)
        crop_height: 裁剪区域总高度百分比 (0-100)
        zoom_scale: 放大倍数 (1.0=不放大)

    Returns:
        裁剪放大后的图片

    Raises:
        ValueError: 裁剪区域完全超出图片边界
    """
    img_w, img_h = image.size
    center_x_px = img_w * center_x / 100
    center_y_px = img_h * center_y / 100
    crop_w_px = img_w * crop_width / 100
    crop_h_px = img_h * crop_height / 100

    left = max(0, center_x_px - crop_w_px / 2)
    top = max(0, center_y_px - crop_h_px / 2)
    right = min(img_w, center_x_px + crop_w_px / 2)
    bottom = min(img_h, center_y_px + crop_h_px / 2)

    if right <= left or bottom <= top:
        raise ValueError(
            f"Crop area is completely outside the image. center: ({center_x}, {center_y}), image size: {img_w}x{img_h}."
        )

    cropped = image.crop((left, top, right, bottom))
    new_w = int(cropped.width * zoom_scale)
    new_h = int(cropped.height * zoom_scale)
    return cropped.resize((new_w, new_h), Image.LANCZOS)


def compress_image(
    image: Image.Image,
    quality: int = 85,
    max_width: int = 1920
) -> Image.Image:
    """
    压缩图片

    Args:
        image: 原始图片
        quality: JPEG质量 (1-100)
        max_width: 最大宽度，超过则缩放

    Returns:
        压缩后的图片
    """
    # 缩放
    if image.width > max_width:
        ratio = max_width / image.width
        new_height = int(image.height * ratio)
        image = image.resize((max_width, new_height), Image.LANCZOS)

    return image


def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """
    图片转base64

    Args:
        image: 图片对象
        format: 图片格式 (PNG/JPEG)

    Returns:
        base64编码字符串
    """
    buffer = io.BytesIO()

    if format.upper() == "JPEG":
        # JPEG不支持透明度，需要转换
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.save(buffer, format="JPEG", quality=85)
    else:
        image.save(buffer, format="PNG")

    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def base64_to_image(base64_str: str) -> Image.Image:
    """
    base64转图片

    Args:
        base64_str: base64编码字符串

    Returns:
        图片对象
    """
    image_data = base64.b64decode(base64_str)
    return Image.open(io.BytesIO(image_data))


def save_image(
    image: Image.Image,
    path: str,
    quality: int = 85
) -> str:
    """
    保存图片

    Args:
        image: 图片对象
        path: 保存路径
        quality: JPEG质量

    Returns:
        保存的文件路径
    """
    # 确保目录存在
    dir_path = os.path.dirname(path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # 根据扩展名保存
    if path.lower().endswith((".jpg", ".jpeg")):
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.save(path, "JPEG", quality=quality)
    else:
        image.save(path, "PNG")

    return path


def generate_screenshot_filename() -> str:
    """
    生成截图文件名

    格式: screenshot_hhmmss_rand4.png

    Returns:
        文件名
    """
    time_str = datetime.now().strftime("%H%M%S")
    rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"screenshot_{time_str}_{rand_str}.png"


def generate_scroll_screenshot_filename() -> str:
    """
    生成滚动长截图文件名

    格式: scroll_screenshot_hhmmss_rand4.png

    Returns:
        文件名
    """
    time_str = datetime.now().strftime("%H%M%S")
    rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"scroll_screenshot_{time_str}_{rand_str}.png"


def generate_crop_zoom_filename() -> str:
    """
    生成裁剪放大图片文件名

    格式: crop_zoom_hhmmss_rand4.png

    Returns:
        文件名
    """
    time_str = datetime.now().strftime("%H%M%S")
    rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"crop_zoom_{time_str}_{rand_str}.png"


def generate_data_dir(
    base_dir: str,
    ai_app_type: str,
    session_id: str
) -> str:
    """
    生成数据存储目录

    格式: 项目根目录/data/ai_app_type__session_id__yyyy-mm-dd/

    Args:
        base_dir: 基础目录名（如 "data"）
        ai_app_type: AI应用类型
        session_id: 会话ID

    Returns:
        目录路径（绝对路径）
    """
    # 使用项目根目录下的data目录
    project_data_dir = get_data_dir()

    date_str = datetime.now().strftime("%Y-%m-%d")
    dir_name = f"{ai_app_type}__{session_id}__{date_str}"
    dir_path = project_data_dir / dir_name

    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)

    return str(dir_path)
