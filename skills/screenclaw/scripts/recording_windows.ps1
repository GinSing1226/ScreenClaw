param(
    [Parameter(Position=0, ValueFromRemainingArguments=$true)][string[]]$RemainingArgs
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "recording_windows.py"

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
}

if (-not $python) {
    Write-Error "Script Error: python is required for recording_windows.ps1"
    exit 1
}

& $python.Source $pythonScript @RemainingArgs
exit $LASTEXITCODE
