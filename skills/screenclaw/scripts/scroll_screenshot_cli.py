#!/usr/bin/env python3
"""
ScreenClaw 滚动长截图脚本（Python 版本）

用法：python scroll_screenshot_cli.py <api_url> <token> <window_id> <session_id> <ai_app_type> <main_window_id> [参数...]

参数说明：
  api_url        - ScreenClaw服务地址
  token          - 认证令牌
  window_id      - 窗口ID
  session_id     - 会话ID（必需）
  ai_app_type    - AI应用类型（必需）
  main_window_id - 主窗口ID（必需，从get_window_list获取）

滚动参数（可选）：
  max_scrolls=<值>       - 最大滚动次数（不指定则使用配置文件默认值）
  scroll_percent=<值>    - 初始滚动幅度(0.1-0.95)（不指定则使用配置文件默认值）
  scroll_wait=<值>       - 滚动等待时间(秒)（不指定则使用配置文件默认值）
  x=<值>                 - 滚动位置横坐标(0-100)，默认50（中心）
  y=<值>                 - 滚动位置纵坐标(0-100)，默认50（中心）

高级参数（可选）：
  max_adjust_retries=<值> - 自适应最大调整次数（不指定则使用配置文件默认值）
  target_overlap_min=<值> - 目标重叠下限(0.10-0.50)（不指定则使用配置文件默认值）
  target_overlap_max=<值> - 目标重叠上限(0.20-0.60)（不指定则使用配置文件默认值）
  stop_threshold=<值>     - 停止阈值(0.0-0.01)（不指定则使用配置文件默认值）

说明：
  - 未指定的参数将使用服务端 config.json 中的默认值
  - 本功能内部硬编码使用 hijack 模式
  - 本功能不支持网格坐标绘制
  - 远程场景的截图保存目录规则：{ai_app_type}__{session_id}__{yyyy-MM-dd}/
  - 系统会自动动态调整滚动幅度以获得最佳重叠，接口会返回实际使用的幅度

降级路径：本脚本 → scroll_screenshot_cli.ps1 → scroll_screenshot_cli.sh
"""

import sys
import json
import base64
import os
from pathlib import Path
try:
    import httpx
except ImportError:
    print("错误：缺少 httpx 模块")
    print("请确保在项目环境中运行此脚本")
    sys.exit(1)


def process_result(result, api_url, session_id=None, ai_app_type=None):
    """处理API响应结果"""
    if not result.get("success"):
        print(f"API 错误: {result.get('message', 'Unknown error')}")
        error_code = result.get("error_code")
        if error_code == "UNSUPPORTED_MODE":
            print("提示：滚动长截图只支持 hijack 或 delegated 模式")
        return None

    data = result.get("data", {})
    is_local = any(indicator in api_url.lower() for indicator in ["localhost", "127.0.0.1", "::1"])

    if is_local:
        # 本地场景：服务端返回image_path，直接使用
        return data.get("image_path")
    else:
        # 远程场景：服务端只返回base64，客户端自己生成符合规则的路径
        # 目录规则：{ai_app_type}__{session_id}__{yyyy-MM-dd}
        # 文件规则：scroll_screenshot_{HHMMSS}_{rand4}.png
        image_base64 = data.get("image_base64")
        if not image_base64:
            print("API 错误: 远程响应中没有image_base64")
            return None

        from datetime import datetime
        import random
        import string

        # 如果没有提供参数，尝试从响应中推断或使用默认值
        if session_id is None:
            session_id = "default"
        if ai_app_type is None:
            ai_app_type = "claude_code"

        date_str = datetime.now().strftime("%Y-%m-%d")
        dir_name = f"{ai_app_type}__{session_id}__{date_str}"

        time_str = datetime.now().strftime("%H%M%S")
        rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        filename = f"scroll_screenshot_{time_str}_{rand_str}.png"

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


def parse_params(param_args):
    """解析命令行参数为字典"""
    params = {}
    for arg in param_args:
        if '=' in arg:
            key, value = arg.split('=', 1)
            # 尝试转换为合适的类型
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif '.' in value:
                try:
                    value = float(value)
                except ValueError:
                    pass
            elif value.isdigit():
                value = int(value)
            params[key] = value
    return params


def main():
    if len(sys.argv) < 7:
        print(__doc__)
        sys.exit(1)

    api_url = sys.argv[1]
    token = sys.argv[2]
    window_id = int(sys.argv[3])
    session_id = sys.argv[4]
    ai_app_type = sys.argv[5]
    main_window_id = int(sys.argv[6])
    param_args = sys.argv[7:]

    # 解析参数
    params = parse_params(param_args)

    # 构建请求体（只包含用户指定的参数，未指定的由服务端使用 config.json 默认值）
    body = {
        "ai_app_type": ai_app_type,
        "session_id": session_id,
        "window_id": window_id,
        "main_window_id": main_window_id,
    }

    # 添加用户指定的参数（不设置默认值，让服务端使用 config.json）
    if 'max_scrolls' in params:
        body['max_scrolls'] = int(params['max_scrolls'])
    if 'scroll_percent' in params:
        body['scroll_percent'] = float(params['scroll_percent'])
    if 'scroll_wait' in params:
        body['scroll_wait'] = float(params['scroll_wait'])
    if 'x' in params:
        body['x'] = float(params['x'])
    if 'y' in params:
        body['y'] = float(params['y'])
    if 'max_adjust_retries' in params:
        body['max_adjust_retries'] = int(params['max_adjust_retries'])
    if 'target_overlap_min' in params:
        body['target_overlap_min'] = float(params['target_overlap_min'])
    if 'target_overlap_max' in params:
        body['target_overlap_max'] = float(params['target_overlap_max'])
    if 'stop_threshold' in params:
        body['stop_threshold'] = float(params['stop_threshold'])

    # 调用 API
    scroll_screenshot_url = f"{api_url.rstrip('/')}/api/scroll_screenshot"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 打印实际使用的参数
    print(f"开始滚动长截图...")
    print(f"  最大滚动次数: {body.get('max_scrolls', '使用配置文件默认值')}")
    print(f"  初始滚动幅度: {body.get('scroll_percent', '使用配置文件默认值')}")
    print(f"  滚动位置: ({body.get('x', 50)}, {body.get('y', 50)})")
    print(f"  等待时间: {body.get('scroll_wait', '使用配置文件默认值')}s")
    print(f"  最大调整次数: {body.get('max_adjust_retries', '使用配置文件默认值')}")

    try:
        with httpx.Client(timeout=300) as client:
            response = client.post(scroll_screenshot_url, headers=headers, json=body)
            response.raise_for_status()
            result = response.json()
    except httpx.TimeoutException:
        print(f"API 调用超时: 操作时间过长")
        sys.exit(1)
    except Exception as e:
        print(f"API 调用失败: {e}")
        sys.exit(1)

    output_path = process_result(result, api_url, session_id, ai_app_type)
    if output_path:
        data = result.get("data", {})
        scroll_count = data.get("scroll_count", 0)
        actual_scroll_percent = data.get("actual_scroll_percent", 0.0)
        fixed_header = data.get("fixed_header", 0)
        fixed_footer = data.get("fixed_footer", 0)

        print(f"\n滚动长截图完成！")
        print(f"  实际截图数量: {scroll_count}")
        print(f"  实际滚动幅度: {actual_scroll_percent * 100:.1f}%")
        if fixed_header > 0:
            print(f"  检测到固定头部: {fixed_header}px")
        if fixed_footer > 0:
            print(f"  检测到固定底部: {fixed_footer}px")
        print(f"  图片保存路径: {output_path}")
        print(output_path)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
