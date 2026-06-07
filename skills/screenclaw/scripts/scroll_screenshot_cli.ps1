# ScreenClaw 滚动长截图脚本（PowerShell 版本）
#
# 用法：
#     powershell -ExecutionPolicy Bypass -File scroll_screenshot_cli.ps1 <api_url> <token> <window_id> <session_id> <ai_app_type> <main_window_id> [参数...]
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
#     max_scrolls=<值>       - 最大滚动次数，默认5
#     scroll_percent=<值>    - 初始滚动幅度(0.1-0.95)，默认0.85
#     scroll_wait=<值>       - 滚动等待时间(秒)，默认1.0
#     x=<值>                 - 滚动位置横坐标(0-100)，默认50（中心）
#     y=<值>                 - 滚动位置纵坐标(0-100)，默认50（中心）
#
# 高级参数（可选）：
#     max_adjust_retries=<值> - 自适应最大调整次数，默认4
#     target_overlap_min=<值> - 目标重叠下限(0.10-0.50)，默认0.35
#     target_overlap_max=<值> - 目标重叠上限(0.20-0.60)，默认0.45
#     stop_threshold=<值>     - 停止阈值(0.0-0.01)，默认0.0001
#
# 说明：
#     - 本功能内部硬编码使用 hijack 模式
#     - 本功能不支持网格坐标绘制
#     - 远程场景的截图保存目录规则：{ai_app_type}__{session_id}__{yyyy-MM-dd}/
#     - 系统会自动动态调整滚动幅度以获得最佳重叠，接口会返回实际使用的幅度
#
# 降级路径：scroll_screenshot_cli.py → 本脚本 → scroll_screenshot_cli.sh
#
# 示例：
#     powershell -ExecutionPolicy Bypass -File scroll_screenshot_cli.ps1 "http://192.168.10.190:12261" "TOKEN123" 1380176 "my-session" "claude_code" 1380176
#     powershell -ExecutionPolicy Bypass -File scroll_screenshot_cli.ps1 "http://192.168.10.190:12261" "TOKEN123" 1380176 "my-session" "claude_code" 1380176 "max_scrolls=10" "scroll_percent=0.9"

param(
    [Parameter(Mandatory=$true)][string]$ApiUrl,
    [Parameter(Mandatory=$true)][string]$Token,
    [Parameter(Mandatory=$true)][int]$WindowId,
    [Parameter(Mandatory=$true)][string]$SessionId,
    [Parameter(Mandatory=$true)][string]$AiAppType,
    [Parameter(Mandatory=$true)][int]$MainWindowId,
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$RemainingArgs
)

# 解析参数函数
function Parse-Params {
    param([string[]]$ParamArgs)

    $params = @{}
    foreach ($arg in $ParamArgs) {
        if ($arg -match '^(.+?)=(.+)$') {
            $key = $Matches[1]
            $value = $Matches[2]

            if ($value -eq 'true') { $value = $true }
            elseif ($value -eq 'false') { $value = $false }
            elseif ($value -match '^\d+$') { $value = [int]$value }
            elseif ($value -match '^\d+\.\d+$') { $value = [double]$value }

            $params[$key] = $value
        }
    }
    return $params
}

# 解析参数
$scriptParams = Parse-Params -ParamArgs $RemainingArgs

# 基础请求体（只包含必需参数，可选参数让服务端使用 config.json 默认值）
$body = @{
    ai_app_type = $AiAppType
    session_id = $SessionId
    window_id = $WindowId
    main_window_id = $MainWindowId
}

# 只添加用户指定的参数（不设置默认值）
if ($scriptParams.ContainsKey('max_scrolls')) { $body.max_scrolls = $scriptParams['max_scrolls'] }
if ($scriptParams.ContainsKey('scroll_percent')) { $body.scroll_percent = $scriptParams['scroll_percent'] }
if ($scriptParams.ContainsKey('scroll_wait')) { $body.scroll_wait = $scriptParams['scroll_wait'] }
if ($scriptParams.ContainsKey('x')) { $body.x = $scriptParams['x'] }
else { $body.x = 50 }  # 坐标默认值

if ($scriptParams.ContainsKey('y')) { $body.y = $scriptParams['y'] }
else { $body.y = 50 }  # 坐标默认值

if ($scriptParams.ContainsKey('max_adjust_retries')) { $body.max_adjust_retries = $scriptParams['max_adjust_retries'] }
if ($scriptParams.ContainsKey('target_overlap_min')) { $body.target_overlap_min = $scriptParams['target_overlap_min'] }
if ($scriptParams.ContainsKey('target_overlap_max')) { $body.target_overlap_max = $scriptParams['target_overlap_max'] }
if ($scriptParams.ContainsKey('stop_threshold')) { $body.stop_threshold = $scriptParams['stop_threshold'] }

# 构建请求
$scrollScreenshotUrl = "$ApiUrl/api/scroll_screenshot"

$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

# 转换为 JSON
$jsonBody = $body | ConvertTo-Json -Compress

# 打印开始信息（显示实际使用的值或"使用配置文件默认值"）
Write-Host "开始滚动长截图..."
$maxDisplay = if ($scriptParams.ContainsKey('max_scrolls')) { $scriptParams['max_scrolls'] } else { "使用配置文件默认值" }
$percentDisplay = if ($scriptParams.ContainsKey('scroll_percent')) { "$($scriptParams['scroll_percent'] * 100)%" } else { "使用配置文件默认值" }
$waitDisplay = if ($scriptParams.ContainsKey('scroll_wait')) { "$($scriptParams['scroll_wait'])s" } else { "使用配置文件默认值" }
$retryDisplay = if ($scriptParams.ContainsKey('max_adjust_retries')) { $scriptParams['max_adjust_retries'] } else { "使用配置文件默认值" }
Write-Host "  最大滚动次数: $maxDisplay"
Write-Host "  初始滚动幅度: $percentDisplay"
Write-Host "  滚动位置: ($($body.x), $($body.y))"
Write-Host "  等待时间: $waitDisplay"
Write-Host "  最大调整次数: $retryDisplay"

try {
    $response = Invoke-RestMethod -Uri $scrollScreenshotUrl -Method Post -Headers $headers -Body $jsonBody -TimeoutSec 300
}
catch {
    Write-Error "API调用失败: $_"
    exit 1
}

if (-not $response.success) {
    Write-Error "API错误: $($response.message)"
    if ($response.error_code -eq "UNSUPPORTED_MODE") {
        Write-Host "提示：滚动长截图只支持 hijack 或 delegated 模式"
    }
    exit 1
}

# 处理结果
$isLocal = $ApiUrl -match "localhost|127\.0\.0\.1|::1"

if ($isLocal) {
    # 本地场景：直接返回路径
    $outputPath = $response.data.image_path
}
else {
    # 远程场景：服务端只返回base64，客户端自己生成符合规则的路径
    $dateStr = Get-Date -Format "yyyy-MM-dd"
    $dirName = "${AiAppType}__${SessionId}__${dateStr}"

    $timeStr = Get-Date -Format "HHmmss"
    $randChars = -join ((97..122) + (48..57) | Get-Random -Count 4 | ForEach-Object { [char]$_ })
    $filename = "scroll_screenshot_${timeStr}_${randChars}.png"

    # 确保data目录存在
    $dataDir = "$env:APPDATA\screenclaw\data"
    if (-not (Test-Path $dataDir)) {
        New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
    }

    $outputDir = Join-Path $dataDir $dirName

    try {
        if (-not (Test-Path $outputDir)) {
            New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
        }
    }
    catch {
        Write-Error "创建目录失败: $_"
        exit 1
    }

    $outputPath = Join-Path $outputDir $filename

    try {
        $bytes = [Convert]::FromBase64String($response.data.image_base64)
        [System.IO.File]::WriteAllBytes($outputPath, $bytes)
    }
    catch {
        Write-Error "保存图片失败: $_"
        exit 1
    }
}

# 打印完成信息
$scrollCount = $response.data.scroll_count
$actualScrollPercent = $response.data.actual_scroll_percent
$fixedHeader = $response.data.fixed_header
$fixedFooter = $response.data.fixed_footer

Write-Host "`n滚动长截图完成！"
Write-Host "  实际截图数量: $scrollCount"
Write-Host "  实际滚动幅度: $($actualScrollPercent * 100)%"
if ($fixedHeader -gt 0) {
    Write-Host "  检测到固定头部: $fixedHeader px"
}
if ($fixedFooter -gt 0) {
    Write-Host "  检测到固定底部: $fixedFooter px"
}
Write-Host "  图片保存路径: $outputPath"
Write-Output $outputPath
