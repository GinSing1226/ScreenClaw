# ScreenClaw 截图获取脚本 (PowerShell)
#
# 用于从 ScreenClaw API 获取截图，并根据调用场景（本地/局域网）选择合适的处理方式。

function Get-Screenshot {
    <#
    .SYNOPSIS
        调用 ScreenClaw 截图 API

    .DESCRIPTION
        根据调用场景（本地/局域网）自动选择合适的处理方式：
        - 本地调用：直接使用返回的 image_path
        - 局域网调用：解码 image_base64 并保存到本地

    .PARAMETER ApiUrl
        API 完整路径（如 http://localhost:12261/api/screenshot）

    .PARAMETER Token
        认证 token

    .PARAMETER WindowId
        目标窗口句柄

    .PARAMETER AiAppType
        AI 应用类型（默认：claude_code）

    .PARAMETER SessionId
        会话唯一标识

    .PARAMETER CoordinateType
        坐标类型（grid/no，默认：grid）

    .EXAMPLE
        Get-Screenshot -ApiUrl "http://localhost:12261/api/screenshot" -Token "your-token" -WindowId 12345
    #>
    param(
        [Parameter(Mandatory = $true)]
        [string]$ApiUrl,

        [Parameter(Mandatory = $true)]
        [string]$Token,

        [Parameter(Mandatory = $true)]
        [int]$WindowId,

        [string]$AiAppType = "claude_code",

        [string]$SessionId = "",

        [string]$CoordinateType = "grid"
    )

    $headers = @{
        "Authorization" = "Bearer $Token"
        "Content-Type"  = "application/json"
    }

    $body = @{
        ai_app_type    = $AiAppType
        session_id     = $SessionId
        window_id      = $WindowId
        coordinate_type = $CoordinateType
    } | ConvertTo-Json

    try {
        # 调用 API
        $response = Invoke-RestMethod -Uri $ApiUrl -Method Post -Headers $headers -Body $body

        if ($response.success -and $response.data.image_base64) {
            # 判断调用场景
            if ($ApiUrl -match "localhost|127\.0\.0\.1") {
                # 本地场景：直接使用 image_path
                Write-Output $response.data.image_path
            }
            else {
                # 局域网场景：解码并保存
                # 从 image_path 中提取目录名和文件名
                # 原路径格式：D:/screenClaw/data/{dir_name}/{filename}
                $pathParts = $response.data.image_path -split [IO.Path]::DirectorySeparatorChar
                $dirName = $pathParts[-2]  # 倒数第二部分是目录名
                $filename = $pathParts[-1]  # 最后部分是文件名

                $dataDir = if ($IsWindows -or $env:OS) {
                    "$env:APPDATA\screenclaw\data"
                }
                else {
                    "$env:HOME/.local/share/screenclaw/data"
                }

                $outputDir = Join-Path $dataDir $dirName
                New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

                # 保存图片
                $bytes = [Convert]::FromBase64String($response.data.image_base64)
                $outputPath = Join-Path $outputDir $filename
                [System.IO.File]::WriteAllBytes($outputPath, $bytes)

                Write-Output $outputPath
            }
        }
        else {
            Write-Error "API error: $($response.message)"
        }
    }
    catch {
        Write-Error "Request failed: $_"
    }
}


# 批处理支持
function Get-BatchScreenshots {
    <#
    .SYNOPSIS
        处理包含截图指令的 batch 响应

    .DESCRIPTION
        从 batch 响应中提取截图数据并保存

    .PARAMETER Results
        batch API 返回的 results 数组
    #>
    param(
        [Parameter(Mandatory = $true)]
        [array]$Results
    )

    $output = @()

    foreach ($item in $Results) {
        if ($item.data -and $item.data.image_base64) {
            # 截图指令 - 局域网场景
            # 从 image_path 中提取目录名和文件名
            $pathParts = $item.data.image_path -split [IO.Path]::DirectorySeparatorChar
            $dirName = $pathParts[-2]
            $filename = $pathParts[-1]

            $dataDir = if ($IsWindows -or $env:OS) {
                "$env:APPDATA\screenclaw\data"
            }
            else {
                "$env:HOME/.local/share/screenclaw/data"
            }

            $outputDir = Join-Path $dataDir $dirName
            New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

            # 保存图片
            $bytes = [Convert]::FromBase64String($item.data.image_base64)
            $outputPath = Join-Path $outputDir $filename
            [System.IO.File]::WriteAllBytes($outputPath, $bytes)

            $output += $outputPath
        }
        else {
            $output += $item.message
        }
    }

    return $output
}


# CLI 使用示例
if ($MyInvocation.InvocationName -ne '.') {
    # 示例：.\fetch_screenshot.ps1 -ApiUrl "http://localhost:12261/api/screenshot" -Token "your-token" -WindowId 12345
}
