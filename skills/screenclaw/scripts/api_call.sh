#!/bin/bash
# ScreenClaw 通用API调用脚本 (Bash)
#
# AI通过此脚本调用所有ScreenClaw API，无需手动组装curl命令。
# 支持所有端点（含batch）。只能在Git Bash或WSL中使用。
#
# 中文传参：直接传中文字符串即可，curl --data-binary 会自动处理UTF-8编码。
#     ./api_call.sh ... text=你好世界
#
# 用法：
#     ./api_call.sh <api_url> <token> <endpoint> [参数...]
#
# 示例：
#     # 获取窗口列表
#     ./api_call.sh http://192.168.10.190:12261 TOKEN get_window_list ai_app_type=claude_code session_id=test_001 keyword=飞书
#
#     # 点击
#     ./api_call.sh http://192.168.10.190:12261 TOKEN click ai_app_type=claude_code session_id=test_001 window_id=123456 x=50 y=35
#
#     # 输入文本（直接传中文）
#     ./api_call.sh http://192.168.10.190:12261 TOKEN input_text ai_app_type=claude_code session_id=test_001 window_id=123456 text=你好世界
#
# 注意：
#   - 截图API请使用 fetch_screenshot_cli.py 专用脚本
#   - ai_app_type 和 session_id 必须显式传入，不支持自动生成
#   - 降级路径：api_call.py → api_call.ps1 → api_call.sh → 手动curl

set -e

if [ $# -lt 3 ]; then
    echo "用法: $0 <api_url> <token> <endpoint> ai_app_type=<值> session_id=<值> [参数...]"
    exit 1
fi

API_URL="$1"
TOKEN="$2"
ENDPOINT="$3"
shift 3  # 移除前3个参数，剩余的是API参数

# 构建URL
URL="${API_URL%/}/api/${ENDPOINT}"

# 解析参数
PARAMS=()
HAS_AI_APP_TYPE=false
HAS_SESSION_ID=false
HAS_MAIN_WINDOW_ID=false
for arg in "$@"; do
    if [[ "$arg" == *"="* ]]; then
        key="${arg%%=*}"
        value="${arg#*=}"

        # 检查必需参数
        if [[ "$key" == "ai_app_type" ]]; then
            HAS_AI_APP_TYPE=true
            AI_APP_TYPE="$value"
        fi
        if [[ "$key" == "session_id" ]]; then
            HAS_SESSION_ID=true
        fi
        if [[ "$key" == "main_window_id" ]]; then
            HAS_MAIN_WINDOW_ID=true
        fi

        # 类型转换
        if [[ "$value" == "true" ]]; then
            value="true"
        elif [[ "$value" == "false" ]]; then
            value="false"
        elif [[ "$value" =~ ^[0-9]+$ ]]; then
            value="$value"
        fi

        # 跳过 ai_app_type，后面单独处理
        if [[ "$key" != "ai_app_type" ]]; then
            # JSON数组/对象不加引号包裹，其他值加引号
            # text/key/keyword/action/newline_key 始终作为字符串
            if [[ "$value" == "["* || "$value" == "{"* || "$value" == "true" || "$value" == "false" || ( "$value" =~ ^[0-9]+$ && "$key" != "text" && "$key" != "key" && "$key" != "keyword" && "$key" != "action" && "$key" != "newline_key" ) ]]; then
                PARAMS+=("\"$key\":$value")
            else
                PARAMS+=("\"$key\":\"$value\"")
            fi
        fi
    fi
done

# 强制检查：ai_app_type、session_id、main_window_id 必须由客户端显式传入
if [[ "$HAS_AI_APP_TYPE" == "false" ]]; then
    echo "错误：ai_app_type 参数必须显式传入。例如：ai_app_type=claude_code"
    exit 1
fi
if [[ "$HAS_SESSION_ID" == "false" ]]; then
    echo "错误：session_id 参数必须显式传入。格式：app_name_YYYYMMDD_HHMMSS"
    exit 1
fi
if [[ "$HAS_MAIN_WINDOW_ID" == "false" ]]; then
    # get_window_list 和 wait 不需要 main_window_id
    if [[ "$ENDPOINT" != "get_window_list" && "$ENDPOINT" != "wait" && "$ENDPOINT" != "delegated" && "$ENDPOINT" != "health" ]]; then
        echo "错误：main_window_id 参数必须显式传入。从get_window_list获取"
        exit 1
    fi
fi

# 构建JSON
JSON="{\"ai_app_type\":\"$AI_APP_TYPE\""
if [ ${#PARAMS[@]} -gt 0 ]; then
    JSON="$JSON,$(IFS=,; echo "${PARAMS[*]}")"
fi
JSON="$JSON}"

# 发送请求
if [[ "$ENDPOINT" == "health" ]]; then
    curl -s -X GET \
      -H "Authorization: Bearer $TOKEN" \
      "$URL"
else
    curl -s -X POST \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      --data-binary "$JSON" \
      "$URL"
fi
