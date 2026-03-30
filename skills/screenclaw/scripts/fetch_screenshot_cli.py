#!/usr/bin/env python3
"""
ScreenClaw 截图获取脚本（专用）

用法：python fetch_screenshot_cli.py <api_url> <token> <window_id> [session_id] [ai_app_type]

参数说明：
  api_url     - ScreenClaw服务地址
  token       - 认证令牌
  window_id   - 窗口ID
  session_id  - 会话ID（可选，默认default）
  ai_app_type - AI应用类型（可选，默认claude_code）

降级路径：本脚本 → fetch_screenshot_cli.ps1 → fetch_screenshot_cli.sh
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


def process_result(result, api_url, session_id="default", ai_app_type="claude_code", window_id=0):
    """处理API响应结果"""
    if not result.get("success"):
        print(f"API 错误: {result.get('message', 'Unknown error')}")
        return None

    data = result.get("data", {})
    is_local = any(indicator in api_url.lower() for indicator in ["localhost", "127.0.0.1", "::1"])

    if is_local:
        # 本地场景：服务端返回image_path，直接使用
        return data.get("image_path")
    else:
        # 远程场景：服务端只返回base64，客户端自己生成符合规则的路径
        # 目录规则：{ai_app_type}__{session_id}__{window_id}__{yyyy-MM-dd}
        # 文件规则：screenshot_{HHMMSS}_{rand4}.png
        image_base64 = data.get("image_base64")
        if not image_base64:
            print("API 错误: 远程响应中没有image_base64")
            return None

        from datetime import datetime
        import random
        import string

        date_str = datetime.now().strftime("%Y-%m-%d")
        dir_name = f"{ai_app_type}__{session_id}__{window_id}__{date_str}"

        time_str = datetime.now().strftime("%H%M%S")
        rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        filename = f"screenshot_{time_str}_{rand_str}.png"

        # 确定保存目录
        if os.name == 'nt':  # Windows
            base_dir = os.path.expandvars("%APPDATA%\\screenclaw\\data")
        else:  # Linux/macOS
            base_dir = os.path.expanduser("~/.local/share/screenclaw/data")

        output_dir = Path(base_dir) / dir_name
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / filename
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
        output_path = process_result(result, api_url, session_id, ai_app_type, window_id)

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
    ai_app_type = sys.argv[5] if len(sys.argv) > 5 else "claude_code"

    # 调用 API
    screenshot_url = f"{api_url.rstrip('/')}/api/screenshot"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    body = {
        "ai_app_type": ai_app_type,
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

    output_path = process_result(result, api_url, session_id, ai_app_type, window_id)
    if output_path:
        print(output_path)


if __name__ == "__main__":
    main()
