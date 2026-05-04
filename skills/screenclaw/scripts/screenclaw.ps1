param(
    [Parameter(Mandatory=$true, Position=0)][string]$Endpoint,
    [Parameter(Position=1, ValueFromRemainingArguments=$true)][string[]]$RemainingArgs
)

function Parse-Value($Key, $Value) {
    if ($Value -eq 'true') { return $true }
    if ($Value -eq 'false') { return $false }
    if ($Key -notin @('text','key','keyword','action','newline_key','api_url','token','ai_app_type','session_id','source_image_path','self_check')) {
        if ($Value -match '^-?\d+$') { return [int]$Value }
        if ($Value -match '^-?\d+\.\d+$') { return [double]$Value }
    }
    return $Value
}

function Set-NestedValue([object]$Obj, [string[]]$Parts, $Value) {
    if ($Parts.Count -eq 1) {
        if ($Obj -is [System.Collections.ArrayList]) {
            $idx = [int]$Parts[0]
            while ($Obj.Count -le $idx) { [void]$Obj.Add($null) }
            $Obj[$idx] = $Value
        } else {
            $Obj[$Parts[0]] = $Value
        }
        return
    }
    $key = $Parts[0]
    $rest = @($Parts[1..($Parts.Count - 1)])
    $nextIsIndex = $Parts[1] -match '^\d+$'
    if ($Obj -is [System.Collections.ArrayList]) {
        $idx = [int]$key
        while ($Obj.Count -le $idx) { [void]$Obj.Add($null) }
        if ($null -eq $Obj[$idx]) {
            if ($nextIsIndex) {
                $Obj[$idx] = [System.Collections.ArrayList]::new()
            } else {
                $Obj[$idx] = [hashtable]::new()
            }
        }
        Set-NestedValue -Obj ([object]$Obj[$idx]) -Parts $rest -Value $Value
    } else {
        if (-not $Obj.ContainsKey($key)) {
            if ($nextIsIndex) {
                $Obj[$key] = [System.Collections.ArrayList]::new()
            } else {
                $Obj[$key] = [hashtable]::new()
            }
        }
        Set-NestedValue -Obj ([object]$Obj[$key]) -Parts $rest -Value $Value
    }
}

function Set-Nested([ref]$Obj, [string[]]$Parts, $Value) {
    Set-NestedValue -Obj ([object]$Obj.Value) -Parts $Parts -Value $Value
}

function Parse-Args([string[]]$RawArgs) {
    $flat = @{}
    foreach ($arg in $RawArgs) {
        if ($arg -notmatch '^(.+?)=(.*)$') {
            throw "invalid argument '$arg', expected key=value"
        }
        $key = $Matches[1]
        $value = $Matches[2]
        $flat[$key] = Parse-Value $key $value
    }
    $result = @{}
    foreach ($kv in $flat.GetEnumerator()) {
        $parts = $kv.Key -split '\.'
        Set-Nested -Obj ([ref]$result) -Parts $parts -Value $kv.Value
    }
    return $result
}

function Convert-BatchSteps([hashtable]$Body) {
    if (-not $Body.ContainsKey('step')) { return $Body }
    $steps = $Body['step']
    $instructions = @()
    foreach ($step in $steps) {
        if ($null -eq $step) { continue }
        if (-not $step.ContainsKey('action')) { throw "each batch step requires action" }
        $params = if ($step.ContainsKey('params')) { $step['params'] } else { @{} }
        $instructions += @{ action = $step['action']; params = $params }
    }
    $Body.Remove('step')
    $Body['instructions'] = $instructions
    return $Body
}

function Save-RemoteImage($Base64, $AiAppType, $SessionId, $Prefix) {
    $dateStr = Get-Date -Format "yyyy-MM-dd"
    $timeStr = Get-Date -Format "HHmmss"
    $rand = -join ((97..122) + (48..57) | Get-Random -Count 4 | ForEach-Object { [char]$_ })
    if ($env:SCREENCLAW_DATA_DIR) {
        $baseDir = $env:SCREENCLAW_DATA_DIR
    } else {
        $root = if ($env:SCREENCLAW_ROOT) { $env:SCREENCLAW_ROOT } else { (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path }
        $baseDir = Join-Path $root "data"
    }
    $sessionPrefix = "${AiAppType}__${SessionId}__"
    $existingDirs = @()
    if (Test-Path $baseDir) {
        $existingDirs = Get-ChildItem -Path $baseDir -Directory -Filter "$sessionPrefix*" | Sort-Object Name
    }
    if ($existingDirs.Count -gt 0) {
        $outDir = $existingDirs[0].FullName
    } else {
        $outDir = Join-Path $baseDir "${sessionPrefix}${dateStr}"
    }
    if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
    $outPath = Join-Path $outDir "${Prefix}_${timeStr}_${rand}.png"
    [System.IO.File]::WriteAllBytes($outPath, [Convert]::FromBase64String($Base64))
    return $outPath
}

function Is-LocalUrl($ApiUrl) {
    $lowered = $ApiUrl.ToLowerInvariant()
    return $lowered.Contains('localhost') -or $lowered.Contains('127.0.0.1') -or $lowered.Contains('::1')
}

function Image-Prefix($EndpointName) {
    if ($EndpointName -eq 'crop_zoom_screenshot') { return 'crop_zoom' }
    if ($EndpointName -eq 'scroll_screenshot') { return 'scroll_screenshot' }
    return 'screenshot'
}

function Convert-LocalCropToBase64([hashtable]$Params) {
    if ($Params.ContainsKey('source_image_path') -and -not $Params.ContainsKey('source_image_base64')) {
        $sourcePath = $Params['source_image_path']
        if (-not (Test-Path $sourcePath)) { throw "source_image_path not found: $sourcePath" }
        $Params['source_image_base64'] = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($sourcePath))
        $Params.Remove('source_image_path')
    }
}

function Prepare-RemoteCropInput($EndpointName, $ApiUrl, [hashtable]$Body) {
    if (Is-LocalUrl $ApiUrl) { return }
    if ($EndpointName -eq 'crop_zoom_screenshot') {
        Convert-LocalCropToBase64 $Body
    }
    if ($EndpointName -eq 'batch' -and $Body.ContainsKey('instructions')) {
        foreach ($instruction in $Body['instructions']) {
            if ($instruction['action'] -eq 'crop_zoom_screenshot') {
                Convert-LocalCropToBase64 $instruction['params']
            }
        }
    }
}

function Materialize-ImageData($EndpointName, $Data, [hashtable]$Body) {
    $path = $Data.image_path
    if (-not $path -and $Data.image_base64) {
        $prefix = Image-Prefix $EndpointName
        $path = Save-RemoteImage $Data.image_base64 $Body['ai_app_type'] $Body['session_id'] $prefix
        $Data | Add-Member -NotePropertyName image_path -NotePropertyValue $path -Force
        $Data.PSObject.Properties.Remove('image_base64')
    }
    return $path
}

function Valid-Endpoints {
    return @(
        'batch','click','crop_zoom_screenshot','delegated','drag','get_window_list','health',
        'hover','input_text','long_press','mouse_move','press_key','right_click','screenshot',
        'scroll','scroll_screenshot','swipe','wait'
    )
}

function Endpoint-Doc($EndpointName) {
    return "references/api/$EndpointName.md"
}

function Validate-Endpoint($EndpointName) {
    if ($EndpointName -notin (Valid-Endpoints)) {
        throw "unknown endpoint '$EndpointName'. Next: read skill.md and use a valid endpoint. Valid endpoints: $((Valid-Endpoints) -join ', ')"
    }
}

function Endpoint-AllowedKeys($EndpointName) {
    $common = @('ai_app_type','session_id','window_id','main_window_id')
    switch ($EndpointName) {
        'health' { return $common }
        'get_window_list' { return $common + @('keyword','include_children','children_filter') }
        'delegated' { return $common + @('action') }
        'screenshot' { return $common + @('coordinate_type','color_mode','grid','coordinate','marker','self_check') }
        'crop_zoom_screenshot' { return $common + @('source_image_path','source_image_base64','center_x','center_y','crop_width','crop_height','zoom_scale') }
        'scroll_screenshot' { return $common + @('action_method','max_scrolls','scroll_percent','scroll_wait','x','y','max_adjust_retries','target_overlap_min','target_overlap_max','stop_threshold') }
        'click' { return $common + @('x','y','action_method') }
        'right_click' { return $common + @('x','y','action_method') }
        'long_press' { return $common + @('x','y','action_method','duration_ms') }
        'hover' { return $common + @('x','y','action_method','duration_ms') }
        'swipe' { return $common + @('start_x','start_y','end_x','end_y','action_method') }
        'drag' { return $common + @('start_x','start_y','end_x','end_y','duration_ms','action_method','target_window_id','target_main_window_id') }
        'scroll' { return $common + @('x','y','delta','action_method') }
        'mouse_move' { return $common + @('delta_x','delta_y','duration_ms','action_method') }
        'input_text' { return $common + @('x','y','text','newline_key','action_method') }
        'press_key' { return $common + @('key','x','y','duration_ms','action_method') }
        'wait' { return $common + @('duration_ms','random_range') }
        'batch' { return $common + @('step','instructions') }
    }
}

function Validate-NestedKeys($EndpointName, $Value, [string[]]$Allowed, $Path) {
    if ($Value -is [System.Collections.ArrayList] -or $Value -is [object[]]) {
        $idx = 0
        foreach ($item in $Value) {
            Validate-NestedKeys $EndpointName $item $Allowed "$Path.$idx"
            $idx += 1
        }
        return
    }
    if ($Value -isnot [hashtable]) { return }
    foreach ($key in $Value.Keys) {
        if ($key -notin $Allowed) {
            throw "unknown parameter '$Path.$key' for endpoint '$EndpointName'. Next: read skill.md and $(Endpoint-Doc $EndpointName)."
        }
    }
}

function Validate-Params($EndpointName, [hashtable]$Body) {
    Validate-Endpoint $EndpointName
    $allowed = Endpoint-AllowedKeys $EndpointName
    foreach ($key in $Body.Keys) {
        if ($key -notin $allowed) {
            throw "unknown parameter '$EndpointName.$key' for endpoint '$EndpointName'. Next: read skill.md and $(Endpoint-Doc $EndpointName)."
        }
    }
    if ($EndpointName -eq 'screenshot') {
        if ($Body.ContainsKey('grid')) { Validate-NestedKeys $EndpointName $Body['grid'] @('density_x','density_y','opacity','color') 'screenshot.grid' }
        if ($Body.ContainsKey('coordinate')) {
            Validate-NestedKeys $EndpointName $Body['coordinate'] @('number_density','number_decimal','number_size','number_color','number_opacity','number_stroke_width','number_stroke_color') 'screenshot.coordinate'
        }
        if ($Body.ContainsKey('marker')) {
            Validate-NestedKeys $EndpointName $Body['marker'] @('x','y','ring_radius','ring_line_width','ring_color','dot_radius','dot_color') 'screenshot.marker'
        }
    }
    if ($EndpointName -eq 'batch' -and $Body.ContainsKey('instructions')) {
        $idx = 0
        foreach ($instruction in $Body['instructions']) {
            $action = $instruction['action']
            if ($action -notin (Valid-Endpoints) -or $action -in @('health','batch')) {
                throw "unknown batch action '$action'. Next: read skill.md and references/api/batch.md."
            }
            $params = if ($instruction.ContainsKey('params')) { $instruction['params'] } else { @{} }
            $stepAllowed = (Endpoint-AllowedKeys $action) | Where-Object { $_ -notin @('ai_app_type','session_id','window_id','main_window_id') }
            foreach ($key in $params.Keys) {
                if ($key -notin $stepAllowed) {
                    throw "unknown parameter 'step.$idx.params.$key' for endpoint '$action'. Next: read skill.md and $(Endpoint-Doc $action)."
                }
            }
            if ($action -eq 'screenshot') {
                if ($params.ContainsKey('grid')) { Validate-NestedKeys $action $params['grid'] @('density_x','density_y','opacity','color') "step.$idx.params.grid" }
                if ($params.ContainsKey('coordinate')) {
                    Validate-NestedKeys $action $params['coordinate'] @('number_density','number_decimal','number_size','number_color','number_opacity','number_stroke_width','number_stroke_color') "step.$idx.params.coordinate"
                }
                if ($params.ContainsKey('marker')) {
                    Validate-NestedKeys $action $params['marker'] @('x','y','ring_radius','ring_line_width','ring_color','dot_radius','dot_color') "step.$idx.params.marker"
                }
            }
            $idx += 1
        }
    }
}

function Sanitize-OutputData($Value) {
    if ($null -eq $Value) { return $null }
    if ($Value -is [System.Collections.IDictionary]) {
        $clean = @{}
        foreach ($key in $Value.Keys) {
            if ($key -notin @('image_base64','source_image_base64')) {
                $sanitized = Sanitize-OutputData $Value[$key]
                if ($null -ne $sanitized -and -not (Is-EmptyCollection $sanitized)) {
                    $clean[$key] = $sanitized
                }
            }
        }
        return $clean
    }
    if ($Value -is [System.Collections.IEnumerable] -and $Value -isnot [string]) {
        $items = @()
        foreach ($item in $Value) {
            $sanitized = Sanitize-OutputData $item
            if ($null -ne $sanitized -and -not (Is-EmptyCollection $sanitized)) {
                $items += ,$sanitized
            }
        }
        return $items
    }
    if ($Value.PSObject -and $Value.PSObject.Properties.Count -gt 0 -and $Value -isnot [string]) {
        $clean = [ordered]@{}
        foreach ($prop in $Value.PSObject.Properties) {
            if ($prop.Name -notin @('image_base64','source_image_base64')) {
                $sanitized = Sanitize-OutputData $prop.Value
                if ($null -ne $sanitized -and -not (Is-EmptyCollection $sanitized)) {
                    $clean[$prop.Name] = $sanitized
                }
            }
        }
        return $clean
    }
    return $Value
}

function Is-EmptyCollection($Value) {
    if ($null -eq $Value) { return $true }
    if ($Value -is [System.Collections.IDictionary]) { return $Value.Count -eq 0 }
    if ($Value -is [System.Collections.IEnumerable] -and $Value -isnot [string]) {
        return @($Value).Count -eq 0
    }
    if ($Value.PSObject -and $Value.PSObject.Properties.Count -gt 0 -and $Value -isnot [string]) {
        return $Value.PSObject.Properties.Count -eq 0
    }
    return $false
}

try {
    Validate-Endpoint $Endpoint
    $body = Parse-Args $RemainingArgs
    if (-not $body.ContainsKey('api_url')) { throw "api_url is required" }
    if (-not $body.ContainsKey('token')) { throw "token is required" }
    $apiUrl = $body['api_url'].TrimEnd('/')
    $token = $body['token']
    $body.Remove('api_url')
    $body.Remove('token')

    if ($Endpoint -ne 'health') {
        foreach ($required in @('ai_app_type','session_id')) {
            if (-not $body.ContainsKey($required)) { throw "$required is required" }
        }
    }
    $windowExempt = @('health','get_window_list','delegated','crop_zoom_screenshot')
    if ($Endpoint -notin $windowExempt -and -not $body.ContainsKey('window_id')) { throw "window_id is required" }
    if ($Endpoint -notin $windowExempt -and $Endpoint -ne 'wait' -and -not $body.ContainsKey('main_window_id')) { throw "main_window_id is required" }
    if ($Endpoint -eq 'batch') { $body = Convert-BatchSteps $body }
    Validate-Params $Endpoint $body
    Prepare-RemoteCropInput $Endpoint $apiUrl $body

    $headers = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }
    $url = "$apiUrl/api/$Endpoint"
    if ($Endpoint -eq 'health') {
        $response = Invoke-RestMethod -Uri $url -Method Get -Headers $headers
    } else {
        $jsonBody = $body | ConvertTo-Json -Depth 20 -Compress
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($jsonBody)
        $response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $bytes -TimeoutSec 240
    }

    if (-not $response.success) {
        $code = if ($response.error_code) { $response.error_code } else { "UNKNOWN" }
        Write-Error "API Error [$code]: $($response.message)"
        exit 1
    }

    if ($Endpoint -in @('screenshot','scroll_screenshot','crop_zoom_screenshot')) {
        $path = Materialize-ImageData $Endpoint $response.data $body
        if ($path) { Write-Output $path }
        if ($response.message) { Write-Output $response.message }
        if ($response.data) {
            Write-Output "Data:"
            Write-Output ((Sanitize-OutputData $response.data) | ConvertTo-Json -Depth 20)
        }
    } elseif ($Endpoint -eq 'batch') {
        $index = 0
        foreach ($item in $response.data.results) {
            if ($item.data -and ($item.data.image_path -or $item.data.image_base64)) {
                $action = if ($index -lt $body['instructions'].Count) { $body['instructions'][$index]['action'] } else { 'screenshot' }
                $path = Materialize-ImageData $action $item.data $body
                if ($path) { Write-Output $path }
            }
            $index += 1
        }
        Write-Output ((Sanitize-OutputData $response) | ConvertTo-Json -Depth 20)
    } else {
        Write-Output ((Sanitize-OutputData $response) | ConvertTo-Json -Depth 20)
    }
} catch {
    $message = $_.Exception.Message
    if ($message -match 'api_url is required|token is required|invalid argument|expected key=value|window_id is required|main_window_id is required|each batch step requires action|source_image_path not found|unknown endpoint|unknown parameter|invalid parameter|unknown batch action') {
        Write-Error "Script Error: $message"
    } else {
        Write-Error "Script Error: API call failed. Check api_url, token, endpoint, and network. Next: read skill.md, then verify the endpoint API document."
    }
    exit 1
}
