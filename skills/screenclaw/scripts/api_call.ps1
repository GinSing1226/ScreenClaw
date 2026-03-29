param(
    [Parameter(Mandatory=$true)][string]$ApiUrl,
    [Parameter(Mandatory=$true)][string]$Token,
    [Parameter(Mandatory=$true)][string]$Endpoint,
    [Parameter()][string]$AiAppType = "claude_code",
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$RemainingArgs
)

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
    } elseif ($Value -is [int]) {
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

            $params[$key] = $value
        }
    }
    return $params
}

$scriptParams = Parse-Params -ParamArgs $RemainingArgs

if (-not $scriptParams.ContainsKey('session_id')) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $scriptParams['session_id'] = "screenclaw_$timestamp"
}

$body = @{
    ai_app_type = $AiAppType
}
foreach ($kv in $scriptParams.GetEnumerator()) {
    $body[$kv.Key] = $kv.Value
}

$jsonBody = ConvertTo-JsonString -Value $body

$url = "$ApiUrl/api/$Endpoint".TrimEnd('/')
$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

try {
    $response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $jsonBody
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Error "API调用失败: $_"
    exit 1
}
