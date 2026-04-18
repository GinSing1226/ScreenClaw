param(
    [Parameter(Mandatory=$true)][string]$ApiUrl,
    [Parameter(Mandatory=$true)][string]$Token,
    [Parameter(Mandatory=$true)][string]$Endpoint,
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$RemainingArgs
)

<#
.SYNOPSIS
    ScreenClaw 通用API调用脚本（PowerShell）

.DESCRIPTION
    AI通过此脚本调用所有ScreenClaw API（不含batch）。兼容PS 5.x和7.x。

    中文传参：直接传中文字符串即可，脚本会自动将非ASCII字符转换为 \uXXXX 编码。
        powershell ... -Endpoint input_text text=你好世界

    不支持batch端点（PowerShell终端会吞双引号导致JSON损坏），batch请用 api_call_batch.ps1。

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts/api_call.ps1 -ApiUrl http://localhost:12261 -Token TOKEN -Endpoint input_text ai_app_type=claude_code session_id=sess_001 main_window_id=123456 window_id=123456 x=50 y=35 text=你好世界

.NOTES
    截图API请使用 fetch_screenshot_cli.ps1 专用脚本。
    降级路径：api_call.py → api_call.ps1 → api_call.sh → 手动curl
#>

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
            elseif ($value.StartsWith('[') -or $value.StartsWith('{')) {
                # JSON数组或对象，尝试解析（兼容 PS 5.1）
                try {
                    $parsed = ConvertFrom-Json $value
                    # ConvertFrom-Json 在 PS 5.1 返回 PSCustomObject/array
                    # 需要转为 hashtable 以便后续 ConvertTo-Json 正确处理
                    if ($parsed -is [System.Collections.IList]) {
                        $value = @($parsed | ForEach-Object {
                            if ($_ -is [System.Management.Automation.PSCustomObject]) {
                                ConvertTo-Depth -InputObject $_
                            } else { $_ }
                        })
                    } elseif ($parsed -is [System.Management.Automation.PSCustomObject]) {
                        $value = ConvertTo-Depth -InputObject $parsed
                    } else {
                        $value = $parsed
                    }
                } catch {
                    # 解析失败则保留为字符串
                }
            }

            $params[$key] = $value
        }
    }
    return $params
}

# PSCustomObject 递归转为 Hashtable（兼容 PS 5.1）
function ConvertTo-Depth {
    param($InputObject)

    if ($InputObject -is [System.Management.Automation.PSCustomObject]) {
        $result = @{}
        foreach ($prop in $InputObject.PSObject.Properties) {
            $result[$prop.Name] = ConvertTo-Depth -InputObject $prop.Value
        }
        return $result
    }
    elseif ($InputObject -is [System.Collections.IList]) {
        return @($InputObject | ForEach-Object { ConvertTo-Depth -InputObject $_ })
    }
    else {
        return $InputObject
    }
}

# batch 端点必须使用专用脚本（简化指令格式，避免 PowerShell 吞双引号）
if ($Endpoint -eq 'batch') {
    Write-Error "Batch endpoint is not supported in this script. Please use: powershell -ExecutionPolicy Bypass -File scripts/api_call_batch.ps1 -ApiUrl <url> -Token <token> -SessionId <id> -WindowId <id> -MainWindowId <id> -Instructions 'click(x=85,y=95);wait(duration_ms=1000)'"
    exit 1
}

$scriptParams = Parse-Params -ParamArgs $RemainingArgs

# 强制检查：ai_app_type、session_id、main_window_id 必须由客户端显式传入
if (-not $scriptParams.ContainsKey('ai_app_type')) {
    Write-Error "错误：ai_app_type 参数必须显式传入。例如：ai_app_type=claude_code"
    exit 1
}
if (-not $scriptParams.ContainsKey('session_id')) {
    Write-Error "错误：session_id 参数必须显式传入。格式：app_name_YYYYMMDD_HHMMSS"
    exit 1
}
if (-not $scriptParams.ContainsKey('main_window_id')) {
    # get_window_list、wait、delegated 不需要 main_window_id
    $exemptEndpoints = @('get_window_list', 'wait', 'delegated', 'health')
    if ($Endpoint -notin $exemptEndpoints) {
        Write-Error "错误：main_window_id 参数必须显式传入。从get_window_list获取"
        exit 1
    }
}

# 构建 body hashtable
$body = @{}
foreach ($kv in $scriptParams.GetEnumerator()) {
    $body[$kv.Key] = $kv.Value
}

# 使用原生 ConvertTo-Json 序列化
try {
    $jsonBody = $body | ConvertTo-Json -Depth 10 -Compress
} catch {
    Write-Error "JSON序列化失败: $_"
    exit 1
}

# 将非ASCII字符转换为 \uXXXX 编码（兼容 PS 5.x 低版本编码问题）
$jsonBody = [regex]::Replace($jsonBody, '[^\x00-\x7F]', {
    param($m)
    '\u{0:X4}' -f [int][char]$m.Value
})

$url = "$ApiUrl/api/$Endpoint".TrimEnd('/')
$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

try {
    if ($Endpoint -eq 'health') {
        $response = Invoke-RestMethod -Uri $url -Method Get -Headers $headers
    } else {
        $response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $jsonBody
    }
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Error "API调用失败: $_"
    exit 1
}
