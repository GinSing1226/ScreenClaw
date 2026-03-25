"""
图片处理工具
"""
import io
import base64
import os
import random
import string
from datetime import datetime
from typing import Optional
from PIL import Image


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

    格式: screenshot-hhmmss-rand4.png

    Returns:
        文件名
    """
    time_str = datetime.now().strftime("%H%M%S")
    rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"screenshot-{time_str}-{rand_str}.png"


def generate_data_dir(
    base_dir: str,
    ai_app_type: str,
    session_id: str
) -> str:
    """
    生成数据存储目录

    格式: base_dir/ai_app_type-session_id-yyyy-mm-dd/

    Args:
        base_dir: 基础目录
        ai_app_type: AI应用类型
        session_id: 会话ID

    Returns:
        目录路径
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    dir_name = f"{ai_app_type}-{session_id}-{date_str}"
    dir_path = os.path.join(base_dir, dir_name)

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    return dir_path
