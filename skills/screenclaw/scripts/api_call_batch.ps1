param(
    [Parameter(Mandatory=$true)][string]$ApiUrl,
    [Parameter(Mandatory=$true)][string]$Token,
    [Parameter(Mandatory=$true)][string]$SessionId,
    [Parameter(Mandatory=$true)][int]$WindowId,
    [Parameter(Mandatory=$true)][int]$MainWindowId,
    [Parameter(Mandatory=$true)][string]$Instructions,
    [Parameter(Mandatory=$true)][string]$AiAppType
)

<#
.SYNOPSIS
    ScreenClaw batch API 专用调用脚本（PowerShell）

.DESCRIPTION
    AI 通过此脚本调用 batch API，执行多步骤固定流程。
    使用简化指令格式，避免 PowerShell 终端吞双引号的问题。
    兼容PS 5.x和7.x。

    简化格式：action(key=value,key=value);action(key=value,key=value)

    支持的 action：click, long_press, swipe, drag, scroll, right_click, hover,
                   mouse_move, input_text, press_key, wait, screenshot

.PARAMETER ApiUrl
    ScreenClaw 服务地址。示例：http://localhost:12261
.PARAMETER Token
    认证令牌。示例：abc123def456
.PARAMETER AiAppType
    AI应用类型。示例：claude_code, kimi_code
.PARAMETER SessionId
    会话ID，整个会话保持不变。示例：wechat_20260405_143025
.PARAMETER WindowId
    目标窗口ID（优先用子窗口）。示例：123456
.PARAMETER MainWindowId
    主窗口ID。示例：123456
.PARAMETER Instructions
    简化格式的指令序列，分号分隔多个指令。

.EXAMPLE
    # 基本点击+输入
    .\api_call_batch.ps1 -ApiUrl "http://localhost:12261" -Token "abc123" -AiAppType "claude_code" -SessionId "sess_20260405_001" -WindowId 123456 -MainWindowId 123456 -Instructions "click(x=85,y=95);wait(duration_ms=500);input_text(x=50,y=35,text=hello)"

.EXAMPLE
    # 中文 + \n换行 + Emoji + hijack模式
    .\api_call_batch.ps1 -ApiUrl "http://localhost:12261" -Token "abc123" -AiAppType "claude_code" -SessionId "sess_20260405_001" -WindowId 123456 -MainWindowId 123456 -Instructions "input_text(x=50,y=35,text=第一行\n第二行😊,action_method=hijack);click(x=97,y=96)"

.EXAMPLE
    # 带截图验证的完整流程
    .\api_call_batch.ps1 -ApiUrl "http://localhost:12261" -Token "abc123" -AiAppType "kimi_code" -SessionId "kimi_20260405_001" -WindowId 654321 -MainWindowId 654321 -Instructions "click(x=30,y=90);wait(duration_ms=1000);input_text(x=50,y=50,text=你好世界,action_method=hijack);press_key(key=enter)"

.NOTES
    截图 API 请使用 fetch_screenshot_cli.ps1 专用脚本。
    非 batch 操作请使用 api_call.ps1。
    降级路径：api_call_batch.ps1 → api_call.py（batch 端点）→ 手动 curl
#>

# 解析简化指令格式
function Parse-Instructions {
    param([string]$Raw)

    $instructions = @()
    $segments = $Raw.Split(@(';'), [StringSplitOptions]::RemoveEmptyEntries)

    foreach ($seg in $segments) {
        $seg = $seg.Trim()
        if ($seg -match '^(\w+)\((.+)\)$') {
            $action = $Matches[1]
            $paramsStr = $Matches[2]
            $params = @{}
            foreach ($kv in $paramsStr.Split(',')) {
                if ($kv -match '^\s*(\w+)\s*=\s*(.+)\s*$') {
                    $k = $Matches[1]
                    $v = $Matches[2].Trim()
                    # 类型推断
                    if ($v -match '^\d+$') { $v = [int]$v }
                    elseif ($v -match '^\d+\.\d+$') { $v = [double]$v }
                    elseif ($v -eq 'true') { $v = $true }
                    elseif ($v -eq 'false') { $v = $false }
                    $params[$k] = $v
                }
            }
            $instructions += @{ action = $action; params = $params }
        }
        elseif ($seg -match '^(\w+)$') {
            $instructions += @{ action = $Matches[1]; params = @{} }
        }
        else {
            Write-Error "无法解析指令: $seg"
            exit 1
        }
    }
    return $instructions
}

# 强制检查必需参数
if (-not $AiAppType) {
    Write-Error "错误：ai_app_type 参数必须显式传入。例如：-AiAppType claude_code"
    exit 1
}
if (-not $SessionId) {
    Write-Error "错误：session_id 参数必须显式传入。格式：app_name_YYYYMMDD_HHMMSS"
    exit 1
}
if (-not $MainWindowId) {
    Write-Error "错误：main_window_id 参数必须显式传入。从 get_window_list 获取"
    exit 1
}

# 解析 instructions（确保始终是数组，PS单元素会被展平）
$parsedInstructions = @(Parse-Instructions -Raw $Instructions)

# 构建 body
$body = @{
    ai_app_type    = $AiAppType
    session_id     = $SessionId
    window_id      = $WindowId
    main_window_id = $MainWindowId
    instructions   = $parsedInstructions
}

# 序列化
try {
    $jsonBody = $body | ConvertTo-Json -Depth 10 -Compress
} catch {
    Write-Error "JSON序列化失败: $_"
    exit 1
}

# 发送请求 - 使用 UTF-8 字节数组，避免 PS 5.x 编码问题和代理对拆分 bug
$url = "$ApiUrl/api/batch"
$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type"  = "application/json"
}

try {
    $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($jsonBody)
    $response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $bodyBytes
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Error "API调用失败: $_"
    exit 1
}
