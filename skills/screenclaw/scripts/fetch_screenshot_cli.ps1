param(
    [Parameter(Mandatory=$true)][string]$ApiUrl,
    [Parameter(Mandatory=$true)][string]$Token,
    [Parameter(Mandatory=$true)][int]$WindowId,
    [Parameter(Mandatory=$true)][string]$SessionId,
    [Parameter(Mandatory=$true)][string]$AiAppType,
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

            # 类型转换
            if ($value -eq 'true') { $value = $true }
            elseif ($value -eq 'false') { $value = $false }
            elseif ($value -match '^\d+$') { $value = [int]$value }
            elseif ($value -match '^\d+\.\d+$') { $value = [double]$value }

            $params[$key] = $value
        }
    }
    return $params
}

# 构建网格参数函数
function Build-GridParams {
    param([hashtable]$Params)

    $grid = @{}
    $coordinate = @{}

    # 网格参数
    if ($Params.ContainsKey('grid_density')) { $grid['density'] = $Params['grid_density'] }
    if ($Params.ContainsKey('grid_opacity')) { $grid['opacity'] = $Params['grid_opacity'] }
    if ($Params.ContainsKey('grid_color')) { $grid['color'] = $Params['grid_color'] }

    # 数字参数
    if ($Params.ContainsKey('number_density')) { $coordinate['number_density'] = $Params['number_density'] }
    if ($Params.ContainsKey('number_decimal')) { $coordinate['number_decimal'] = $Params['number_decimal'] }
    if ($Params.ContainsKey('number_size')) { $coordinate['number_size'] = $Params['number_size'] }
    if ($Params.ContainsKey('number_color')) { $coordinate['number_color'] = $Params['number_color'] }
    if ($Params.ContainsKey('number_opacity')) { $coordinate['number_opacity'] = $Params['number_opacity'] }

    $result = @{}
    if ($grid.Count -gt 0) { $result['grid'] = $grid }
    if ($coordinate.Count -gt 0) { $result['coordinate'] = $coordinate }
    return $result
}

# 转换为JSON字符串函数
function ConvertTo-JsonString {
    param($Value)

    if ($Value -is [string]) {
        $result = ""
        foreach ($char in $Value.ToCharArray()) {
            $code = [int][char]$char
            if ($code -eq 92) {
                $result += '\\'
            } elseif ($code -eq 34) {
                $result += '\"'
            } elseif ($code -eq 10) {
                $result += '\n'
            } elseif ($code -eq 13) {
                $result += '\r'
            } elseif ($code -eq 9) {
                $result += '\t'
            } elseif ($code -gt 127) {
                $result += [string]::Format('\u{0:x4}', $code)
            } else {
                $result += $char
            }
        }
        return '"' + $result + '"'
    } elseif ($Value -is [bool]) {
        return $Value.ToString().ToLower()
    } elseif ($Value -is [int] -or $Value -is [double]) {
        return $Value.ToString()
    } elseif ($Value -is [hashtable]) {
        $parts = @()
        foreach ($kv in $Value.GetEnumerator()) {
            $keyStr = ConvertTo-JsonString -Value $kv.Key
            $valueStr = ConvertTo-JsonString -Value $kv.Value
            $parts += "${keyStr}:${valueStr}"
        }
        return "{$($parts -join ',')}"
    } else {
        return "null"
    }
}

# 解析参数
$scriptParams = Parse-Params -ParamArgs $RemainingArgs
$gridParams = Build-GridParams -Params $scriptParams

$screenshotUrl = "$ApiUrl/api/screenshot"

$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

# 构建基础body
$body = @{
    ai_app_type = $AiAppType
    session_id = $SessionId
    window_id = $WindowId
    coordinate_type = "grid"
}

# 合并网格参数
foreach ($kv in $gridParams.GetEnumerator()) {
    $body[$kv.Key] = $kv.Value
}

$jsonBody = ConvertTo-JsonString -Value $body

try {
    $response = Invoke-RestMethod -Uri $screenshotUrl -Method Post -Headers $headers -Body $jsonBody
}
catch {
    Write-Error "API调用失败: $_"
    exit 1
}

if (-not $response.success) {
    Write-Error "API错误: $($response.message)"
    exit 1
}

$isLocal = $ApiUrl -match "localhost|127\.0\.0\.1|::1"

if ($isLocal) {
    Write-Output $response.data.image_path
}
else {
    # 远程场景：服务端只返回base64，客户端自己生成符合规则的路径
    # 目录规则：{ai_app_type}__{session_id}__{window_id}__{yyyy-MM-dd}
    # 文件规则：screenshot_{HHMMSS}_{rand4}.png
    $dateStr = Get-Date -Format "yyyy-MM-dd"
    $dirName = "${AiAppType}__${SessionId}__${WindowId}__${dateStr}"

    $timeStr = Get-Date -Format "HHmmss"
    $randChars = -join ((97..122) + (48..57) | Get-Random -Count 4 | ForEach-Object { [char]$_ })
    $filename = "screenshot_${timeStr}_${randChars}.png"

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
        Write-Output $outputPath
    }
    catch {
        Write-Error "保存图片失败: $_"
        exit 1
    }
}
