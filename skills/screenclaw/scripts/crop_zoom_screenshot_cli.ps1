param(
    [Parameter(Mandatory=$true)][string]$ApiUrl,
    [Parameter(Mandatory=$true)][string]$Token,
    [Parameter(Mandatory=$true)][string]$SourceImagePath,
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

            if ($value -match '^\d+$') { $value = [int]$value }
            elseif ($value -match '^\d+\.\d+$') { $value = [double]$value }

            $params[$key] = $value
        }
    }
    return $params
}

# 解析参数
$scriptParams = Parse-Params -ParamArgs $RemainingArgs

# 必填检查
$required = @('center_x', 'center_y', 'crop_width', 'crop_height')
foreach ($r in $required) {
    if (-not $scriptParams.ContainsKey($r)) {
        Write-Error "错误：缺少必需参数 $r"
        exit 1
    }
}

# 构建body
$body = @{
    ai_app_type = $AiAppType
    session_id = $SessionId
    source_image_path = $SourceImagePath
    center_x = $scriptParams['center_x']
    center_y = $scriptParams['center_y']
    crop_width = $scriptParams['crop_width']
    crop_height = $scriptParams['crop_height']
}

if ($scriptParams.ContainsKey('zoom_scale')) {
    $body['zoom_scale'] = $scriptParams['zoom_scale']
}

# 序列化
try {
    $jsonBody = $body | ConvertTo-Json -Compress
} catch {
    Write-Error "JSON序列化失败: $_"
    exit 1
}

# 发送请求
$url = "$ApiUrl/api/crop_zoom_screenshot"
$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

try {
    $response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $jsonBody
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
    Write-Output "Crop zoom successful. If details are still unclear, adjust parameters and process the same source image again."
}
else {
    $dateStr = Get-Date -Format "yyyy-MM-dd"
    $dirName = "${AiAppType}__${SessionId}__${dateStr}"

    $timeStr = Get-Date -Format "HHmmss"
    $randChars = -join ((97..122) + (48..57) | Get-Random -Count 4 | ForEach-Object { [char]$_ })
    $filename = "crop_zoom_${timeStr}_${randChars}.png"

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
        Write-Output "Crop zoom successful. If details are still unclear, adjust parameters and process the same source image again."
    }
    catch {
        Write-Error "保存图片失败: $_"
        exit 1
    }
}
