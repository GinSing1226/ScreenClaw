#!/usr/bin/env python3
"""
ScreenClaw 通用API调用脚本

AI通过此脚本调用所有ScreenClaw API，无需手动组装curl命令。
支持所有端点（含batch）。可在PowerShell和bash终端中使用。

中文入参：直接传中文字符串即可，requests库会自动处理编码。
    python api_call.py ... text=你好世界

用法：
    python api_call.py <api_url> <token> <endpoint> ai_app_type=<type> session_id=<id> main_window_id=<id> [其他参数...]

必填参数（key=value格式）：
    ai_app_type      : AI应用类型，如 claude_code
    session_id       : 会话ID，格式 app_name_YYYYMMDD_HHMMSS
    main_window_id   : 主窗口ID（get_window_list/wait/delegated 免传）

示例：
    # 获取窗口列表
    python api_call.py http://192.168.10.190:12261 TOKEN get_window_list ai_app_type=claude_code session_id=sess_001 keyword=飞书

    # 点击
    python api_call.py http://192.168.10.190:12261 TOKEN click ai_app_type=claude_code session_id=sess_001 window_id=123456 main_window_id=123456 x=50 y=35

    # 输入文本（直接传中文）
    python api_call.py http://192.168.10.190:12261 TOKEN input_text ai_app_type=claude_code session_id=sess_001 window_id=123456 main_window_id=123456 text=你好世界

    # 托管模式
    python api_call.py http://192.168.10.190:12261 TOKEN delegated ai_app_type=claude_code session_id=sess_001 action=enter

注意：截图API请使用 fetch_screenshot_cli.py 专用脚本
降级路径：api_call.py → api_call.ps1 → api_call.sh → 手动curl
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
            elif value.startswith('[') or value.startswith('{'):
                # JSON数组或对象，尝试解析
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    pass  # 解析失败则保留为字符串
            params[key] = value
    return params


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    api_url = sys.argv[1]
    token = sys.argv[2]
    endpoint = sys.argv[3]

    # sys.argv[4] 可能是位置参数(ai_app_type裸值)或 key=value 形式
    # AI 习惯用 key=value 格式，此时不应作为位置参数吃掉
    param_args = sys.argv[4:]
    ai_app_type = None
    if param_args and '=' not in param_args[0]:
        ai_app_type = param_args[0]
        param_args = param_args[1:]

    # 构建请求
    url = f"{api_url.rstrip('/')}/api/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 解析参数
    params = parse_params(param_args)

    # 位置参数 ai_app_type 合并到 params（优先用 key=value 形式）
    if ai_app_type and 'ai_app_type' not in params:
        params['ai_app_type'] = ai_app_type

    # 强制检查：ai_app_type、session_id、main_window_id 必须由客户端显式传入
    if 'ai_app_type' not in params:
        print("错误：ai_app_type 参数必须显式传入。例如：ai_app_type=claude_code")
        sys.exit(1)
    if 'session_id' not in params:
        print("错误：session_id 参数必须显式传入。格式：app_name_YYYYMMDD_HHMMSS")
        sys.exit(1)
    if 'main_window_id' not in params:
        # get_window_list、wait、delegated 不需要 main_window_id
        exempt_endpoints = {'get_window_list', 'wait', 'delegated', 'health'}
        if endpoint not in exempt_endpoints:
            print("错误：main_window_id 参数必须显式传入。从get_window_list获取")
            sys.exit(1)

    # 构建body
    body = {
        "ai_app_type": params.pop('ai_app_type'),
        **params
    }

    # 发送请求（requests.post(json=) 内部 json.dumps 自动处理中文编码）
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
