#!/usr/bin/env python3
"""
ScreenClaw 截图获取脚本

用于从 ScreenClaw API 获取截图，并根据调用场景（本地/局域网）选择合适的处理方式。
"""

import json
import base64
import os
from pathlib import Path
import requests
from typing import Dict, Any, Optional


def fetch_screenshot(
    api_url: str,
    token: str,
    window_id: int,
    ai_app_type: str = "claude_code",
    session_id: str = "",
    coordinate_type: str = "grid",
    grid_params: Optional[Dict[str, Any]] = None,
    coordinate_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    调用 ScreenClaw 截图 API

    Args:
        api_url: API 完整路径（如 http://localhost:12261/api/screenshot）
        token: 认证 token
        window_id: 目标窗口句柄
        ai_app_type: AI 应用类型
        session_id: 会话唯一标识
        coordinate_type: 坐标类型（grid/no）
        grid_params: 网格参数
        coordinate_params: 坐标数字参数

    Returns:
        API 响应的 JSON 数据
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    body = {
        "ai_app_type": ai_app_type,
        "session_id": session_id,
        "window_id": window_id,
        "coordinate_type": coordinate_type
    }

    if grid_params:
        body["grid"] = grid_params

    if coordinate_params:
        body["coordinate"] = coordinate_params

    response = requests.post(api_url, headers=headers, json=body, timeout=30)
    response.raise_for_status()
    return response.json()


def process_screenshot_local(result: Dict[str, Any]) -> str:
    """
    本地调用场景：直接使用返回的 image_path

    Args:
        result: API 响应的 JSON 数据

    Returns:
        Markdown 格式的图片引用
    """
    if not result.get("success"):
        raise Exception(f"API error: {result.get('message')}")

    image_path = result["data"]["image_path"]
    return f"![screenshot](file:///{image_path})"


def process_screenshot_lan(
    result: Dict[str, Any]
) -> str:
    """
    局域网调用场景：解码 image_base64 并保存到调用方机器的用户数据目录

    从 API 返回的 image_path 中提取目录名和文件名，保持与 ScreenClaw 本地相同的结构。

    Args:
        result: API 响应的 JSON 数据

    Returns:
        保存后的图片路径
    """
    if not result.get("success"):
        raise Exception(f"API error: {result.get('message')}")

    # 提取数据
    data = result["data"]
    image_base64 = data["image_base64"]
    original_path = Path(data["image_path"])

    # 提取目录名（如：claude_code-session123-1001-2026-03-28）
    # 原路径格式：D:/screenClaw/data/{dir_name}/{filename}
    dir_name = original_path.parent.name
    filename = original_path.name

    # 确定保存路径（调用方机器的用户数据目录）
    if os.name == 'nt':  # Windows
        base_dir = os.path.expandvars("%APPDATA%\\screenclaw\\data")
    else:  # Linux/macOS
        base_dir = os.path.expanduser("~/.local/share/screenclaw/data")

    # 保持与 ScreenClaw 相同的目录结构
    output_dir = Path(base_dir) / dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    # 保存图片
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(image_base64))

    return str(output_path)


def is_localhost(api_url: str) -> bool:
    """
    判断 API 地址是否为本地地址

    Args:
        api_url: API URL

    Returns:
        True 如果是本地地址
    """
    localhost_indicators = ["localhost", "127.0.0.1", "::1"]
    return any(indicator in api_url.lower() for indicator in localhost_indicators)


def fetch_screenshot_auto(
    api_base_url: str,
    token: str,
    window_id: int,
    ai_app_type: str = "claude_code",
    session_id: str = "",
    **kwargs
) -> str:
    """
    自动判断场景并获取截图

    Args:
        api_base_url: API 基础 URL（如 http://localhost:12261）
        token: 认证 token
        window_id: 目标窗口句柄
        ai_app_type: AI 应用类型
        session_id: 会话唯一标识
        **kwargs: 其他截图参数

    Returns:
        本地场景：Markdown 格式的图片引用
        局域网场景：保存后的图片路径
    """
    screenshot_url = f"{api_base_url.rstrip('/')}/api/screenshot"
    result = fetch_screenshot(
        screenshot_url, token, window_id, ai_app_type, session_id, **kwargs
    )

    if is_localhost(screenshot_url):
        return process_screenshot_local(result)
    else:
        return process_screenshot_lan(result)


# CLI 使用示例
if __name__ == "__main__":
    import sys

    # 示例：python fetch_screenshot.py http://localhost:12261 your-token 12345
    if len(sys.argv) >= 4:
        api_base = sys.argv[1]
        token = sys.argv[2]
        window_id = int(sys.argv[3])

        result_path = fetch_screenshot_auto(
            api_base, token, window_id,
            ai_app_type="cli", session_id="manual"
        )
        print(f"Screenshot: {result_path}")
    else:
        print("Usage: python fetch_screenshot.py <api_base_url> <token> <window_id>")
