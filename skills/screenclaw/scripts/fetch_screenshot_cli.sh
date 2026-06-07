#!/bin/bash
# ScreenClaw 截图获取脚本（专用 - Bash）
#
# 用法：
#     bash fetch_screenshot_cli.sh <api_url> <token> <window_id> <session_id> <ai_app_type> <main_window_id> [参数...]
#
# 参数说明：
#     api_url        - ScreenClaw服务地址
#     token          - 认证令牌
#     window_id      - 窗口ID
#     session_id     - 会话ID（必需）
#     ai_app_type    - AI应用类型（必需）
#     main_window_id - 主窗口ID（必需，从get_window_list获取）
#
# 网格参数（可选）：
#     grid_density=<值>      - 每格宽度（像素），值越小网格越密，默认5.0
#     grid_opacity=<值>       - 网格透明度(0-100)，默认50
#     grid_color=<值>         - 网格颜色，默认#ff0000
#
# 颜色模式（可选）：
#     color_mode=<值>         - 颜色模式：grayscale（灰度）/color（原色），默认grayscale
#
# 数字参数（可选）：
#     number_density=<值>     - 数字密度，默认2
#     number_decimal=<值>      - 小数位数(0-4)，默认0
#     number_size=<值>         - 字体大小(4-32)，默认12
#     number_color=<值>        - 数字颜色，默认#ff0000
#     number_opacity=<值>      - 数字透明度(0-100)，默认100
#
# 降级路径：本脚本 → fetch_screenshot_cli.py → fetch_screenshot_cli.ps1
#
# 用法一（推荐）：直接调用API
#   bash fetch_screenshot_cli.sh "http://192.168.10.190:12261" "TOKEN123" 1380176 "my-session" "claude_code" 1380176
#   bash fetch_screenshot_cli.sh "http://192.168.10.190:12261" "TOKEN123" 1380176 "my-session" "claude_code" 1380176 "grid_density=8" "number_size=14"
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

# 构建网格和数字参数
build_grid_params() {
    local grid_parts=""
    local coord_parts=""

    for arg in "$@"; do
        if [[ "$arg" =~ ^(.+?)=(.+)$ ]]; then
            key="${BASH_REMATCH[1]}"
            value="${BASH_REMATCH[2]}"

            case "$key" in
                grid_density)
                    grid_parts="$grid_parts,\"density\":$value"
                    ;;
                grid_opacity)
                    grid_parts="$grid_parts,\"opacity\":$value"
                    ;;
                grid_color)
                    grid_parts="$grid_parts,\"color\":\"$value\""
                    ;;
                number_density)
                    coord_parts="$coord_parts,\"number_density\":$value"
                    ;;
                number_decimal)
                    coord_parts="$coord_parts,\"number_decimal\":$value"
                    ;;
                number_size)
                    coord_parts="$coord_parts,\"number_size\":$value"
                    ;;
                number_color)
                    coord_parts="$coord_parts,\"number_color\":\"$value\""
                    ;;
                number_opacity)
                    coord_parts="$coord_parts,\"number_opacity\":$value"
                    ;;
            esac
        fi
    done

    local result=""
    if [ -n "$grid_parts" ]; then
        grid_parts="${grid_parts:1}"  # 移除开头的逗号
        result="$result,\"grid\":{$grid_parts}"
    fi
    if [ -n "$coord_parts" ]; then
        coord_parts="${coord_parts:1}"  # 移除开头的逗号
        result="$result,\"coordinate\":{$coord_parts}"
    fi

    echo "$result"
}

# 处理结果并保存图片
process_result() {
    local json_file="$1"
    local api_url="$2"

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
        # 从JSON中提取参数信息（如果有的话）
        local sess_id=$(jq -r '.data.session_id // "default"' "$json_file")
        local app_type=$(jq -r '.data.ai_app_type // "claude_code"' "$json_file")

        local date_str=$(date +"%Y-%m-%d")
        local dir_name="${app_type}__${sess_id}__${date_str}"

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

    # 处理结果
    output_path=$(process_result "$json_path" "$api_url")
    echo "$output_path"

    # 自动删除临时JSON文件
    rm -f "$json_path" 2>/dev/null || true

    exit 0
fi

# 用法一：直接调用API
if [ $# -lt 6 ]; then
    echo "用法一（推荐）：直接调用API"
    echo "  bash fetch_screenshot_cli.sh <api_url> <token> <window_id> <session_id> <ai_app_type> <main_window_id> [参数...]"
    echo ""
    echo "示例："
    echo "  bash fetch_screenshot_cli.sh http://192.168.10.190:12261 TOKEN123 1380176 my-session claude_code 1380176"
    echo "  bash fetch_screenshot_cli.sh http://192.168.10.190:12261 TOKEN123 1380176 my-session claude_code 1380176 grid_density=8 number_size=14"
    echo ""
    echo "网格参数（可选）："
    echo "  grid_density=<值>      - 每格宽度（像素），值越小网格越密，默认5.0"
    echo "  grid_opacity=<值>       - 网格透明度(0-100)，默认50"
    echo "  grid_color=<值>         - 网格颜色，默认#ff0000"
    echo ""
    echo "颜色模式（可选）："
    echo "  color_mode=<值>         - 颜色模式：grayscale（灰度）/color（原色），默认grayscale"
    echo ""
    echo "数字参数（可选）："
    echo "  number_density=<值>     - 数字密度，默认2"
    echo "  number_decimal=<值>      - 小数位数(0-4)，默认0"
    echo "  number_size=<值>         - 字体大小(4-32)，默认12"
    echo "  number_color=<值>        - 数字颜色，默认#ff0000"
    echo "  number_opacity=<值>      - 数字透明度(0-100)，默认100"
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
session_id="$4"
ai_app_type="$5"
main_window_id="$6"
shift 6  # 移除前6个参数，剩余的是网格/数字参数

# 检查curl是否存在
if ! command -v curl &> /dev/null; then
    echo -e "${RED}错误：缺少 curl 工具${NC}" >&2
    exit 1
fi

# 构造请求URL
screenshot_url="${api_url%/}/api/screenshot"

# 解析 coordinate_type 参数（默认 grid）
COORDINATE_TYPE="grid"
COLOR_MODE="grayscale"
for arg in "$@"; do
    if [[ "$arg" == "coordinate_type="* ]]; then
        COORDINATE_TYPE="${arg#coordinate_type=}"
    fi
    if [[ "$arg" == "color_mode="* ]]; then
        COLOR_MODE="${arg#color_mode=}"
    fi
done

# 构建网格和数字参数
grid_params=$(build_grid_params "$@")

# 构建JSON
JSON="{\"ai_app_type\":\"$ai_app_type\",\"session_id\":\"$session_id\",\"window_id\":$window_id,\"main_window_id\":$main_window_id,\"coordinate_type\":\"$COORDINATE_TYPE\",\"color_mode\":\"$COLOR_MODE\"$grid_params}"

# 调用API并保存到临时文件
tmp_json=$(mktemp)
trap "rm -f $tmp_json" EXIT

http_code=$(curl -s -w "%{http_code}" -o "$tmp_json" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d "$JSON" \
    "$screenshot_url")

if [ "$http_code" != "200" ]; then
    echo -e "${RED}API 调用失败，HTTP状态码: $http_code${NC}" >&2
    cat "$tmp_json" >&2
    exit 1
fi

# 处理结果
output_path=$(process_result "$tmp_json" "$api_url")
echo "$output_path"
