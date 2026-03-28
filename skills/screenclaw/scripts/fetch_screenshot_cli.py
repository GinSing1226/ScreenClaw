#!/usr/bin/env python3
"""
ScreenClaw 截图获取脚本（独立版本）

可以直接调用，无需依赖其他模块。

用法一（推荐）：直接调用API
    python fetch_screenshot.py <api_url> <token> <window_id> [session_id]

示例：
    python fetch_screenshot.py http://192.168.10.190:12261 TOKEN123 1380176
    python fetch_screenshot.py http://192.168.10.190:12261 TOKEN123 1380176 my-session

用法二（备用）：处理已保存的JSON响应（会自动删除该JSON文件）
    python fetch_screenshot.py <json_file_path> <api_url>

示例：
    python fetch_screenshot.py C:\\Users\\xxx\\AppData\\Local\\Temp\\screenshot_response.json http://192.168.10.190:12261
"""

import sys
import json
import base64
import os
import tempfile
from pathlib import Path
try:
    import requests
except ImportError:
    print("错误：缺少 requests 模块")
    print("请安装：pip install requests")
    sys.exit(1)


def process_result(result, api_url):
    """处理API响应结果"""
    if not result.get("success"):
        print(f"API 错误: {result.get('message', 'Unknown error')}")
        return None

    image_path = result["data"]["image_path"]
    image_base64 = result["data"]["image_base64"]

    # 判断本地还是局域网
    is_local = any(indicator in api_url.lower() for indicator in ["localhost", "127.0.0.1", "::1"])

    if is_local:
        # 本地场景：直接返回路径
        return image_path
    else:
        # 局域网场景：保存到本地
        # 从 image_path 中提取目录名和文件名
        original_path = Path(image_path)
        dir_name = original_path.parent.name
        filename = original_path.name

        # 确定保存目录
        if os.name == 'nt':  # Windows
            base_dir = os.path.expandvars("%APPDATA%\\screenclaw\\data")
        else:  # Linux/macOS
            base_dir = os.path.expanduser("~/.local/share/screenclaw/data")

        output_dir = Path(base_dir) / dir_name
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename

        # 保存图片
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(image_base64))

        return str(output_path)


def main():
    # 用法二：处理已保存的JSON文件
    if len(sys.argv) == 3 and sys.argv[1].endswith('.json'):
        json_path = sys.argv[1]
        api_url = sys.argv[2]

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                result = json.load(f)
        except Exception as e:
            print(f"读取JSON文件失败: {e}")
            sys.exit(1)

        # 处理结果
        output_path = process_result(result, api_url)

        # 自动删除临时JSON文件
        try:
            os.remove(json_path)
        except:
            pass  # 删除失败不影响主流程

        if output_path:
            print(output_path)
        sys.exit(0)

    # 用法一：直接调用API
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    api_url = sys.argv[1]
    token = sys.argv[2]
    window_id = int(sys.argv[3])
    session_id = sys.argv[4] if len(sys.argv) > 4 else "default"

    # 调用 API
    screenshot_url = f"{api_url.rstrip('/')}/api/screenshot"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    body = {
        "ai_app_type": "claude_code",
        "session_id": session_id,
        "window_id": window_id,
        "coordinate_type": "grid"
    }

    try:
        response = requests.post(screenshot_url, headers=headers, json=body, timeout=30)
        response.raise_for_status()
        result = response.json()
    except Exception as e:
        print(f"API 调用失败: {e}")
        sys.exit(1)

    output_path = process_result(result, screenshot_url)
    if output_path:
        print(output_path)

    # 处理响应
    image_path = result["data"]["image_path"]
    image_base64 = result["data"]["image_base64"]

    # 判断本地还是局域网
    is_local = any(indicator in screenshot_url.lower() for indicator in ["localhost", "127.0.0.1", "::1"])

    if is_local:
        # 本地场景：直接返回路径
        print(image_path)
    else:
        # 局域网场景：保存到本地
        # 从 image_path 中提取目录名和文件名
        original_path = Path(image_path)
        dir_name = original_path.parent.name
        filename = original_path.name

        # 确定保存目录
        if os.name == 'nt':  # Windows
            base_dir = os.path.expandvars("%APPDATA%\\screenclaw\\data")
        else:  # Linux/macOS
            base_dir = os.path.expanduser("~/.local/share/screenclaw/data")

        output_dir = Path(base_dir) / dir_name
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename

        # 保存图片
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(image_base64))

        print(output_path)


if __name__ == "__main__":
    main()
