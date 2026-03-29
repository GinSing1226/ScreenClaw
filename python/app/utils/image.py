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
    """获取项目根目录"""
    # 获取当前exe或脚本所在目录，然后向上一级找到项目根目录
    if getattr(sys, 'frozen', False):
        # 打包后的exe
        exe_dir = Path(sys.executable).parent
        # exe在 src-tauri/target/debug/ 或 release/ 目录下
        # 项目根目录是 exe 的父目录的父目录的父目录
        return exe_dir.parent.parent.parent
    else:
        # 开发模式：python/main.py 所在目录的父目录
        return Path(__file__).parent.parent.parent.parent


def get_data_dir() -> Path:
    """获取data目录路径"""
    return get_project_root() / "data"


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


def generate_data_dir(
    base_dir: str,
    ai_app_type: str,
    session_id: str,
    window_id: str = ""
) -> str:
    """
    生成数据存储目录

    格式: 项目根目录/data/ai_app_type_session_id[_window_id]_yyyy-mm-dd/

    Args:
        base_dir: 基础目录名（如 "data"）
        ai_app_type: AI应用类型
        session_id: 会话ID
        window_id: 窗口ID（可选）

    Returns:
        目录路径（绝对路径）
    """
    # 使用项目根目录下的data目录
    project_data_dir = get_data_dir()

    date_str = datetime.now().strftime("%Y-%m-%d")
    if window_id:
        dir_name = f"{ai_app_type}_{session_id}_{window_id}_{date_str}"
    else:
        dir_name = f"{ai_app_type}_{session_id}_{date_str}"
    dir_path = project_data_dir / dir_name

    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)

    return str(dir_path)
