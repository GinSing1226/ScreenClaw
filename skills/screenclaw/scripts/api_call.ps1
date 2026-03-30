param(
    [Parameter(Mandatory=$true)][string]$ApiUrl,
    [Parameter(Mandatory=$true)][string]$Token,
    [Parameter(Mandatory=$true)][string]$Endpoint,
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

# 强制检查：ai_app_type 和 session_id 必须由客户端显式传入
if (-not $scriptParams.ContainsKey('ai_app_type')) {
    Write-Error "错误：ai_app_type 参数必须显式传入。例如：ai_app_type=claude_code"
    exit 1
}
if (-not $scriptParams.ContainsKey('session_id')) {
    Write-Error "错误：session_id 参数必须显式传入。格式：app_name_YYYYMMDD_HHMMSS"
    exit 1
}

$body = @{
    ai_app_type = $scriptParams['ai_app_type']
}
foreach ($kv in $scriptParams.GetEnumerator()) {
    if ($kv.Key -ne 'ai_app_type') {
        $body[$kv.Key] = $kv.Value
    }
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
