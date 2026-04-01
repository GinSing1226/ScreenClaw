# ScreenClaw Batch 结果处理脚本 (PowerShell)
#
# 用于处理 batch API 的响应，特别是处理包含截图指令的结果。

function Get-BatchResultsOutput {
    <#
    .SYNOPSIS
        处理 batch API 响应中的截图数据

    .DESCRIPTION
        从 batch 响应的 results 数组中提取截图数据并处理。
        自动判断本地/局域网场景。

    .PARAMETER Results
        batch API 返回的 results 数组

    .PARAMETER ApiUrl
        API URL（用于判断本地/局域网场景）

    .EXAMPLE
        $results = $response.data.results
        Get-BatchResultsOutput -Results $results -ApiUrl "http://localhost:12261/api/batch"
    #>
    param(
        [Parameter(Mandatory = $true)]
        [array]$Results,

        [Parameter(Mandatory = $true)]
        [string]$ApiUrl
    )

    $output = @()

    # 判断调用场景
    $isLocal = $ApiUrl -match "localhost|127\.0\.0\.1"

    foreach ($item in $Results) {
        if ($item.data -and $item.data.image_base64) {
            # 截图指令
            if ($isLocal) {
                # 本地场景：直接使用 image_path
                $imagePath = $item.data.image_path
                $output += "![screenshot](file:///$imagePath)"
            }
            else {
                # 局域网场景：解码并保存
                # 从 image_path 中提取目录名和文件名
                # 原路径格式：D:/screenClaw/data/{dir_name}/{filename}
                $pathParts = $item.data.image_path -split [IO.Path]::DirectorySeparatorChar
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
                $bytes = [Convert]::FromBase64String($item.data.image_base64)
                $outputPath = Join-Path $outputDir $filename
                [System.IO.File]::WriteAllBytes($outputPath, $bytes)

                $output += "![screenshot]($outputPath)"
            }
        }
        else {
            # 非截图指令
            $output += $item.message
        }
    }

    return $output
}


function Invoke-BatchAndProcess {
    <#
    .SYNOPSIS
        调用 batch API 并自动处理结果

    .DESCRIPTION
        一站式调用 batch API 并处理包含截图的结果

    .PARAMETER ApiUrl
        batch API 完整路径

    .PARAMETER Token
        认证 token

    .PARAMETER Instructions
        指令数组

    .PARAMETER AiAppType
        AI 应用类型

    .PARAMETER SessionId
        会话唯一标识

    .EXAMPLE
        $instructions = @(
            @{ action = "click"; params = @{ x = 50; y = 30 } },
            @{ action = "screenshot"; params = @{ coordinate_type = "grid" } }
        )
        Invoke-BatchAndProcess -ApiUrl "http://localhost:12261/api/batch" -Token "xxx" -Instructions $instructions
    #>
    param(
        [Parameter(Mandatory = $true)]
        [string]$ApiUrl,

        [Parameter(Mandatory = $true)]
        [string]$Token,

        [Parameter(Mandatory = $true)]
        [array]$Instructions,

        [Parameter(Mandatory = $true)]
        [string]$AiAppType,

        [Parameter(Mandatory = $true)]
        [string]$SessionId,

        [Parameter(Mandatory = $true)]
        [int]$WindowId,

        [Parameter(Mandatory = $true)]
        [int]$MainWindowId
    )

    $headers = @{
        "Authorization" = "Bearer $Token"
        "Content-Type"  = "application/json"
    }

    $body = @{
        ai_app_type    = $AiAppType
        session_id     = $SessionId
        window_id      = $WindowId
        main_window_id = $MainWindowId
        instructions   = $Instructions
    } | ConvertTo-Depth -Depth 10 | ConvertTo-Json

    try {
        # 调用 API
        $response = Invoke-RestMethod -Uri $ApiUrl -Method Post -Headers $headers -Body $body

        if ($response.success) {
            # 处理结果
            $output = Get-BatchResultsOutput -Results $response.data.results -ApiUrl $ApiUrl
            return $output -join "`n"
        }
        else {
            Write-Error "Batch failed: $($response.message)"
            return $null
        }
    }
    catch {
        Write-Error "Request failed: $_"
        return $null
    }
}

# 辅助函数：深度转换 Hashtable 为 PSObject
function ConvertTo-Depth {
    param($InputObject, $Depth = 10)

    if ($Depth -le 0) { return $InputObject }

    if ($InputObject -is [System.Collections.IDictionary]) {
        $result = @{}
        foreach ($kv in $InputObject.GetEnumerator()) {
            $result[$kv.Key] = ConvertTo-Depth -InputObject $kv.Value -Depth ($Depth - 1)
        }
        return [PSCustomObject]$result
    }
    elseif ($InputObject -is [array]) {
        $result = @($InputObject | ForEach-Object { ConvertTo-Depth -InputObject $_ -Depth ($Depth - 1) })
        return $result
    }
    else {
        return $InputObject
    }
}


# CLI 使用示例
if ($MyInvocation.InvocationName -ne '.') {
    # 示例：从文件读取 batch 结果并处理
    if ($args.Count -ge 1) {
        $resultFile = $args[0]
        $result = Get-Content $resultFile | ConvertFrom-Json

        $output = Get-BatchResultsOutput -Results $result.data.results -ApiUrl $result.api_url
        Write-Output $output
    }
    else {
        Write-Host "Usage: .\batch_results_processor.ps1 <result_json_file>"
    }
}
