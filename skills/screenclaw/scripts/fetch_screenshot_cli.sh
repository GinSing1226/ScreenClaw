#!/bin/bash
# ScreenClaw 截图获取脚本（专用 - Bash）
#
# 用法：
#     bash fetch_screenshot_cli.sh <api_url> <token> <window_id> [session_id] [ai_app_type]
#
# 参数说明：
#     api_url     - ScreenClaw服务地址
#     token       - 认证令牌
#     window_id   - 窗口ID
#     session_id  - 会话ID（可选，默认default）
#     ai_app_type - AI应用类型（可选，默认claude_code）
#
# 降级路径：本脚本 → fetch_screenshot_cli.py → fetch_screenshot_cli.ps1
#
# 用法一（推荐）：直接调用API
#   bash fetch_screenshot_cli.sh "http://192.168.10.190:12261" "TOKEN123" 1380176
#   bash fetch_screenshot_cli.sh "http://192.168.10.190:12261" "TOKEN123" 1380176 "my-session"
#
# 用法二（备用）：处理已保存的JSON响应（会自动删除该JSON文件）
#   bash fetch_screenshot_cli.sh "/tmp/screenshot_response.json" "http://192.168.10.190:12261"

set -e  # 遇到错误立即退出

# 颜色输出（可选）
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    NC='\033[0m'  # No Color
else
    RED=''
    GREEN=''
    NC=''
fi

# 判断是否为本地地址
is_local_url() {
    local url="$1"
    [[ "$url" =~ (localhost|127\.0\.0\.1|::1) ]]
}

# 获取数据目录（跨平台）
get_data_dir() {
    local os_type="$(uname -s)"
    case "$os_type" in
        Darwin*)
            # macOS
            echo "$HOME/Library/Application Support/screenclaw/data"
            ;;
        *)
            # Linux
            echo "$HOME/.local/share/screenclaw/data"
            ;;
    esac
}

# 处理结果并保存图片
process_result() {
    local json_file="$1"
    local api_url="$2"
    local sess_id="${3:-default}"
    local app_type="${4:-claude_code}"
    local win_id="${5:-0}"

    # 检查jq是否安装
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}错误：缺少 jq 工具${NC}" >&2
        echo "请安装:  brew install jq  (macOS)" >&2
        echo "       sudo apt install jq  (Ubuntu/Debian)" >&2
        exit 1
    fi

    # 读取JSON
    local success=$(jq -r '.success' "$json_file")
    if [ "$success" != "true" ]; then
        local message=$(jq -r '.message // "Unknown error"' "$json_file")
        echo -e "${RED}API 错误: $message${NC}" >&2
        exit 1
    fi

    local image_path=$(jq -r '.data.image_path // empty' "$json_file")
    local image_base64=$(jq -r '.data.image_base64 // empty' "$json_file")

    if is_local_url "$api_url"; then
        # 本地场景：直接返回路径
        echo "$image_path"
    else
        # 远程场景：服务端只返回base64，客户端自己生成符合规则的路径
        # 目录规则：{ai_app_type}__{session_id}__{window_id}__{yyyy-MM-dd}
        # 文件规则：screenshot_{HHMMSS}_{rand4}.png
        local date_str=$(date +"%Y-%m-%d")
        local dir_name="${app_type}__${sess_id}__${win_id}__${date_str}"

        local time_str=$(date +"%H%M%S")
        local rand_str=$(cat /dev/urandom | tr -dc 'a-z0-9' | head -c 4)
        local filename="screenshot_${time_str}_${rand_str}.png"

        # 确定保存目录
        local base_dir=$(get_data_dir)
        local output_dir="$base_dir/$dir_name"
        mkdir -p "$output_dir"

        # 保存图片
        local output_path="$output_dir/$filename"
        echo "$image_base64" | base64 -d > "$output_path"

        echo "$output_path"
    fi
}

# 用法二：处理已保存的JSON文件
if [[ "$1" =~ \.json$ ]] && [ -n "$2" ]; then
    json_path="$1"
    api_url="$2"

    if [ ! -f "$json_path" ]; then
        echo -e "${RED}错误：JSON文件不存在: $json_path${NC}" >&2
        exit 1
    fi

    # 处理结果（JSON文件场景无法获取原始参数，使用默认值）
    output_path=$(process_result "$json_path" "$api_url" "$sess_id" "$app_type" "$win_id")
    echo "$output_path"

    # 自动删除临时JSON文件
    rm -f "$json_path" 2>/dev/null || true

    exit 0
fi

# 用法一：直接调用API
if [ $# -lt 3 ]; then
    echo "用法一（推荐）：直接调用API"
    echo "  bash fetch_screenshot_cli.sh <api_url> <token> <window_id> [session_id] [ai_app_type]"
    echo ""
    echo "示例："
    echo "  bash fetch_screenshot_cli.sh http://192.168.10.190:12261 TOKEN123 1380176"
    echo "  bash fetch_screenshot_cli.sh http://192.168.10.190:12261 TOKEN123 1380176 my-session"
    echo "  bash fetch_screenshot_cli.sh http://192.168.10.190:12261 TOKEN123 1380176 my-session claude_code"
    echo ""
    echo "用法二（备用）：处理已保存的JSON响应"
    echo "  bash fetch_screenshot_cli.sh <json_file_path> <api_url>"
    echo ""
    echo "示例："
    echo "  bash fetch_screenshot_cli.sh /tmp/screenshot_response.json http://192.168.10.190:12261"
    exit 1
fi

api_url="$1"
token="$2"
window_id="$3"
session_id="${4:-default}"
ai_app_type="${5:-claude_code}"

# 检查curl是否存在
if ! command -v curl &> /dev/null; then
    echo -e "${RED}错误：缺少 curl 工具${NC}" >&2
    exit 1
fi

# 构造请求URL
screenshot_url="${api_url%/}/api/screenshot"

# 调用API并保存到临时文件
tmp_json=$(mktemp)
trap "rm -f $tmp_json" EXIT

http_code=$(curl -s -w "%{http_code}" -o "$tmp_json" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d "{\"ai_app_type\": \"$ai_app_type\", \"session_id\": \"$session_id\", \"window_id\": $window_id, \"coordinate_type\": \"grid\"}" \
    "$screenshot_url")

if [ "$http_code" != "200" ]; then
    echo -e "${RED}API 调用失败，HTTP状态码: $http_code${NC}" >&2
    cat "$tmp_json" >&2
    exit 1
fi

# 处理结果
output_path=$(process_result "$tmp_json" "$api_url" "$session_id" "$ai_app_type" "$window_id")
echo "$output_path"
