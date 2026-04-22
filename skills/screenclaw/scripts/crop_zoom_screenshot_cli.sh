#!/bin/bash
# ScreenClaw 裁剪放大截图脚本（专用 - Bash）
#
# 用法：
#     bash crop_zoom_screenshot_cli.sh <api_url> <token> <source_image_path> <session_id> <ai_app_type> center_x=<值> center_y=<值> crop_width=<值> crop_height=<值> [zoom_scale=<值>]
#
# 参数说明：
#     api_url            - ScreenClaw服务地址
#     token              - 认证令牌
#     source_image_path  - 原始图片路径（screenshot或scroll_screenshot返回的路径）
#     session_id         - 会话ID（必需）
#     ai_app_type        - AI应用类型（必需）
#
# 裁剪参数（必需）：
#     center_x=<值>      - 裁剪区域中心点横坐标百分比(0-100)
#     center_y=<值>      - 裁剪区域中心点纵坐标百分比(0-100)
#     crop_width=<值>    - 裁剪区域总宽度百分比(0-100)
#     crop_height=<值>   - 裁剪区域总高度百分比(0-100)
#
# 可选参数：
#     zoom_scale=<值>    - 放大倍数(1.0-10.0)，默认2.0
#
# 降级路径：本脚本 → crop_zoom_screenshot_cli.py → crop_zoom_screenshot_cli.ps1

set -e

if [ -t 1 ]; then
    RED='\033[0;31m'
    NC='\033[0m'
else
    RED=''
    NC=''
fi

is_local_url() {
    local url="$1"
    [[ "$url" =~ (localhost|127\.0\.0\.1|::1) ]]
}

get_data_dir() {
    local os_type="$(uname -s)"
    case "$os_type" in
        Darwin*) echo "$HOME/Library/Application Support/screenclaw/data" ;;
        *)       echo "$HOME/.local/share/screenclaw/data" ;;
    esac
}

# 用法检查
if [ $# -lt 5 ]; then
    echo "用法：bash crop_zoom_screenshot_cli.sh <api_url> <token> <source_image_path> <session_id> <ai_app_type> center_x=<值> center_y=<值> crop_width=<值> crop_height=<值> [zoom_scale=<值>]"
    echo ""
    echo "示例："
    echo "  bash crop_zoom_screenshot_cli.sh http://localhost:12261 TOKEN /path/to/screenshot.png sess_001 claude_code center_x=55 center_y=65 crop_width=20 crop_height=20"
    echo "  bash crop_zoom_screenshot_cli.sh http://localhost:12261 TOKEN /path/to/screenshot.png sess_001 claude_code center_x=55 center_y=65 crop_width=10 crop_height=10 zoom_scale=4.0"
    exit 1
fi

api_url="$1"
token="$2"
source_image_path="$3"
session_id="$4"
ai_app_type="$5"
shift 5

# 解析参数
CENTER_X=""
CENTER_Y=""
CROP_WIDTH=""
CROP_HEIGHT=""
ZOOM_SCALE=""
OTHER_PARAMS=""

for arg in "$@"; do
    if [[ "$arg" == "center_x="* ]]; then
        CENTER_X="${arg#center_x=}"
    elif [[ "$arg" == "center_y="* ]]; then
        CENTER_Y="${arg#center_y=}"
    elif [[ "$arg" == "crop_width="* ]]; then
        CROP_WIDTH="${arg#crop_width=}"
    elif [[ "$arg" == "crop_height="* ]]; then
        CROP_HEIGHT="${arg#crop_height=}"
    elif [[ "$arg" == "zoom_scale="* ]]; then
        ZOOM_SCALE="${arg#zoom_scale=}"
    fi
done

# 必填检查
if [ -z "$CENTER_X" ] || [ -z "$CENTER_Y" ] || [ -z "$CROP_WIDTH" ] || [ -z "$CROP_HEIGHT" ]; then
    echo -e "${RED}错误：缺少必需参数（center_x, center_y, crop_width, crop_height）${NC}" >&2
    exit 1
fi

# 构建JSON
ZOOM_JSON=""
if [ -n "$ZOOM_SCALE" ]; then
    ZOOM_JSON=",\"zoom_scale\":$ZOOM_SCALE"
fi

JSON="{\"ai_app_type\":\"$ai_app_type\",\"session_id\":\"$session_id\",\"source_image_path\":\"$source_image_path\",\"center_x\":$CENTER_X,\"center_y\":$CENTER_Y,\"crop_width\":$CROP_WIDTH,\"crop_height\":$CROP_HEIGHT$ZOOM_JSON}"

# 调用API
url="${api_url%/}/api/crop_zoom_screenshot"

if ! command -v jq &> /dev/null; then
    echo -e "${RED}错误：缺少 jq 工具${NC}" >&2
    echo "请安装:  brew install jq  (macOS)" >&2
    echo "       sudo apt install jq  (Ubuntu/Debian)" >&2
    exit 1
fi

tmp_json=$(mktemp)
trap "rm -f $tmp_json" EXIT

http_code=$(curl -s -w "%{http_code}" -o "$tmp_json" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d "$JSON" \
    "$url")

if [ "$http_code" != "200" ]; then
    echo -e "${RED}API 调用失败，HTTP状态码: $http_code${NC}" >&2
    cat "$tmp_json" >&2
    exit 1
fi

success=$(jq -r '.success' "$tmp_json")
if [ "$success" != "true" ]; then
    message=$(jq -r '.message // "Unknown error"' "$tmp_json")
    echo -e "${RED}API 错误: $message${NC}" >&2
    exit 1
fi

image_path=$(jq -r '.data.image_path // empty' "$tmp_json")
image_base64=$(jq -r '.data.image_base64 // empty' "$tmp_json")

if is_local_url "$api_url"; then
    echo "$image_path"
else
    date_str=$(date +"%Y-%m-%d")
    dir_name="${ai_app_type}__${session_id}__${date_str}"
    time_str=$(date +"%H%M%S")
    rand_str=$(cat /dev/urandom | tr -dc 'a-z0-9' | head -c 4)
    filename="crop_zoom_${time_str}_${rand_str}.png"

    base_dir=$(get_data_dir)
    output_dir="$base_dir/$dir_name"
    mkdir -p "$output_dir"

    output_path="$output_dir/$filename"
    echo "$image_base64" | base64 -d > "$output_path"

    echo "$output_path"
fi

echo "Crop zoom successful. If details are still unclear, adjust parameters and process the same source image again."
