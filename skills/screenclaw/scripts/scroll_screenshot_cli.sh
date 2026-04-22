#!/bin/bash
# ScreenClaw 滚动长截图脚本（Bash 版本）
#
# 用法：
#     bash scroll_screenshot_cli.sh <api_url> <token> <window_id> <session_id> <ai_app_type> <main_window_id> [参数...]
#
# 参数说明：
#     api_url        - ScreenClaw服务地址
#     token          - 认证令牌
#     window_id      - 窗口ID
#     session_id     - 会话ID（必需）
#     ai_app_type    - AI应用类型（必需）
#     main_window_id - 主窗口ID（必需，从get_window_list获取）
#
# 滚动参数（可选）：
#     max_scrolls=<值>       - 最大滚动次数（不指定则使用服务端配置）
#     scroll_percent=<值>    - 初始滚动幅度(0.1-0.95)（不指定则使用服务端配置）
#     scroll_wait=<值>       - 滚动等待时间(秒)（不指定则使用服务端配置）
#     x=<值>                 - 滚动位置横坐标(0-100)，默认50（中心）
#     y=<值>                 - 滚动位置纵坐标(0-100)，默认50（中心）
#
# 高级参数（可选）：
#     max_adjust_retries=<值> - 自适应最大调整次数（不指定则使用服务端配置）
#     target_overlap_min=<值> - 目标重叠下限(0.10-0.50)（不指定则使用服务端配置）
#     target_overlap_max=<值> - 目标重叠上限(0.20-0.60)（不指定则使用服务端配置）
#     stop_threshold=<值>     - 停止阈值(1~0.0001，即100%~0.01%)（不指定则使用服务端配置）
#
# 说明：
#     - 未指定的参数将使用服务端 config.json 中的默认值
#     - 本功能内部硬编码使用 hijack 模式
#     - 本功能不支持网格坐标绘制
#     - 远程场景的截图保存目录规则：{ai_app_type}__{session_id}__{yyyy-MM-dd}/
#     - 系统会自动动态调整滚动幅度以获得最佳重叠，接口会返回实际使用的幅度
#
# 降级路径：scroll_screenshot_cli.py → scroll_screenshot_cli.ps1 → 本脚本
#
# 示例：
#     bash scroll_screenshot_cli.sh "http://192.168.10.190:12261" "TOKEN123" 1380176 "my-session" "claude_code" 1380176
#     bash scroll_screenshot_cli.sh "http://192.168.10.190:12261" "TOKEN123" 1380176 "my-session" "claude_code" 1380176 "max_scrolls=10" "scroll_percent=0.9"

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
    local session_id="$3"
    local ai_app_type="$4"

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
        local error_code=$(jq -r '.error_code // ""' "$json_file")
        echo -e "${RED}API 错误: $message${NC}" >&2
        if [ "$error_code" = "UNSUPPORTED_MODE" ]; then
            echo "提示：滚动长截图只支持 hijack 或 delegated 模式" >&2
        fi
        exit 1
    fi

    local image_path=$(jq -r '.data.image_path // empty' "$json_file")
    local image_base64=$(jq -r '.data.image_base64 // empty' "$json_file")

    if is_local_url "$api_url"; then
        # 本地场景：直接返回路径
        echo "$image_path"
    else
        # 远程场景：服务端只返回base64，客户端自己生成符合规则的路径
        local date_str=$(date +"%Y-%m-%d")
        local dir_name="${ai_app_type}__${session_id}__${date_str}"

        local time_str=$(date +"%H%M%S")
        local rand_str=$(cat /dev/urandom | tr -dc 'a-z0-9' | head -c 4)
        local filename="scroll_screenshot_${time_str}_${rand_str}.png"

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

# 检查参数
if [ $# -lt 6 ]; then
    echo "用法："
    echo "  bash scroll_screenshot_cli.sh <api_url> <token> <window_id> <session_id> <ai_app_type> <main_window_id> [参数...]"
    echo ""
    echo "示例："
    echo "  bash scroll_screenshot_cli.sh http://192.168.10.190:12261 TOKEN123 1380176 my-session claude_code 1380176"
    echo "  bash scroll_screenshot_cli.sh http://192.168.10.190:12261 TOKEN123 1380176 my-session claude_code 1380176 max_scrolls=10 scroll_percent=0.9"
    echo ""
    echo "滚动参数（可选）："
    echo "  max_scrolls=<值>       - 最大滚动次数（不指定则使用服务端配置）"
    echo "  scroll_percent=<值>    - 初始滚动幅度(0.1-0.95)（不指定则使用服务端配置）"
    echo "  scroll_wait=<值>       - 滚动等待时间(秒)（不指定则使用服务端配置）"
    echo "  x=<值>                 - 滚动位置横坐标(0-100)，默认50（中心）"
    echo "  y=<值>                 - 滚动位置纵坐标(0-100)，默认50（中心）"
    echo ""
    echo "高级参数（可选）："
    echo "  max_adjust_retries=<值> - 自适应最大调整次数（不指定则使用服务端配置）"
    echo "  target_overlap_min=<值> - 目标重叠下限(0.10-0.50)（不指定则使用服务端配置）"
    echo "  target_overlap_max=<值> - 目标重叠上限(0.20-0.60)（不指定则使用服务端配置）"
    echo "  stop_threshold=<值>     - 停止阈值(1~0.0001，即100%~0.01%)（不指定则使用服务端配置）"
    exit 1
fi

api_url="$1"
token="$2"
window_id="$3"
session_id="$4"
ai_app_type="$5"
main_window_id="$6"
shift 6  # 移除前6个参数，剩余的是可选参数

# 检查curl是否存在
if ! command -v curl &> /dev/null; then
    echo -e "${RED}错误：缺少 curl 工具${NC}" >&2
    exit 1
fi

# 基础JSON（只包含必需参数）
json_body="{
  \"ai_app_type\": \"$ai_app_type\",
  \"session_id\": \"$session_id\",
  \"window_id\": $window_id,
  \"main_window_id\": $main_window_id,
  \"x\": 50,
  \"y\": 50"

# 初始化变量（避免未定义错误）
max_scrolls=""
scroll_percent=""
scroll_wait=""
max_adjust_retries=""

# 用于跟踪是否指定了参数（用于显示）
max_scrolls_specified=false
scroll_percent_specified=false
scroll_wait_specified=false
max_adjust_retries_specified=false

# 解析参数并动态添加到JSON
for arg in "$@"; do
    case "$arg" in
        max_scrolls=*)
            max_scrolls="${arg#max_scrolls=}"
            json_body="$json_body,
  \"max_scrolls\": $max_scrolls"
            max_scrolls_specified=true
            ;;
        scroll_percent=*)
            scroll_percent="${arg#scroll_percent=}"
            json_body="$json_body,
  \"scroll_percent\": $scroll_percent"
            scroll_percent_specified=true
            ;;
        scroll_wait=*)
            scroll_wait="${arg#scroll_wait=}"
            json_body="$json_body,
  \"scroll_wait\": $scroll_wait"
            scroll_wait_specified=true
            ;;
        x=*)
            x="${arg#x=}"
            # 更新x值
            json_body=$(echo "$json_body" | sed 's/"x": 50/"x": '"$x"'/')
            ;;
        y=*)
            y="${arg#y=}"
            # 更新y值
            json_body=$(echo "$json_body" | sed 's/"y": 50/"y": '"$y"'/')
            ;;
        max_adjust_retries=*)
            max_adjust_retries="${arg#max_adjust_retries=}"
            json_body="$json_body,
  \"max_adjust_retries\": $max_adjust_retries"
            max_adjust_retries_specified=true
            ;;
        target_overlap_min=*)
            target_overlap_min="${arg#target_overlap_min=}"
            json_body="$json_body,
  \"target_overlap_min\": $target_overlap_min"
            ;;
        target_overlap_max=*)
            target_overlap_max="${arg#target_overlap_max=}"
            json_body="$json_body,
  \"target_overlap_max\": $target_overlap_max"
            ;;
        stop_threshold=*)
            stop_threshold="${arg#stop_threshold=}"
            json_body="$json_body,
  \"stop_threshold\": $stop_threshold"
            ;;
    esac
done

# 关闭JSON
json_body="$json_body
}"

# 构造请求URL
scroll_screenshot_url="${api_url%/}/api/scroll_screenshot"

# 打印开始信息（显示实际使用的值或"使用配置文件默认值"）
echo "开始滚动长截图..."
if [ "$max_scrolls_specified" = true ]; then
    echo "  最大滚动次数: $max_scrolls"
else
    echo "  最大滚动次数: 使用配置文件默认值"
fi

if [ "$scroll_percent_specified" = true ]; then
    echo "  初始滚动幅度: $(awk "BEGIN {printf \"%.0f\", $scroll_percent * 100}")%"
else
    echo "  初始滚动幅度: 使用配置文件默认值"
fi

echo "  滚动位置: ($(echo "$json_body" | grep -o '"x": [0-9.]*' | cut -d' ' -f2), $(echo "$json_body" | grep -o '"y": [0-9.]*' | cut -d' ' -f2))"

if [ "$scroll_wait_specified" = true ]; then
    echo "  等待时间: $scroll_wait s"
else
    echo "  等待时间: 使用配置文件默认值"
fi

if [ "$max_adjust_retries_specified" = true ]; then
    echo "  最大调整次数: $max_adjust_retries"
else
    echo "  最大调整次数: 使用配置文件默认值"
fi

# 调用API并保存到临时文件
tmp_json=$(mktemp)
trap "rm -f $tmp_json" EXIT

http_code=$(curl -s -w "%{http_code}" -o "$tmp_json" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d "$json_body" \
    "$scroll_screenshot_url")

if [ "$http_code" != "200" ]; then
    echo -e "${RED}API 调用失败，HTTP状态码: $http_code${NC}" >&2
    cat "$tmp_json" >&2
    exit 1
fi

# 处理结果
output_path=$(process_result "$tmp_json" "$api_url" "$session_id" "$ai_app_type")

# 打印完成信息
scroll_count=$(jq -r '.data.scroll_count // 0' "$tmp_json")
actual_scroll_percent=$(jq -r '.data.actual_scroll_percent // 0' "$tmp_json")
fixed_header=$(jq -r '.data.fixed_header // 0' "$tmp_json")
fixed_footer=$(jq -r '.data.fixed_footer // 0' "$tmp_json")

echo ""
echo "滚动长截图完成！"
echo "  实际截图数量: $scroll_count"
echo "  实际滚动幅度: $(awk "BEGIN {printf \"%.1f\", $actual_scroll_percent * 100}")%"
if [ "$fixed_header" -gt 0 ]; then
    echo "  检测到固定头部: $fixed_header px"
fi
if [ "$fixed_footer" -gt 0 ]; then
    echo "  检测到固定底部: $fixed_footer px"
fi
echo "  图片保存路径: $output_path"

# 输出路径（供脚本捕获）
echo "$output_path"
