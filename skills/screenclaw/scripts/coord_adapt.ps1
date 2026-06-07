param(
    [Parameter(Position=0, ValueFromRemainingArguments=$true)][string[]]$RemainingArgs
)

function Parse-Value($Value) {
    if ($Value -match '^-?\d+(\.\d+)?$') { return [double]$Value }
    return $Value
}

function Set-NestedValue([hashtable]$Obj, [string[]]$Parts, $Value) {
    if ($Parts.Count -eq 1) {
        $Obj[$Parts[0]] = $Value
        return
    }
    $key = $Parts[0]
    if (-not $Obj.ContainsKey($key)) { $Obj[$key] = @{} }
    Set-NestedValue $Obj[$key] @($Parts[1..($Parts.Count - 1)]) $Value
}

function Parse-Args([string[]]$RawArgs) {
    $result = @{}
    foreach ($arg in $RawArgs) {
        if ($arg -notmatch '^(.+?)=(.*)$') {
            throw "invalid argument '$arg', expected key=value"
        }
        Set-NestedValue $result ($Matches[1] -split '\.') (Parse-Value $Matches[2])
    }
    return $result
}

function Require-Number([hashtable]$Root, [string]$Path) {
    $value = $Root
    foreach ($part in ($Path -split '\.')) {
        if ($value -isnot [hashtable] -or -not $value.ContainsKey($part)) {
            throw "$Path is required"
        }
        $value = $value[$part]
    }
    if ($value -isnot [double] -and $value -isnot [int]) {
        throw "$Path must be a number"
    }
    return [double]$value
}

try {
    $params = Parse-Args $RemainingArgs
    $sourceWidth = Require-Number $params "source.width"
    $sourceHeight = Require-Number $params "source.height"
    $sourceScale = Require-Number $params "source.scale_factor"
    $currentWidth = Require-Number $params "current.width"
    $currentHeight = Require-Number $params "current.height"
    $currentScale = Require-Number $params "current.scale_factor"
    $pointX = Require-Number $params "point.x"
    $pointY = Require-Number $params "point.y"
    $risk = if ($params.ContainsKey("risk")) { [string]$params["risk"] } else { "normal" }
    $risk = $risk.ToLowerInvariant()

    $thresholds = @{
        large = @{ direct = 6.0; verify = 20.0 }
        normal = @{ direct = 3.0; verify = 15.0 }
        small = @{ direct = 2.0; verify = 8.0 }
        danger = @{ direct = 0.0; verify = 6.0 }
    }
    if (-not $thresholds.ContainsKey($risk)) {
        throw "risk must be one of: danger, large, normal, small"
    }
    if (($sourceWidth, $sourceHeight, $sourceScale, $currentWidth, $currentHeight, $currentScale | Measure-Object -Minimum).Minimum -le 0) {
        throw "width, height, and scale_factor must be greater than 0"
    }

    $sourceXPx = $sourceWidth * $pointX / 100.0
    $sourceYPx = $sourceHeight * $pointY / 100.0
    $logicalX = $sourceXPx / $sourceScale
    $logicalY = $sourceYPx / $sourceScale
    $candidateXPx = $logicalX * $currentScale
    $candidateYPx = $logicalY * $currentScale
    $candidateX = $candidateXPx / $currentWidth * 100.0
    $candidateY = $candidateYPx / $currentHeight * 100.0

    $shiftXPx = ($candidateX - $pointX) / 100.0 * $currentWidth
    $shiftYPx = ($candidateY - $pointY) / 100.0 * $currentHeight
    $distancePx = [Math]::Sqrt($shiftXPx * $shiftXPx + $shiftYPx * $shiftYPx)
    $maxAxisShift = [Math]::Max([Math]::Abs($shiftXPx), [Math]::Abs($shiftYPx))
    $riskThreshold = $thresholds[$risk]

    if ($candidateX -lt 0 -or $candidateX -gt 100 -or $candidateY -lt 0 -or $candidateY -gt 100) {
        $decision = "relocate"
        $reason = "candidate is outside 0-100 percent bounds"
    } elseif ($maxAxisShift -le $riskThreshold.direct) {
        $decision = "direct"
        $reason = "axis shift is within direct threshold"
    } elseif ($maxAxisShift -le $riskThreshold.verify) {
        $decision = "verify"
        $reason = "axis shift requires marker verification"
    } else {
        $decision = "relocate"
        $reason = "axis shift exceeds verification threshold"
    }

    [ordered]@{
        decision = $decision
        risk = $risk
        candidate = [ordered]@{ x = [Math]::Round($candidateX, 4); y = [Math]::Round($candidateY, 4) }
        template = [ordered]@{ x = $pointX; y = $pointY }
        shift_px = [ordered]@{
            x = [Math]::Round($shiftXPx, 4)
            y = [Math]::Round($shiftYPx, 4)
            distance = [Math]::Round($distancePx, 4)
            max_axis = [Math]::Round($maxAxisShift, 4)
        }
        thresholds_px = $riskThreshold
        source = [ordered]@{ width = $sourceWidth; height = $sourceHeight; scale_factor = $sourceScale }
        current = [ordered]@{ width = $currentWidth; height = $currentHeight; scale_factor = $currentScale }
        reason = $reason
    } | ConvertTo-Json -Depth 10
} catch {
    Write-Error "Script Error: $($_.Exception.Message)"
    exit 1
}
