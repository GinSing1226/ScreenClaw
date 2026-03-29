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
    # 获取图片路径并提取目录名和文件名
    $imagePath = $response.data.image_path
    $pathParts = $imagePath -split '[\\/]' | Where-Object { $_ -ne '' }

    if ($pathParts.Count -ge 2) {
        $dirName = $pathParts[-2]
        $filename = $pathParts[-1]
    } else {
        $dirName = $SessionId
        $filename = "screenshot.png"
    }

    # 确保data目录存在
    $dataDir = "$env:APPDATA\screenclaw\data"
    if (-not (Test-Path $dataDir)) {
        New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
    }

    $outputDir = Join-Path $dataDir $dirName

    # 创建目录
    try {
        if (-not (Test-Path $outputDir)) {
            New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
        }
    }
    catch {
        # 回退：使用时间戳作为目录名
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $outputDir = Join-Path $dataDir $timestamp
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    }

    $outputPath = Join-Path $outputDir $filename

    # 保存图片
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
