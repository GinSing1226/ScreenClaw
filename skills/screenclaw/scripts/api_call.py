#!/usr/bin/env python3
"""
ScreenClaw 通用API调用脚本

AI通过此脚本调用所有ScreenClaw API，无需手动组装curl命令。
中文会自动转换为Unicode编码。

用法：
    python api_call.py <api_url> <token> <endpoint> [ai_app_type] [参数...]

示例：
    # 获取窗口列表
    python api_call.py http://192.168.10.190:12261 TOKEN get_window_list claude_code keyword=飞书

    # 点击
    python api_call.py http://192.168.10.190:12261 TOKEN click claude_code window_id=123456 x=50 y=35

    # 输入文本
    python api_call.py http://192.168.10.190:12261 TOKEN input_text claude_code window_id=123456 text=你好

注意：截图API请使用 fetch_screenshot_cli.py 专用脚本
降级路径：本脚本 → api_call.ps1 → api_call.sh → 手动curl（见 references/api/call_templates.md）
"""

import sys
import json
import requests


def encode_unicode(value):
    """递归处理参数中的中文字符，转换为Unicode编码"""
    if isinstance(value, dict):
        return {k: encode_unicode(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [encode_unicode(v) for v in value]
    elif isinstance(value, str):
        # 检测并转Unicode（只转中文字符）
        if any(ord(c) > 127 for c in value):
            return value.encode('unicode_escape').decode('utf-8')
    return value


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
            elif value.isdigit():
                value = int(value)
            params[key] = value
    return params


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    api_url = sys.argv[1]
    token = sys.argv[2]
    endpoint = sys.argv[3]
    ai_app_type = sys.argv[4] if len(sys.argv) > 4 else "claude_code"
    param_args = sys.argv[5:]

    # 构建请求
    url = f"{api_url.rstrip('/')}/api/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 解析参数
    params = parse_params(param_args)

    # 强制检查：ai_app_type、session_id、main_window_id 必须由客户端显式传入
    if 'ai_app_type' not in params:
        print("错误：ai_app_type 参数必须显式传入。例如：ai_app_type=claude_code")
        sys.exit(1)
    if 'session_id' not in params:
        print("错误：session_id 参数必须显式传入。格式：app_name_YYYYMMDD_HHMMSS")
        sys.exit(1)
    if 'main_window_id' not in params:
        # get_window_list 和 wait 不需要 main_window_id
        exempt_endpoints = {'get_window_list', 'wait'}
        if endpoint not in exempt_endpoints:
            print("错误：main_window_id 参数必须显式传入。从get_window_list获取")
            sys.exit(1)

    # 构建body
    body = {
        "ai_app_type": params.pop('ai_app_type'),
        **params
    }

    # 处理中文编码
    body = encode_unicode(body)

    # 发送请求
    try:
        response = requests.post(url, headers=headers, json=body, timeout=30)
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.RequestException as e:
        print(f"API调用失败: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"响应解析失败: {e}")
        print(f"原始响应: {response.text}")
        sys.exit(1)

    # 输出结果（JSON格式）
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
