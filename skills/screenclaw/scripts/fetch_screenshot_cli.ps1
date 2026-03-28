# ScreenClaw 截图获取脚本（独立CLI版本）
#
# 用法一（推荐）：直接调用API
#   .\fetch_screenshot_cli.ps1 "http://192.168.10.190:12261" "TOKEN123" 1380176
#   .\fetch_screenshot_cli.ps1 "http://192.168.10.190:12261" "TOKEN123" 1380176 "my-session"
#
# 用法二（备用）：处理已保存的JSON响应（会自动删除该JSON文件）
#   .\fetch_screenshot_cli.ps1 "C:\Users\xxx\AppData\Local\Temp\screenshot_response.json" "http://192.168.10.190:12261"

param(
    [Parameter(Mandatory = $true)]
    [string]$Param1,

    [Parameter(Mandatory = $false)]
    [string]$Param2,

    [Parameter(Mandatory = $false)]
    [int]$Param3,

    [Parameter(Mandatory = $false)]
    [string]$Param4 = "default"
)

# 用法二：处理已保存的JSON文件
if ($Param1.EndsWith('.json') -and $Param2) {
    $jsonPath = $Param1
    $apiUrl = $Param2

    try {
        $result = Get-Content $jsonPath -Raw | ConvertFrom-Json
    }
    catch {
        Write-Error "读取JSON文件失败: $_"
        exit 1
    }

    $imagePath = $result.data.image_path
    $imageBase64 = $result.data.image_base64

    # 判断本地还是局域网
    $isLocal = $apiUrl -match "localhost|127\.0\.0\.1"

    if ($isLocal) {
        # 本地场景：直接返回路径
        Write-Output $imagePath
    }
    else {
        # 局域网场景：保存到本地
        $pathParts = $imagePath -split [IO.Path]::DirectorySeparatorChar
        $dirName = $pathParts[-2]
        $filename = $pathParts[-1]

        # 确定保存目录
        $dataDir = if ($IsWindows -or $env:OS) {
            "$env:APPDATA\screenclaw\data"
        }
        else {
            "$env:HOME/.local/share/screenclaw/data"
        }

        $outputDir = Join-Path $dataDir $dirName
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

        # 保存图片
        $outputPath = Join-Path $outputDir $filename
        $bytes = [Convert]::FromBase64String($imageBase64)
        [System.IO.File]::WriteAllBytes($outputPath, $bytes)

        Write-Output $outputPath
    }

    # 自动删除临时JSON文件
    try {
        Remove-Item $jsonPath -Force -ErrorAction SilentlyContinue
    }
    catch {
        # 删除失败不影响主流程
    }

    exit 0
}

# 用法一：直接调用API
$ApiUrl = $Param1
$Token = $Param2
$WindowId = $Param3
$SessionId = $Param4

$screenshotUrl = "$ApiUrl/api/screenshot"

$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

$body = @{
    ai_app_type = "claude_code"
    session_id = $SessionId
    window_id = $WindowId
    coordinate_type = "grid"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri $screenshotUrl -Method Post -Headers $headers -Body $body
}
catch {
    Write-Error "API 调用失败: $_"
    exit 1
}

if (-not $response.success) {
    Write-Error "API 错误: $($response.message)"
    exit 1
}

# 判断本地还是局域网
$isLocal = $ApiUrl -match "localhost|127\.0\.0\.1"

if ($isLocal) {
    # 本地场景：直接返回路径
    Write-Output $response.data.image_path
}
else {
    # 局域网场景：保存到本地
    $pathParts = $response.data.image_path -split [IO.Path]::DirectorySeparatorChar
    $dirName = $pathParts[-2]
    $filename = $pathParts[-1]

    # 确定保存目录
    $dataDir = if ($IsWindows -or $env:OS) {
        "$env:APPDATA\screenclaw\data"
    }
    else {
        "$env:HOME/.local/share/screenclaw/data"
    }

    $outputDir = Join-Path $dataDir $dirName
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

    # 保存图片
    $outputPath = Join-Path $outputDir $filename
    $bytes = [Convert]::FromBase64String($response.data.image_base64)
    [System.IO.File]::WriteAllBytes($outputPath, $bytes)

    Write-Output $outputPath
}
