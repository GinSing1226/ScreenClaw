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

# 构建网格参数函数
function Build-GridParams {
    param([hashtable]$Params)

    $grid = @{}
    $coordinate = @{}
    $marker = @{}

    if ($Params.ContainsKey('grid_density_x')) { $grid['density_x'] = $Params['grid_density_x'] }
    if ($Params.ContainsKey('grid_density_y')) { $grid['density_y'] = $Params['grid_density_y'] }
    if ($Params.ContainsKey('grid_opacity')) { $grid['opacity'] = $Params['grid_opacity'] }
    if ($Params.ContainsKey('grid_color')) { $grid['color'] = $Params['grid_color'] }

    if ($Params.ContainsKey('number_density')) { $coordinate['number_density'] = $Params['number_density'] }
    if ($Params.ContainsKey('number_decimal')) { $coordinate['number_decimal'] = $Params['number_decimal'] }
    if ($Params.ContainsKey('number_size')) { $coordinate['number_size'] = $Params['number_size'] }
    if ($Params.ContainsKey('number_color')) { $coordinate['number_color'] = $Params['number_color'] }
    if ($Params.ContainsKey('number_opacity')) { $coordinate['number_opacity'] = $Params['number_opacity'] }

    if ($Params.ContainsKey('marker_x') -and $Params.ContainsKey('marker_y')) {
        $marker['x'] = $Params['marker_x']
        $marker['y'] = $Params['marker_y']
        if ($Params.ContainsKey('marker_ring_radius')) { $marker['ring_radius'] = $Params['marker_ring_radius'] }
        if ($Params.ContainsKey('marker_ring_line_width')) { $marker['ring_line_width'] = $Params['marker_ring_line_width'] }
        if ($Params.ContainsKey('marker_ring_color')) { $marker['ring_color'] = $Params['marker_ring_color'] }
        if ($Params.ContainsKey('marker_dot_radius')) { $marker['dot_radius'] = $Params['marker_dot_radius'] }
        if ($Params.ContainsKey('marker_dot_color')) { $marker['dot_color'] = $Params['marker_dot_color'] }
    }

    # 多标记点：收集 marker_N_x/marker_N_y 索引
    $markerIndices = @{}
    foreach ($key in @($Params.Keys)) {
        if ($key -match '^marker_(\d+)_x$') {
            $markerIndices[$Matches[1]] = $true
        }
    }
    # 向后兼容：marker_x/marker_y → 索引 1
    if ($Params.ContainsKey('marker_x') -and $Params.ContainsKey('marker_y') -and -not $markerIndices.ContainsKey('1')) {
        $markerIndices['1'] = $true
    }

    $markerArray = @()
    foreach ($idx in ($markerIndices.Keys | Sort-Object { [int]$_ })) {
        $m = @{}
        foreach ($f in @('x','y','ring_radius','ring_line_width','ring_color','dot_radius','dot_color')) {
            $idxKey = "marker_${idx}_${f}"
            if ($Params.ContainsKey($idxKey)) { $m[$f] = $Params[$idxKey] }
        }
        # 向后兼容：marker_x → marker_1_x
        if ($idx -eq '1' -and -not $m.ContainsKey('x')) {
            foreach ($f in @('x','y','ring_radius','ring_line_width','ring_color','dot_radius','dot_color')) {
                $legacyKey = "marker_$f"
                if ($Params.ContainsKey($legacyKey)) { $m[$f] = $Params[$legacyKey] }
            }
        }
        if ($m.ContainsKey('x') -and $m.ContainsKey('y')) {
            $markerArray += ,$m
        }
    }

    $result = @{}
    if ($grid.Count -gt 0) { $result['grid'] = $grid }
    if ($coordinate.Count -gt 0) { $result['coordinate'] = $coordinate }
    if ($marker.Count -gt 0) { $result['marker'] = $marker }
    if ($markerArray.Count -gt 0) { $result['marker'] = $markerArray }
    return $result
}

# 解析参数
$scriptParams = Parse-Params -ParamArgs $RemainingArgs

$gridParams = Build-GridParams -Params $scriptParams

$screenshotUrl = "$ApiUrl/api/screenshot"

$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

# 解析 coordinate_type 参数（默认 grid）
$coordinateType = "grid"
if ($scriptParams.ContainsKey('coordinate_type')) {
    $coordinateType = $scriptParams['coordinate_type']
    $scriptParams.Remove('coordinate_type')
}

# 解析 color_mode 参数（默认 grayscale）
$colorMode = "grayscale"
if ($scriptParams.ContainsKey('color_mode')) {
    $colorMode = $scriptParams['color_mode']
    $scriptParams.Remove('color_mode')
}

# 构建基础body
$body = @{
    ai_app_type = $AiAppType
    session_id = $SessionId
    window_id = $WindowId
    main_window_id = $MainWindowId
    coordinate_type = $coordinateType
    color_mode = $colorMode
}

# 合并网格参数
foreach ($kv in $gridParams.GetEnumerator()) {
    $body[$kv.Key] = $kv.Value
}

# 使用 PowerShell 5.1+ 的 ConvertTo-Json
try {
    $jsonBody = $body | ConvertTo-Json -Compress
} catch {
    # 降级：手动构建 JSON
    $jsonBody = "{"
    $parts = @()
    foreach ($kv in $body.GetEnumerator()) {
        $key = $kv.Key
        $value = $kv.Value

        if ($value -is [string]) {
            $parts += "`"$key`":`"$value`""
        } elseif ($value -is [bool]) {
            $parts += "`"$key`":$($value.ToString().ToLower())"
        } elseif ($value -is [int] -or $value -is [double]) {
            $parts += "`"$key`":$value"
        } elseif ($value -is [hashtable]) {
            $innerParts = @()
            foreach ($innerKv in $value.GetEnumerator()) {
                $innerKey = $innerKv.Key
                $innerValue = $innerKv.Value
                if ($innerValue -is [string]) {
                    $innerParts += "`"$innerKey`":`"$innerValue`""
                } else {
                    $innerParts += "`"$innerKey`":$innerValue"
                }
            }
            $parts += "`"$key`":{$($innerParts -join ',')}"
        }
    }
    $jsonBody = "{$($parts -join ',')}"
}

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
    if ($gridParams.ContainsKey('marker')) {
        Write-Output "Screenshot successful. Marker indicates the position of your input coordinates on the image. If result is unsatisfactory, refer to skill.md for parameter tuning."
    } else {
        Write-Output "Screenshot successful. If result is unsatisfactory, refer to skill.md for parameter tuning."
    }
}
else {
    # 远程场景：服务端只返回base64，客户端自己生成符合规则的路径
    # 目录规则：{ai_app_type}__{session_id}__{yyyy-MM-dd}
    # 文件规则：screenshot_{HHMMSS}_{rand4}.png
    $dateStr = Get-Date -Format "yyyy-MM-dd"
    $dirName = "${AiAppType}__${SessionId}__${dateStr}"

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
        if ($gridParams.ContainsKey('marker')) {
            Write-Output "Screenshot successful. Marker indicates the position of your input coordinates on the image. If result is unsatisfactory, refer to skill.md for parameter tuning."
        } else {
            Write-Output "Screenshot successful. If result is unsatisfactory, refer to skill.md for parameter tuning."
        }
    }
    catch {
        Write-Error "保存图片失败: $_"
        exit 1
    }
}
