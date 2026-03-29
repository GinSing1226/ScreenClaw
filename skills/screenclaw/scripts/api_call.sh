#!/bin/bash
# ScreenClaw 通用API调用脚本 (Bash)
#
# AI通过此脚本调用所有ScreenClaw API，无需手动组装curl命令。
# 中文会自动转换为Unicode编码。
#
# 用法：
#     ./api_call.sh <api_url> <token> <endpoint> [ai_app_type] [参数...]
#
# 示例：
#     # 获取窗口列表
#     ./api_call.sh http://192.168.10.190:12261 TOKEN get_window_list claude_code keyword=飞书
#
#     # 点击
#     ./api_call.sh http://192.168.10.190:12261 TOKEN click claude_code window_id=123456 x=50 y=35
#
#     # 输入文本
#     ./api_call.sh http://192.168.10.190:12261 TOKEN input_text claude_code window_id=123456 text=你好
#
# 注意：截图API请使用 fetch_screenshot_cli.py 专用脚本
# 降级路径：本脚本 → api_call.py → api_call.ps1 → 手动curl（见 references/api/call_templates.md）

set -e

if [ $# -lt 3 ]; then
    echo "用法: $0 <api_url> <token> <endpoint> [ai_app_type] [参数...]"
    exit 1
fi

API_URL="$1"
TOKEN="$2"
ENDPOINT="$3"
AI_APP_TYPE="${4:-claude_code}"
shift 4  # 移除前4个参数，剩余的是API参数

# 构建URL
URL="${API_URL%/}/api/${ENDPOINT}"

# 解析参数
PARAMS=()
HAS_SESSION_ID=false
for arg in "$@"; do
    if [[ "$arg" =~ ^(.+?)=(.+)$ ]]; then
        key="${BASH_REMATCH[1]}"
        value="${BASH_REMATCH[2]}"

        # 检查是否已有session_id
        if [[ "$key" == "session_id" ]]; then
            HAS_SESSION_ID=true
        fi

        # 类型转换
        if [[ "$value" == "true" ]]; then
            value="true"
        elif [[ "$value" == "false" ]]; then
            value="false"
        elif [[ "$value" =~ ^[0-9]+$ ]]; then
            value="$value"
        fi

        PARAMS+=("\"$key\":\"$value\"")
    fi
done

# 自动添加 session_id（如果没有提供）
if [[ "$HAS_SESSION_ID" == "false" ]]; then
    timestamp=$(date +"%Y%m%d_%H%M%S")
    PARAMS+=("\"session_id\":\"screenclaw_${timestamp}\"")
fi

# 构建JSON
JSON="{\"ai_app_type\":\"$AI_APP_TYPE\""
if [ ${#PARAMS[@]} -gt 0 ]; then
    JSON="$JSON,$(IFS=,; echo "${PARAMS[*]}")"
fi
JSON="$JSON}"

# 自动转换中文为Unicode（使用Python）
JSON=$(python3 -c "
import sys
json = '$JSON'
def encode_unicode(s):
    chars = []
    for c in s:
        code = ord(c)
        if code > 127:
            chars.append(f'\u{code:04x}')
        else:
            chars.append(c)
    # 处理转义的引号
    result = ''.join(chars)
    return result.replace('\"', '"').replace(\"\\'\", '\')
print(encode_unicode(json))
")

# 发送请求
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$JSON" \
  "$URL"
