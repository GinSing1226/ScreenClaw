param(
    [Parameter(Mandatory=$true)][string]$ApiUrl,
    [Parameter(Mandatory=$true)][string]$Token,
    [Parameter(Mandatory=$true)][int]$WindowId,
    [Parameter()][string]$SessionId = "default",
    [Parameter()][string]$AiAppType = "claude_code"
)

$screenshotUrl = "$ApiUrl/api/screenshot"

$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

$body = @{
    ai_app_type = $AiAppType
    session_id = $SessionId
    window_id = $WindowId
    coordinate_type = "grid"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri $screenshotUrl -Method Post -Headers $headers -Body $body
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
