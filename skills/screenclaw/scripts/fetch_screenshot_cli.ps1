# ScreenClaw Screenshot Script
# Usage: powershell -ExecutionPolicy Bypass -File fetch_screenshot_cli.ps1 <api_url> <token> <window_id> [session_id]

$ApiUrl = $args[0]
$Token = $args[1]
$WindowId = $args[2]
$SessionId = if ($args.Length -gt 2) { $args[3] } else { "default" }

if (-not $ApiUrl -or -not $Token -or -not $WindowId) {
    Write-Error "Usage: fetch_screenshot_cli.ps1 <api_url> <token> <window_id> [session_id]"
    exit 1
}

$screenshotUrl = "$ApiUrl/api/screenshot"

$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

$body = @{
    ai_app_type = "claude_code"
    session_id = $SessionId
    window_id = [int]$WindowId
    coordinate_type = "grid"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri $screenshotUrl -Method Post -Headers $headers -Body $body
}
catch {
    Write-Error "API call failed: $_"
    exit 1
}

if (-not $response.success) {
    Write-Error "API error: $($response.message)"
    exit 1
}

$isLocal = $ApiUrl -match "localhost|127\.0\.0\.1"

if ($isLocal) {
    Write-Output $response.data.image_path
}
else {
    $pathParts = $response.data.image_path -split '[\\/]'
    $dirName = $pathParts[-2]
    $filename = $pathParts[-1]

    $dataDir = "$env:APPDATA\screenclaw\data"
    $outputDir = Join-Path $dataDir $dirName
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

    $outputPath = Join-Path $outputDir $filename
    $bytes = [Convert]::FromBase64String($response.data.image_base64)
    [System.IO.File]::WriteAllBytes($outputPath, $bytes)

    Write-Output $outputPath
}
